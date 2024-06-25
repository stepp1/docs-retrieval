#!/bin/bash

VENV_PATH=".venv"
INSTALL_IN_VENV=false

# Check if Poetry is installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry could not be found"
    # ask if we want to create a venv or if the user wants to install it by himself
    read -p "Do you want to install Poetry? [y/n]" -n 1 -r
    # if the user wants to install it by himself
    if [[ $REPLY =~ ^[Nn]$ ]]
    then
        echo "Please install Poetry and run this script again. See https://python-poetry.org/docs/ for more information."
        exit 1
    fi
    # if the user wants to create a venv, 
    # we will install poetry in the venv
    INSTALL_IN_VENV=true
fi

# check if proyecto-contratos-psinet is already cloned
if [ -d "proyecto-contratos-psinet" ]; then
    echo "proyecto-contratos-psinet is already cloned"
    cd proyecto-contratos-psinet;
    git pull origin master;
fi
# else: clone the repo
if [ ! -d "proyecto-contratos-psinet" ]; then
    echo "cloning proyecto-contratos-psinet"
    # use ssh to clone the repo because its private
    git clone git@github.com:KenMiyake/proyecto-contratos-psinet.git
    cd proyecto-contratos-psinet;
fi

# create venv if needed
if $INSTALL_IN_VENV; then
    echo "Creating venv in $VENV_PATH"
    python3 -m venv $VENV_PATH
    $VENV_PATH/bin/pip install -U pip setuptools
    # in case installation hangs, use PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring $VENV_PATH/bin/pip install poetry
fi

# install dependencies
echo "Installing dependencies"
poetry install