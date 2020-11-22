#/bin/bash

if [ "$EUID" -eq 0 ]
then
    echo "Please do not run this script with root"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ENV_DIR="${DIR}/.env"

# Install libatlas-base-dev for tflite
sudo apt-get install -y libatlas-base-dev=3.10.3-8+rpi1 freeglut3-dev=2.8.1-3

if [ ! -d "$ENV_DIR" ]; then
    # Setup virtualenv
    python3 -m pip install --upgrade pip
    python3 -m pip install --user virtualenv

    python3 -m virtualenv $ENV_DIR

    # Install relevant dependencies
    source $ENV_DIR/bin/activate

    python3 -m pip install -r requirements.txt
else
    source $ENV_DIR/bin/activate
fi