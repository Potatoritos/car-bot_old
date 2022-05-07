my discord bot! (wip)

# Requirements

* Python 3.10
* ffmpeg

# Running

1. Set up virtual environment

```bash
# Create venv
python -m venv venv

# Activate venv
source venv/bin/activate
```

2. Install dependencies

```bash
python -m pip install -U -r requirements.txt
```

3. Build stuff

```bash
chmod +x build_carpp.sh
./build_carpp.sh
```

(if this doesn't work, run `python build_carpp.py build`, open the `build` directory, find the .so or .dll file, then move this file into the `carbot` folder)

4. Set up config

```bash
cp carbot/config_copy.py carbot/config.py

# edit carbot/config.py
$EDITOR carbot/config.py
```

5. Run
```
chmod +x run.sh
./run.sh
```
