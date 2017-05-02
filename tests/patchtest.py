# Licensed under GPLv3 (https://www.gnu.org/licenses/gpl.html)

# Test patching system

import sys
import os
sys.path.append(os.path.relpath("../synth"))
import patcher
import time

patches = patcher.Patcher()

while True:
    patches.update()
    sigConns = patches.getModuleQueue()
    auxConns = patches.getAuxConnections()
    print("==========================")
    print("Signal Conns: " + str(sigConns))
    print("Auxiliary conns: " + str(auxConns))
    time.sleep(0.3)
