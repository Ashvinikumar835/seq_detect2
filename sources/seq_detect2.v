`timescale 1ns / 1ps
//detect 110110

module seq_detect2(
    input clk,
    input rst,
    input din,
    output reg dout
);

reg [2:0] state;

parameter S0 = 3'd0,
          S1 = 3'd1,
          S2 = 3'd2,
          S3 = 3'd3,
          S4 = 3'd4,
          S5 = 3'd5,
          S6 = 3'd6;

always @(posedge clk or posedge rst)
begin
    if (rst) begin
        state <= S0;
        dout <= 0;
    end
    else begin

        if (state == S0) begin
            if (din == 1)
            begin
                state <= S1;
                dout <= 0;
                end
            else
            begin
                state <= S0;
                dout <= 0;
                end
        end


else if (state == S1) begin
            if (din == 1)
            begin
                state <= S2;
                dout <= 0;
                end
            else
            begin
                state <= S0;
                dout <= 0;
                end
        end


else if (state == S2) begin
            if (din == 1)
            begin
                state <= S2;
                dout <= 0;
                end
            else
            begin
                state <= S3;
                dout <= 0;
                end
        end


else if (state == S3) begin
            if (din == 1)
            begin
                state <= S4;
                dout <= 0;
                end
            else
            begin
                state <= S0;
                dout <= 0;
                end
        end


else if (state == S4) begin
            if (din == 1)
            begin
                state <= S5;
                dout <= 0;
                end
            else
            begin
                state <= S0;
                dout <= 0;
                end
        end

else if (state == S5) begin
            if (din == 1)
            begin
                state <= S2;
                dout <= 0;
                end
            else
            begin
                state <= S3;
                dout <= 1;
                end
        end

   end
end


endmodule
