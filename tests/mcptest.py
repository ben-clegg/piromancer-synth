# Licensed under GPLv3 (https://www.gnu.org/licenses/gpl.html)

# Test MCP3008 ADC inputs

import sys
import os
sys.path.append(os.path.relpath("../synth"))
import mcpaccess
import time

mcp = mcpaccess.MCPAccess()

while True:
    print("==========================")
    print("ADC 0: " + str(mcp.readadc(0)))
    print("ADC 1: " + str(mcp.readadc(1)))
    print("ADC 2: " + str(mcp.readadc(2)))
    print("ADC 3: " + str(mcp.readadc(3)))
    print("ADC 4: " + str(mcp.readadc(4)))
    print("ADC 5: " + str(mcp.readadc(5)))
    print("ADC 6: " + str(mcp.readadc(6)))
    print("ADC 7: " + str(mcp.readadc(7)))
    print("==========================")
    print("REVERSED: ")
    print("ADC 0: " + str(mcp.readadc(0, reversed=True)))
    print("ADC 1: " + str(mcp.readadc(1, reversed=True)))
    print("ADC 2: " + str(mcp.readadc(2, reversed=True)))
    print("ADC 3: " + str(mcp.readadc(3, reversed=True)))
    print("ADC 4: " + str(mcp.readadc(4, reversed=True)))
    print("ADC 5: " + str(mcp.readadc(5, reversed=True)))
    print("ADC 6: " + str(mcp.readadc(6, reversed=True)))
    print("ADC 7: " + str(mcp.readadc(7, reversed=True)))

    time.sleep(0.2)
