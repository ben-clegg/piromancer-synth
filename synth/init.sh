# Licensed under GPLv3 (https://www.gnu.org/licenses/gpl.html)
killall -9 jackd & sleep 1
jackd -r -p 8 -t 2000 -d alsa --device hw:CARD=0,DEV=0 -S -P -o 2 -n 3 -p 1024 -r 44100 -X seq &
sleep 1
python pyohost.py
