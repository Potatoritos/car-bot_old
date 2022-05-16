#!/bin/bash
source venv/bin/activate

git pull

./build_carpp.sh

python -m pip install -U -r requirements.txt

./put_slash.sh

deactivate
