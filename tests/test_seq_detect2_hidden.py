"""
Cocotb testbench for seq_detect2 (seq_detect2.v).
Detects overlapping sequence "110110" — dout=1 on the cycle the final '0' is received.
Example: input "110110110" -> output "000001001".
"""

from __future__ import annotations

import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb_tools.runner import get_runner


async def reset_dut(dut, cycles=2):
    """Assert reset for a few cycles, then release."""
    dut.rst.value = 1
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


async def drive_sequence(dut, bit_str: str):
    """Drive din with bits from bit_str, one bit per clock cycle."""
    for b in bit_str:
        dut.din.value = int(b, 2)
        await RisingEdge(dut.clk)


async def drive_and_check(dut, input_seq: str, expected_out: str):
    """Drive input sequence and check dout each cycle."""
    # Drive din, wait for posedge; dout is registered so read after edge settles.
    actual = []
    for b in input_seq:
        dut.din.value = int(b, 2)
        await RisingEdge(dut.clk)
        await Timer(1, "ns")  # Read after non-blocking updates apply
        actual.append(str(int(dut.dout.value)))
    got = "".join(actual)
    assert got == expected_out, f"input={input_seq} expected out={expected_out} got={got}"


@cocotb.test()
async def test_sequence_110110_single(dut):
    """Single occurrence: input 110110 -> output 000001."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "110110", "000001")


@cocotb.test()
async def test_sequence_then_no_match(dut):
    """One detect then noise: 11011000 -> 00000100."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "11011000", "00000100")



@cocotb.test()
async def test_sequence_two_non_overlapping(dut):
    """Two non-overlapping: 1101100110110 -> 0000010000001."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await drive_and_check(dut, "1101100110110", "0000010000001")

@cocotb.test()
async def test_reset_clears_state(dut):
    """After reset, next 110110 still gives 000001."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    # Partial sequence then reset
    await drive_sequence(dut, "110")
    await reset_dut(dut)
    await drive_and_check(dut, "110110", "000001")


###################

@cocotb.test()
async def test_full_overlap_chain(dut):
    """
    Continuous overlapping matches.
    110110110110 -> detections at 6,9,12
    input : 110110110110
    output: 000001001001
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "110110110110", "000001001001")


@cocotb.test()
async def test_overlap_with_extra_prefix(dut):
    """
    Overlap where prefix immediately starts next match.
    input : 1110110110
    output: 0000001001
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "1110110110", "0000001001")


@cocotb.test()
async def test_partial_prefix_restart(dut):
    """
    Partial prefix then restart.
    input : 1101110110110
    output: 0000000001001
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "1101110110110", "0000000001001")



@cocotb.test()
async def test_dense_prefix_noise(dut):
    """
    Many prefix fragments that should not trigger false detect.
    input : 111111011011
    output: 000000000000
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "111111011011", "000000000100")


@cocotb.test()
async def test_long_noise_then_match(dut):
    """
    Long random prefix before valid match.
    input : 1010101010110110
    output: 0000000000000001
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "1010101010110110", "0000000000000001")



@cocotb.test()
async def test_all_zeros(dut):
    """
    Edge case: no ones at all.
    input : 000000000000
    output: 000000000000
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "000000000000", "000000000000")


@cocotb.test()
async def test_all_ones(dut):
    """
    Edge case: continuous ones.
    Should never detect.
    input : 111111111111
    output: 000000000000
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "111111111111", "000000000000")


@cocotb.test()
async def test_back_to_back_matches(dut):
    """
    Back-to-back matches with minimal separation.
    input : 1101100110110
    output: 0000010000001
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await drive_and_check(dut, "1101100110110", "0000010000001")



@cocotb.test()
async def test_reset_mid_pattern(dut):
    """
    Reset exactly during a partial pattern.
    FSM must forget previous state.
    """
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    await drive_sequence(dut, "11011")  # almost complete
    await reset_dut(dut)

    await drive_and_check(dut, "110110", "000001")








def test_seq_detect2_hidden_runner():
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sources = [proj_path / "golden/seq_detect2.v"]
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="seq_detect2",
        always=True,
    )
    runner.test(hdl_toplevel="seq_detect2", test_module="test_seq_detect2_hidden")



