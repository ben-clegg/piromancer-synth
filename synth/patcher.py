# Licensed under GPLv3 (https://www.gnu.org/licenses/gpl.html)

import time
from collections import deque

import RPi.GPIO as GPIO
import os

PIN_REFRESH = 0.01 # Pin refresh delay, in seconds

# Pins
P_OSC_SIG_OUT = 3

P_FLT_SIG_IN = 8
P_FLT_SIG_OUT = 10

P_AMP_SIG_IN = 12

P_LFO_SIG_OUT = 7
P_ENV_SIG_OUT = 5

P_OSC_FMOD_IN = 23
P_FLT_CUTOFF_IN = 21
P_AMP_MOD_IN = 19
P_AMP_ENV_IN = 15

# Outputs
P_OUTPUTS = (P_OSC_SIG_OUT,
            P_FLT_SIG_OUT,
            P_LFO_SIG_OUT,
            P_ENV_SIG_OUT)
# Inputs
P_INPUTS = (P_FLT_SIG_IN,
            P_AMP_SIG_IN,
            P_OSC_FMOD_IN,
            P_FLT_CUTOFF_IN,
            P_AMP_MOD_IN,
            P_AMP_ENV_IN)

# Module ids
MOD_OSC = 1
MOD_FILTER = 2
MOD_AMPLIFIER = 3
MOD_LFO = 4
MOD_ENVELOPE = 5

# Auxiliary connection ids
CONN_LFO_OSC_SWEEP = 1
CONN_ENV_OSC_SWEEP = 2
CONN_LFO_FLT_CUTOFF = 3
CONN_ENV_FLT_CUTOFF = 4
CONN_LFO_AMP_MOD = 5
CONN_ENV_AMP_ENV = 6

class Patcher:

    def __init__(self):
        # Use board pin numbering - compatible with different RPi revisions
        GPIO.setmode(GPIO.BOARD)

        # Setup outputs
        for o in P_OUTPUTS:
            GPIO.setup(o, GPIO.OUT)

        #Setup inputs
        for i in P_INPUTS:
            GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Force outputs to low
        GPIO.output(P_OUTPUTS, GPIO.LOW)

        # Get starting signal path
        self.moduleQueue = self.findSignalPath()
        self.auxConns = self.findLfoAndEnvConns()

    def update(self):
        self.moduleQueue = self.findSignalPath()
        self.auxConns = self.findLfoAndEnvConns()

    def getModuleQueue(self):
        print("getting module queue (signal path)")
        return deque(self.moduleQueue)

    def getAuxConnections(self):
        return self.auxConns

    #Check standard signal path, returns queue of signal path, pop to find signal order
    def findSignalPath(self):
        queue = [MOD_OSC] #Signal will always start with oscillator
        GPIO.output(P_OUTPUTS, GPIO.LOW) #Set all outputs to 0/off/False
        GPIO.output(P_OSC_SIG_OUT, GPIO.HIGH) #Set initial output (oscillator) to 1/on/True
        print("locked osc")
        return self.getNextSignalModule(queue)

    #Recursive function used in findSignalPath, adds module IDs to queue
    def getNextSignalModule(self, queue):
        time.sleep(PIN_REFRESH)
        #Filter
        if(GPIO.input(P_FLT_SIG_IN)):
            queue.append(MOD_FILTER)
            GPIO.output(P_OUTPUTS, GPIO.LOW)
            GPIO.output(P_FLT_SIG_OUT, GPIO.HIGH)
            print("locked filter")
            return self.getNextSignalModule(queue) #Recurse
        #More modules can be implemented here, in the same way as filter, using an elif
        #Amplifier
        elif(GPIO.input(P_AMP_SIG_IN)):
            queue.append(MOD_AMPLIFIER)
            GPIO.output(P_OUTPUTS, GPIO.LOW)
            print("locked amp, returning")
            return queue #Don't recurse, amplifier is the last possible module in this synth
        else:
            print("amp not reached")
            return [] #Clear the queue, amplifier not reached - no audio made

    def findLfoAndEnvConns(self):
        connList = [] #Empty list of connections
        #Test LFO
        GPIO.output(P_OUTPUTS, GPIO.LOW) #Set all outputs to 0/off/False
        GPIO.output(P_LFO_SIG_OUT, GPIO.HIGH) #Set LFO output on
        time.sleep(PIN_REFRESH)
        if(GPIO.input(P_OSC_FMOD_IN)):
            connList.append(CONN_LFO_OSC_SWEEP)
        if(GPIO.input(P_FLT_CUTOFF_IN)):
            connList.append(CONN_LFO_FLT_CUTOFF)
        if(GPIO.input(P_AMP_MOD_IN)):
            connList.append(CONN_LFO_AMP_MOD)
        #Test Envelope
        GPIO.output(P_OUTPUTS, GPIO.LOW) #Set all outputs to 0/off/False
        GPIO.output(P_ENV_SIG_OUT, GPIO.HIGH) #Set LFO output on
        time.sleep(PIN_REFRESH)
        if(GPIO.input(P_FLT_CUTOFF_IN)):
            connList.append(CONN_ENV_FLT_CUTOFF)
        if(GPIO.input(P_AMP_ENV_IN)):
            connList.append(CONN_ENV_AMP_ENV)
        if(GPIO.input(P_OSC_FMOD_IN)):
            connList.append(CONN_ENV_OSC_SWEEP)
        #Return list of connection ids
        return connList
