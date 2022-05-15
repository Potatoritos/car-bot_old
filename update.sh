#!/bin/bash
source venv/bin/activate

git pull

./build_carpp.sh

./put_slash.sh

deactivate
