# Licensed under GPLv3 (https://www.gnu.org/licenses/gpl.html)

import time
import threading
import RPi.GPIO as GPIO

# Button input pins
P_BTN_OSC_WAVEFORM = 11
P_BTN_FILT_TYPE = 13
# PTM momentary switches should be connected to these pins and GND

# Wave IDs
WAVE_SUPERSAW = 1 # Roland JP-8000 emulation
WAVE_SINE = 2
WAVE_TRI = 3
WAVE_SQUARE = 4
WAVE_PINK = 5

# Filter type IDS
FILTER_MOOG_LP = 1 # Moog Resonant Lowpass Emulator
FILTER_BP_RESON = 2 # 2nd order "classic resonant bandpass filter"
# The following are "Butterworth" filters, with "high stopband attenuation"
FILTER_LP = 3 # Lowpass
FILTER_HP = 4 # Highpass
FILTER_BP = 5 # Bandpass - const bandwidth
FILTER_BR = 6 # Band reject (bandstop) - const bandwidth
FILTER_NOTCH = 7 # Same as BR, but narrow const bandwidth

WAIT = 0.6 # How long to wait if button press detected, to cycle types if button held
class Buttons:
    def __init__(self):
        # Use board pin numbering - compatible with different RPi revisions
        GPIO.setmode(GPIO.BOARD)
        # Initialise GPIO inputs in pull-up resistor mode
        GPIO.setup(P_BTN_OSC_WAVEFORM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(P_BTN_FILT_TYPE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Define initial osc wave and filter type controls
        self.waveID = 1
        self.filtID = 1
        self.pressedOscWave = False
        self.pressedFiltType = False

    def update(self):
        # Update oscillator waveform button
        self.pressedOscWave = not GPIO.input(P_BTN_OSC_WAVEFORM)
        # Input is inverted by "not", normally False when pressed
        if self.pressedOscWave:
            self.waveID += 1
            if self.waveID > WAVE_PINK: # Last wave type
                self.waveID = 1
            time.sleep(WAIT)


        # Update filter type button
        self.pressedFiltType = not GPIO.input(P_BTN_FILT_TYPE)
        if self.pressedFiltType:
            self.filtID += 1
            if self.filtID > FILTER_NOTCH: # Last filt type
                self.filtID = 1
            time.sleep(WAIT)

    def getWaveFilterTypes(self):
        # Return a tuple of the the osc wave id, and filter type id
        # These values are modified by button presses, checked by threads.
        # The threads are started on class initialisation
        return (self.waveID, self.filtID)
