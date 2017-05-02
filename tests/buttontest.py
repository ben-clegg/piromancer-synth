# Licensed under GPLv3 (https://www.gnu.org/licenses/gpl.html)

# Test momentary PTM button 

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

P_BTN_OSC_WAVEFORM = 11
P_BTN_FILT_TYPE = 13

GPIO.setup(P_BTN_OSC_WAVEFORM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(P_BTN_FILT_TYPE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
    pressedOsc = False
    pressedOsc = not GPIO.input(P_BTN_OSC_WAVEFORM)
    pressedFilt = False
    pressedFilt = not GPIO.input(P_BTN_FILT_TYPE)
    # Note raw input is inversed - False = button pressed
    # therefore inverted with not statement
    if pressedOsc:
        print('Osc Waveform!')
    if pressedFilt:
        print('Filter Type!')
    if ((not pressedOsc) and (not pressedFilt)):
        print('Nothing Pressed!')
