# Licensed under GPLv3 (https://www.gnu.org/licenses/gpl.html)

from pyo import *
from collections import deque
import os
import time
import copy

import mcpaccess
import patcher
import buttons

# Setup MCP ADC, Patching System, and Button checking
mcp = mcpaccess.MCPAccess()
patches = patcher.Patcher()
btns = buttons.Buttons()

# Setup pyo server
s = Server(audio='jack', sr=44100, nchnls=1, duplex=0, jackname='pyo')

# Print MIDI input devices
midiInputs = pm_get_input_devices()
print(midiInputs)

# Server config
s.setIchnls(0) # Disable audio in, unneeded
s.setMidiInputDevice(3) #Set midi device
s.boot() #Boot server

# Copy output to otherwise unused channel, as only using mono,
# but both speakers should output.
os.system("jack_connect pyo:output_1 system:playback_2")

s.start()

# MIDI input
midi = Notein(poly=1, scale=1) # scale=1 : pitch in Hz
                                # poly=1 : 1 stream - monophonic

frq = 480 # Initialise frequency
frq = midi['pitch'] #Note pitch (frequency in Hz)

# Analog inputs:
# ADC0 = [UNUSED] (Gain)
# ADC1 = [UNUSED] (Filter Cutoff)
# ADC2 = Env. Release (inverted)
# ADC3 = Env. Sustain (inverted)
# ADC4 = LFO Amplitude
# ADC5 = LFO Frequency
# ADC6 = Env. Decay (inverted)
# ADC7 = Env. Attack (inverted)

# Initialise potentiometer-controlled inputs
envValues = [0.5, 0.5, 0.5, 0.5] # Attack, Decay, Sustain, Release
env = MidiAdsr(midi['velocity'], attack=0.1, decay=0.1, sustain=0.1, release=0.1)
lfoValues = [0.4, 0.4] # Frequency, Amplitude
filt_frq = 500

def update_env():
    # Updates the globally defined envelope with appropriate MCP3008 readings
    global env
    env = MidiAdsr(midi['velocity'], attack=envValues[0], decay=envValues[1], sustain=envValues[2], release=envValues[3])

update_env()

# patch variables
sigConns = patches.getModuleQueue()
auxConns = patches.getAuxConnections()
btnVals = btns.getWaveFilterTypes() # tuple (wavetype, filttype)
# btnVals[0] = osc waveform id ; btnVals[1] = filter type

# Function definitions
def m_lfo(target=400, ampMult=1, freqMult=1):
    # Simple sine LFO.
    # Centered around target frequency
    # Other parameters multiply the MCP LFO inputs (which are 0 - 1)
    # ampMult multiplies the amplitude (amount)
    # freqMult multiplies the frequency of the LFO sine wave

    return Sine(freq=(0.1 + (freqMult * lfoValues[0])), mul=ampMult * lfoValues[1], add=target)

def m_oscillator(vel):
    # Generate source
    # http://ajaxsoundstudio.com/pyodoc/api/classes/generators.html
    local_frq = frq # set local variable to modify frequency

    # Modulate frequency with LFO
    if(patcher.CONN_LFO_OSC_SWEEP in auxConns):
        local_frq = m_lfo(frq, 100, 10)

    # Modulate frequency with Envelope
    if(patcher.CONN_ENV_OSC_SWEEP in auxConns):
        # Note: divide env by sustain (the amplitude of the sustain period)
        #       this means sustain period is always the input frequency,
        #       preventing detuning
        local_frq = local_frq * (env / env.sustain)

    # Select waveform
    if(btnVals[0] == buttons.WAVE_SUPERSAW):
        osc = SuperSaw(freq=local_frq, mul=vel) # SuperSaw wave
    elif(btnVals[0] == buttons.WAVE_SINE):
        osc = Sine(freq=local_frq, mul=vel) # Sine wave
    elif(btnVals[0] == buttons.WAVE_TRI):
        # Resistor / capacitor emulation, triangle form
        osc = RCOsc(freq=local_frq, sharp=0, mul=vel)
    elif(btnVals[0] == buttons.WAVE_SQUARE):
        # Resistor / capacitor emulation, almost square form
        osc = RCOsc(freq=local_frq, sharp=1, mul=vel)
    elif(btnVals[0] == buttons.WAVE_PINK):
        osc = PinkNoise(mul=vel) # Pink noise - freq. independent
    else:
        # Sine wave by default (prevent potential crashes)
        osc = Sine(freq=local_frq, mul=vel)
    return osc

