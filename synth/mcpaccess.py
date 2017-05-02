#!/usr/bin/env python

# MCP3008 driver program
#   modified example written by Limor "Ladyada" Fried for Adafruit Industries,
#   (c) 2015, released into the public domain
#   https://gist.github.com/ladyada/3151375
# This modified program is also released into the public domain,
#   in the same manner.

import time
#import os
import RPi.GPIO as GPIO

# Use board pin numbering - compatible with different RPi revisions
GPIO.setmode(GPIO.BOARD)

#Define pins
P_MCP3008_DOUT = 24
P_MCP3008_CLK = 26
P_MCP3008_DIN = 22
P_MCP3008_CS = 18

DEBUG = 1
TOLERANCE = 10 # Change must be greater than this value

class MCPAccess:
    def __init__(self):
        # set up the SPI interface pins
        GPIO.setup(P_MCP3008_DIN, GPIO.OUT)
        GPIO.setup(P_MCP3008_DOUT, GPIO.IN)
        GPIO.setup(P_MCP3008_CLK, GPIO.OUT)
        GPIO.setup(P_MCP3008_CS, GPIO.OUT)
        # "last read" value of each input (8 inputs)
        self.last_reads = [0, 0, 0, 0, 0, 0, 0, 0]

    # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    def readadc(self, adcnum, reversed=False):
            if ((adcnum > 7) or (adcnum < 0)):
                    return -1
            GPIO.output(P_MCP3008_CS, True)

            GPIO.output(P_MCP3008_CLK, False)  # start clock low
            GPIO.output(P_MCP3008_CS, False)     # bring CS low

            commandout = adcnum
            commandout |= 0x18  # start bit + single-ended bit
            commandout <<= 3    # we only need to send 5 bits here
            for i in range(5):
                    if (commandout & 0x80):
                            GPIO.output(P_MCP3008_DIN, True)
                    else:
                            GPIO.output(P_MCP3008_DIN, False)
                    commandout <<= 1
                    GPIO.output(P_MCP3008_CLK, True)
                    GPIO.output(P_MCP3008_CLK, False)

            adcout = 0
            # read in one empty bit, one null bit and 10 ADC bits
            for i in range(12):
                    GPIO.output(P_MCP3008_CLK, True)
                    GPIO.output(P_MCP3008_CLK, False)
                    adcout <<= 1
                    if (GPIO.input(P_MCP3008_DOUT)):
                            adcout |= 0x1

            GPIO.output(P_MCP3008_CS, True)

            adcout >>= 1       # first bit is 'null' so drop it

            if reversed:
                # Reverse the value, for inverted potentiometer polarity
                adcout = 1024 - adcout

            # Check if big enough difference since last reading
            # to prevent fluctuations
            if (abs(adcout - self.last_reads[adcnum]) > TOLERANCE):
                # Replace if there is
                self.last_reads[adcnum] = adcout

            return float(self.last_reads[adcnum])
