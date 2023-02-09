#!/bin/bash

. venv/bin/activate

export LD_LIBRARY_PATH="$(pwd)/venv/lib/python3.10/site-packages/PyQt5/Qt5/lib"

pyinstaller --clean --log-level WARN -F -n esp32-mpy-jama --add-binary src/content:content src/app.py