def m_filter(input_signal, modFreq=False):
    # Apply filter
    # http://ajaxsoundstudio.com/pyodoc/api/classes/filters.html

    local_frq = frq  # Scale to input frequency
    # Note: MCP input can be used as frequency instead
    # if the cutoff potentiometer is functional

    # Modulate cutoff frequency with LFO
    if(patcher.CONN_LFO_FLT_CUTOFF in auxConns):
        local_frq = m_lfo(frq, 500, 10)

    # Modulate cutoff frequency with Envelope
    if(patcher.CONN_ENV_FLT_CUTOFF in auxConns):
        local_frq = local_frq * env

    if(btnVals[1] == buttons.FILTER_MOOG_LP):
        # Moog Resonant Lowpass
        local_frq += 50 # increase cutoff slightly, reduces filter by LP
        return MoogLP(input_signal, freq=(local_frq), res=1).out()
    elif(btnVals[1] == buttons.FILTER_BP_RESON):
        # Resonant bandpass
        return Reson(input_signal, freq=(local_frq), q=4).out()
    elif(btnVals[1] == buttons.FILTER_LP):
        # Lowpass
        return ButLP(input_signal, freq=(local_frq)).out()
    elif(btnVals[1] == buttons.FILTER_HP):
        # Highpass
        return ButHP(input_signal, freq=(local_frq)).out()
    elif(btnVals[1] == buttons.FILTER_BP):
        # Bandpass
        return ButBP(input_signal, freq=(local_frq), q = 4).out()
    elif(btnVals[1] == buttons.FILTER_BR):
        # Band reject (bandstop)
        return ButBR(input_signal, freq=(local_frq), q = 4).out()
    elif(btnVals[1] == buttons.FILTER_NOTCH):
        # Notch filter, implemented as above, but with narrow bandwidth
        return ButBR(input_signal, freq=(local_frq), q = 380).out()
    else:
        # Use Moog Resonant Lowpass by default (prevents potential crashes)
        return MoogLP(input_signal, freq=(local_frq), res=1).out()
    # Note: for band-filters, q = freq / bandwidth, so low q = high width

def m_amp(input_signal):
    # VCA simulation
    local_gain = 0.6
    if(patcher.CONN_LFO_AMP_MOD in auxConns):
        local_gain = m_lfo(0.6, 0.5, 10)
    if(patcher.CONN_ENV_AMP_ENV in auxConns):
        local_gain = local_gain * env
    if(btnVals[0] == buttons.WAVE_SQUARE):
        # Reduce volume of square wave
        local_gain = local_gain * 0.8

    local_signal = input_signal
    local_signal.setMul(local_gain)
    return local_signal


def createSignal():
    if(sigConns):
        # Connections queue not empty
        localSigConns = copy.deepcopy(sigConns)
        item = localSigConns.popleft()
        if(item == patcher.MOD_OSC):
            wav = m_oscillator(1)
            print('Found oscillator')
            return processStep(wav, localSigConns)
    print('No sig connections, returning None')
    return None

def processStep(signal, localSigConns):
    if(sigConns):
        # Connections queue not empty
        localSig = signal
        item = localSigConns.popleft()
        if(item == patcher.MOD_FILTER):
            filtered = m_filter(localSig)
            print('Found filter')
            return processStep(filtered, localSigConns)
        elif(item == patcher.MOD_AMPLIFIER):
            print('Found amplifier, returning signal output')
            #m_amp()
            #localSig.setMul(env)
            #localSig.setMul(0.6)
            return m_amp(localSig).out()
    print('No sig connections to process, returning None')
    return None

def logger():
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
    print("Button Values: " + str(btnVals))
    print("Signal Conns: " + str(sigConns))
    print("Auxiliary conns: " + str(auxConns))
    print("==========================")

def ctl_scan(ctlnum):
    print(ctlnum)



# Generate audio, applying signal processing where necessary
audio = createSignal()

# Loop to maintain server activity
while True:
    # Update envelope values
    prevEnvValues = envValues
    envValues = [mcp.readadc(7, reversed=True) / 1024,
                    mcp.readadc(6, reversed=True) / 1024,
                        mcp.readadc(3, reversed=True) / 1024,
                            mcp.readadc(2, reversed=True) / 1024]
    # Update LFO values
    prevLfoValues = lfoValues
    lfoValues = [mcp.readadc(5) / 1024, mcp.readadc(4) / 1024]
    # Update patchbay connections
    prevSigConns = sigConns
    prevAuxConns = auxConns
    patches.update()
    sigConns = patches.getModuleQueue()
    auxConns = patches.getAuxConnections()
    # Update buttons
    prevBtnVals = btnVals
    btns.update()
    btnVals = btns.getWaveFilterTypes()
    # If any connections have changed, buttons pressed,
    # or MCP readings changed, update the audio signal
    if(
            (list(prevSigConns) != list(sigConns)) or
            (list(prevAuxConns) != list(auxConns)) or
            (list(prevEnvValues) != list(envValues)) or
            (list(prevLfoValues) != list(lfoValues)) or
            (prevBtnVals != btnVals)
        ):
            # Update envelope
            update_env()
            # Regenerate audio
            audio = createSignal()
    #logger() # Uncomment to print debugging logs

    # Scan ctl
    midictl = CtlScan(ctl_scan)
    print(midictl)
