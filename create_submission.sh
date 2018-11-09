#!/bin/sh

cp nightMiner.py MyBot.py
/usr/bin/zip -9 -r /tmp/nightMiner MyBot.py hlt/*.py custom_routines/*.py
rm MyBot.py

