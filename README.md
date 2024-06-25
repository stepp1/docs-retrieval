# Retrieval Augmented Generation for Legal Documents

> This project was a collaboration between the [PSINET](https://www.psinet.cl/). The goal was to explore the feasibility of extracting legal information in accurate and efficient ways. The project was developed by Victor Faraggi, Ken Miyake and Andres Olivares. This is a copy of the original repository without any reference to the actual customer.

 a system that can retrieve and generate legal documents using state-of-the-art techniques in Natural Language Processing (NLP).

## Installation

We have changed the installation process to use a more reproducible one: [Poetry](https://python-poetry.org/docs/).

### Local Development (*easy*)

We provide scripts to install the project. To use them download the corresponding file for your operating system:

* Linux, MacOS: Download `install.sh`, open a terminal, navigate to the file location and run it:

  ```bash
  ./install.sh
  ```

  Note: Remember to move the file first if you want to use a specific location.

### Local Development (*advanced*)

To install create a virtual environment and the necessary packages. First we must install Poetry, it is recommended to visit [Poetry](https://python-poetry.org/docs/) and read the instructions to make it easier for you. Then, open a terminal and follow the following instructions (run the instructions in a single session and do not close the terminal in between):

1. Download this repository, currently hosted on GitHub, and then navigate to the correct folder:

   ```bash
   git clone git@github.com:stepp1/docs-retrieval.git;
   cd project-contracts-psinet;
   ```
2. Create a virtual environment if necessary. If you installed `pipx` to install Poetry or already created a virtual environment, this step is not necessary.

   ```bash
   VENV_PATH="./.venv"
   python -m venv $VENV_PATH
   ```
3. If you have not yet installed Poetry, do so now:

   ```bash
   $VENV_PATH/bin/pip install -U pip setuptools
   $VENV_PATH/bin/pip install poetry
   ```
4. Now install the project using Poetry:

   ```bash
   poetry install
   ```

   If Poetry gets *stuck* installing, use:

   ```bash
   PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring poetry install
   ```
   
### Production (future)

TODO: Build a Dockerfile

## Run App

To run the demo app, you need to open a terminal in the project location and run the following:

```bash
streamlit run app.py
```

### Contributors

- Victor Faraggi (https://github.com/stepp1)
- Ken Miyake (https://github.com/KenMiyake)
- Andres Olivares (https://github.com/Androli12)