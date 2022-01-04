#!/bin/bash

python build_carpp.py build

mv build/lib.*/carpp.*.so carbot
