#!/bin/bash

. venv/bin/activate

pythondir=$(ls -1 venv/lib)

export LD_LIBRARY_PATH=$(pwd)/venv/lib/$pythondir/site-packages/PyQt5/Qt5/lib

echo $LD_LIBRARY_PATH

pyinstaller --clean --log-level WARN -F -n esp32-mpy-jama --add-binary src/content:content src/app.py

