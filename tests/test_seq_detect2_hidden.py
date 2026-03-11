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



def test_seq_detect2_hidden_runner():
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sources = [proj_path / "sources/seq_detect2.v"]
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="seq_detect2",
        always=True,
    )
    runner.test(hdl_toplevel="seq_detect2", test_module="test_seq_detect2_hidden")
