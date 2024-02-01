# Installation Guide

> [!IMPORTANT]
> The following guide is generic and therefore needs to be adapted to the particular software to install. This is easily done by replacing:
> 1. `<REPO-URL>` with the _URL_ of the remote git repository hosting the software (e.g. `https://github.com/Qiskit-Community/prototype-zne`).
> 2. `<SOFTWARE-NAME>` with the _name_ of the desired software (e.g. `prototype-zne`).
> 3. `<IMPORT-NAME>` with the _import name_ of the desired software (e.g. `zne`).

To follow along, make sure that your local environment is compatible with the software:
- Supported operating system (Linux, macOS, or Windows).
- Supported Python version (3.8 – 3.12).
- (Optional) We recommend updating `pip` to its latest version:
    ```sh
    pip install -U pip
    ```


## Table of contents

1. [Setting up a Python environment](#setting-up-a-python-environment)
2. [Basic PyPI installation](#basic-pypi-installation)
3. [Installation from source](#installation-from-source)
4. [Optional dependencies](#optional-dependencies)
5. [Testing the installation](#testing-the-installation)


## Setting up a Python environment

Although not strictly required, it can be useful to create a new *virtual environment* with a custom name (here referred to as `<VENV-NAME>`, common names are `venv` and `.venv`) to avoid dependency conflicts. We recommend using the latest Python version supported by the software. There are several alternatives to do this within the terminal:

- Using `venv` from the [python standard library](https://docs.python.org/3/library/venv.html):
    ```sh
    python -m venv <VENV-NAME>
    source <VENV-NAME>/bin/activate
    ```
    To deactivate and delete the virtual environment afterwards do:
    ```sh
    deactivate
    rm -r <VENV-NAME>
    ```
- Using `virtualenv` after [installation](https://virtualenv.pypa.io/en/latest/index.html):
    ```sh
    python -m virtualenv <VENV-NAME>
    source <VENV-NAME>/bin/activate
    ```
    To deactivate and delete the virtual environment afterwards do:
    ```sh
    deactivate
    rm -r <VENV-NAME>
    ```
- Using `conda` after installing [Miniconda](https://docs.conda.io/en/latest/miniconda.html):
    ```sh
    conda create -n <VENV-NAME> python=<PYTHON-VERSION>
    conda activate <VENV-NAME>
    ```
    To deactivate and delete the virtual environment afterwards do:
    ```sh
    conda deactivate
    conda env remove -n <VENV-NAME>
    ```


## Basic PyPI installation

The easiest way to install this software is from the PyPI public repository. This will install the latest stable version available, which will provide a higher level of robustness, although patches and updates might take longer to be available. From the terminal, use `pip` to install the software:
```sh
pip install <SOFTWARE-NAME>
```

To update the software to its latest release (i.e. at a later point in time):
```sh
pip install -U <SOFTWARE-NAME>
```

> [!TIP]
> If this software has not yet been published to PyPI, you will need to [install it from source](#installation-from-source). The easiest way to do so is by installing directly [from the remote git repository](#from-remote) (e.g. GitHub).


## Installation from source

To get the latest features and patches as soon as they are released, or to contribute, you will need to install from source. Please note that bleeding-edge software is less tested and therefore more likely to include bugs despite our best efforts.

### From remote

If you don't care about making changes to the source code, you can simply use `pip` to easily install it [from the remote git repository](https://pip.pypa.io/en/stable/topics/vcs-support/):
```sh
pip install <SOFTWARE-NAME>@git+<REPO-URL>
```

Updates can be retrieved at any point via:
```sh
pip install -U <SOFTWARE-NAME>@git+<REPO-URL>
```

### From local

If you wish to make changes to the source code, either for [contribution](CONTRIBUTING.md) or personal use, you will need to download a local copy of the repository and install it using `pip`:

0. Make sure you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed for version control.
1. From the terminal, clone the repository. This will add the provided URL to the list of remotes under the name `origin`:
    ```sh
    git clone <REPO-URL>.git
    ```
    Alternatively, instead of cloning the original repository, you may choose to clone your personal [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) —provided that this functionality is enabled. You can do so by using the appropriate URL and adding the original repository to the list of remotes (here under the name `upstream`). This will be required for [contribution](CONTRIBUTING.md) unless you are granted write permissions for the original repository.
    ```sh
    git clone <YOUR-FORK-URL>.git
    git remote add upstream <REPO-URL>.git
    ```
2. Change directory to the freshly cloned repository:
    ```sh
    cd <SOFTWARE-NAME>
    ```
3. Install the software and required dependencies:
    ```sh
    pip install .
    ```
4. (Optional) If you plan to make changes to the code, you can install it in editable mode by passing the `-e` flag to the `pip install` command. This will slightly impact performance, but it will also make sure that you do not need to reinstall the software after every edit for it to work as intended. This is also useful in order to pull new versions and updates from the repository without need to reinstall.
    ```sh
    pip install -e .
    ```
5. To update the software to its latest release (i.e. at a later point in time) you will need to pull new changes to the source code from the desired remote repository (e.g. `origin`, `upstream`). From the local directory holding the cloned repository (i.e. use `cd`) run:
    ```sh
    git pull <REMOTE-REPO> main
    ```
    If you did not install in editable mode, after this, you will also need to reinstall:
    ```sh
    pip install -U .
    ```
    This last command can be skipped by installing the software in editable mode.


## Optional dependencies

For users:
- `notebook` → for jupyter notebooks (e.g. `jupyter`)

For developers:
- `dev` → for development (e.g. `tox`)
- `test` → for testing (e.g. `pytest`)
- `lint` → for lint checks (e.g. `pylint`)
- `docs` → for documentation (e.g. `sphinx`)

If you wish to install any of these bundles of optional dependencies (e.g. `<OPT-BUN>`) from PyPI use the following format in your installation/update commands:
```sh
pip install [-U] <SOFTWARE-NAME>[<OPT-BUN>]
```
Or, for multiple optional bundles:
```sh
pip install [-U] <SOFTWARE-NAME>[<OPT-BUN-1>,<OPT-BUN-2>]
```

The same format can be used for installation of these bundles from _local_ source by simply substituting `<SOFTWARE-NAME>` for `.` in the install commands:
```sh
pip install [-U] [-e] .[<OPT-BUN-1>,<OPT-BUN-2>]
```
Similarly, for installation from _remote_ source:
```sh
pip install [-U] <SOFTWARE-NAME>@git+<REPO-URL>[<OPT-BUN-1>,<OPT-BUN-2>]
```

> [!TIP]
> If running `zsh` on the terminal (e.g. default shell on modern macOS devices), you will instead need to enclose the target in between quotation marks:
> ```zsh
> pip install [-U] [-e] "<SOFTWARE-NAME>[<OPT-BUN>]"
> ```
> This can be checked by running the following command:
> ```zsh
> echo $0
> ```


## Testing the installation

Users may now run the demo notebooks on their local machine (optional dependencies apply), or use the software in their own projects by simply importing it:
```python
import <IMPORT-NAME>
```
From the terminal:
```sh
$ python
Python 3.10.5 (main, Jun 23 2022, 17:15:25) [Clang 13.1.6 (clang-1316.0.21.2.5)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import <IMPORT-NAME>
>>> print(<IMPORT-NAME>)
<module '<IMPORT-NAME>' from '.venv/lib/python3.10/site-packages/<IMPORT-NAME>/__init__.py'>
```
For instructions on how to use this software see our [reference guide](docs/reference_guide.md).
