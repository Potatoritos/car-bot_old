#!/bin/bash
source venv/bin/activate

cd carbot
python del_all_slash.py
cd ..

deactivate
