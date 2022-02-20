#!/bin/bash
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
export WORKON_HOME=~/VirtualEnvs
export VIRTUALENVWRAPPER_VIRTUALENV=/home/imbl/.local/bin/virtualenv
source /usr/local/bin/virtualenvwrapper.sh
cd /home/imbl/Documents/Software/syncmrt;
workon syncmrt;
python main.py;
