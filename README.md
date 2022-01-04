
# car-bot

my discord bot!

WIP

# Requirements

python 3.9

# Running

1. Set up virtual environment

run `python -m venv venv`

to activate venv, run `source venv/bin/activate` (windows: `venv\Scripts\activate.bat`)

2. Install dependencies

run `pip install -U -r requirements.txt`

3. Build stuff

run `build_carpp.sh`

(if this doesn't work (or if you are on windows), run `python build_carpp.py build`, open the `build` directory, find the .so or .dll file, then move this file into the `carbot` folder)

4. Set up config

copy `config_copy.py` in the `carbot` directory and rename the copied file to `config.py`. Then, edit the settings in `config.py`

5. Run

run `./run.sh`

(if this doesn't work, run `python carbot.py` in the `carbot` directory)

