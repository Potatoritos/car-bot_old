#!/bin/bash
source venv/bin/activate

cd carbot
python put_slash.py
cd ..

deactivate
