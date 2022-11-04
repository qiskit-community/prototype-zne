# Quantum Prototype Installation Guide

To follow along, make sure that your local environment is compatible with the package:
- Supported operating system (Linux, macOS, or Windows).
- Supported Python version (3.8 – 3.11).
- (Optional) We recommend updating `pip` to its latest version:
    ```
    pip install -U pip
    ```


## Table of contents

1. [Setting up a Python environment](#setting-up-a-python-environment)
2. [Basic PyPI installation](#basic-pypi-installation)
3. [Installation from source](#installation-from-source)
4. [Optional dependencies](#optional-dependencies)
5. [Testing the installation](#testing-the-installation)


## Setting up a Python environment

Although not strictly required, it can be useful to create a new *virtual environment* with a custom name (here referred to as `<VENV-NAME>`, common names are `venv` and `.venv`) to avoid dependency conflicts. We recommend using the latest Python version supported by the package. There are several alternatives to do this within the terminal:

- Using `venv` from the [python standard library](https://docs.python.org/3/library/venv.html):
    ```
    python -m venv <VENV-NAME>
    source <VENV-NAME>/bin/activate
    ```
    To deactivate and delete the virtual environment afterwards do:
    ```
    deactivate
    rm -r <VENV-NAME>
    ```
- Using `virtualenv` after [installation](https://virtualenv.pypa.io/en/latest/index.html):
    ```
    python -m virtualenv <VENV-NAME>
    source <VENV-NAME>/bin/activate
    ```
    To deactivate and delete the virtual environment afterwards do:
    ```
    deactivate
    rm -r <VENV-NAME>
    ```
- Using `conda` after installing [Miniconda](https://docs.conda.io/en/latest/miniconda.html):
    ```
    conda create -n <VENV-NAME> python=<PYTHON-VERSION>
    conda activate <VENV-NAME>
    ```
    To deactivate and delete the virtual environment afterwards do:
    ```
    conda deactivate
    conda env remove -n <VENV-NAME>
    ```


## Basic PyPI installation

<!-- :warning: **Currently unavailable** -->

The easiest way to install this package is from the PyPI public repository. This will install the latest stable version available, which will provide a higher level of robustness, although patches and updates might take longer to be available. From the terminal, use pip to install the package:
```
pip install prototype-zne
```

To update the package to its latest release (i.e. at a later point in time):
```
pip install -U prototype-zne
```


## Installation from source

To get the latest features and patches as soon as they are released, or to contribute, you will need to install from source. Please note that bleeding-edge software is less tested and therefore more likely to include bugs despite our best efforts.

0. Make sure you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed for version control.
1. From the terminal, clone the repository. This will add the provided URL to the list of remotes under the name `origin`:
    ```
    git clone https://github.com/qiskit-community/prototype-zne.git
    ```
    Alternatively, instead of cloning the original repository, you may choose to clone your personal [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) —provided that this functionality is enabled. You can do so by using the appropriate URL and adding the original repository to the list of remotes (here under the name `upstream`). This will be required for [contribution](CONTRIBUTING.md) unless you are granted write permissions for the original repository.
    ```
    git clone <YOUR-FORK-URL>
    git remote add upstream https://github.com/qiskit-community/prototype-zne.git
    ```
2. Change directory to the freshly cloned repository:
    ```
    cd prototype-zne
    ```
3. Install the package and required dependencies:
    ```
    pip install .
    ```
4. (Optional) If you plan to make changes to the code, you can install it in editable mode by passing the `-e` flag to the `pip install` command. This will slightly impact performance, but it will also make sure that you do not need to reinstall the package after every edit for it to work as intended. This is also useful in order to pull new versions and updates from the repository without need to reinstall.
    ```
    pip install -e .
    ```
5. To update the package to its latest release (i.e. at a later point in time) you will need to pull new changes to the source code from the desired remote repository (e.g. `origin`, `upstream`). From the local directory holding the cloned repository (i.e. use `cd`) run:
    ```
    git pull <REMOTE-REPO> main
    ```
    If you did not install in editable mode, after this, you will also need to reinstall:
    ```
    pip install .
    ```
    This last command can be skipped by installing the package in editable mode.


## Optional dependencies

For users:
- `notebook` → for jupyter notebooks (e.g. `jupyter`)

For developers:
- `dev` → for development (e.g. `tox`)
- `test` → for testing (e.g. `pytest`)
- `lint` → for lint checks (e.g. `pylint`)
- `docs` → for documentation (e.g. `sphinx`)

If you wish to install any of these bundles of optional dependencies (e.g. `<OPT-BUN>`) from PyPI use the following format in your installation/update commands:
```
pip install [-U] prototype-zne[<OPT-BUN>]
```
Or, for multiple optional bundles:
```
pip install [-U] prototype-zne[<OPT-BUN-1>,<OPT-BUN-2>]
```
If running `zsh` on the terminal (e.g. default shell on macOS devices), you will instead need to enclose the target in between quotation marks:
```
pip install [-U] "prototype-zne[<OPT-BUN>]"
```
This can be checked by running the following command:
```
echo $0
```

The same format can be used for installation of these bundles from source by simply substituting `prototype-zne` for `.` in the install commands. For example:
```
pip install .[<OPT-BUN-1>,<OPT-BUN-2>]
```

Editable mode can also be enabled:
```
pip install -e ".[<OPT-BUN-1>,<OPT-BUN-2>]"
```

## Testing the installation

Users may now run the demo notebooks on their local machine (optional dependencies apply), or use the package in their own software by simply importing it:
```python
import zne
```
From the terminal:
```
$ python
Python 3.10.5 (main, Jun 23 2022, 17:15:25) [Clang 13.1.6 (clang-1316.0.21.2.5)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import zne
>>> print(zne)
<module 'zne' from '.venv/lib/python3.10/site-packages/zne/__init__.py'>
```
For instructions on how to use this package see [here](docs/reference_guide.md).
