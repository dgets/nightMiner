#!/bin/sh

#create the .zip for submission
cp nightMiner.py MyBot.py
/usr/bin/zip -9 -r /tmp/nightMiner MyBot.py hlt/*.py custom_routines/*.py
rm MyBot.py

#archive the bot for battling against the next version upgrade
cd ../../src/py/haliteIII
rm -Rf previous_incarnation
mkdir previous_incarnation
cd previous_incarnation
/usr/bin/unzip /tmp/nightMiner

echo nightMiner.zip is in /tmp
echo version is archived in ~/src/py/haliteIII/previous_incarnation for
echo battles against upcoming revisions

