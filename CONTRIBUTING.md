[![code style: black](https://img.shields.io/badge/Code_Style-black-000000.svg?style=flat)](https://github.com/psf/black)
[![docs style: Google](https://img.shields.io/badge/Docs_Style-Google-DB4437.svg?style=flat&logo=Google&logoColor=white)](https://docs.idmod.org/projects/doc-guidance/en/latest/docstrings.html)
[![commit style: Conventional Commits](https://img.shields.io/badge/Commit_Style-Conventional_Commits-E86F76.svg?style=flat)](https://www.conventionalcommits.org/)

[![pre-commit](https://img.shields.io/badge/pre--commit-FAB040.svg?style=flat&logo=pre-commit&logoColor=white)](https://pre-commit.com/)

# Contributing
__We appreciate all kinds of help, so thank you!__

This guide is for those who want to extend the module or documentation. If you just want to use the software, read [this other guide](./docs/reference_guide.md) instead.


## Table of contents
0. [Giving feedback](#giving-feedback)
1. [Initial set-up](#initial-set-up)
    - [Installing dependencies](#installing-dependencies)
    - [Adding git hooks](#adding-git-hooks)
2. [Style guide](#style-guide)
    - [Code](#code)
    - [Documentation](#documentation)
    - [Copyright notice](#copyright-notice)
    - [Commits](#commits)
3. [GitHub issues and pull-requests](#github-issues-and-pull-requests)
4. [Running tests](#running-tests)
    - [Bulk testing](#bulk-testing)
    - [Granular testing](#granular-testing)
    - [Custom testing](#custom-testing)
5. [Making a pull request](#making-a-pull-request)
    - [Step-by-step guide](#step-by-step-guide)
    - [Pull request checklist](#pull-request-checklist)


## Giving feedback

We encourage your feedback!

Other than submitting new source code, users can contribute in a number of meaningful ways. You can share your thoughts with us by:

- _Opening an issue_ in the repository for reporting bugs, enhancements, or requesting new features.
- _Starting a conversation on GitHub Discussions_ and engaging with researchers, developers, and other users regarding this project.


## Initial set-up

### Installing dependencies
In order to contribute, you will need to [install the module from source](/INSTALL.md#installation-from-source) with developer dependencies (i.e. `dev` bundle) and, optionally, in editable mode. We recommend using the latest version of python available despite the fact that this software maintains support for legacy versions, as some of the developer tools require newer functionality to work (e.g. type annotation format introduced in python 3.10).

If you do not have write permissions to the original repository, you will need to open a fork in your personal account first, and submit all pull requests (PR) from there. Even if you have write permissions, forking the repository should always work provided that this functionality is enabled, so this is the recommended approach.

If forking is disabled and you do not have write permissions, we recommend [reaching out](#giving-feedback) to the repository owners.

### Adding git hooks
Since this repo adheres to the [conventional commits](#commits) standard we suggest enabling _Pre-commit_ git hooks to validate the format of your commit messages. From the terminal, after [activating your virtual environment](/INSTALL.md#setting-up-a-python-environment), run:
```
pre-commit install -t commit-msg
```

Additionally, in order to ensure meeting the quality of code standards for this repository, no PR will be merged if the `tox` checks fail, so it is better to encounter failures one at a time on every commit attempt rather than having to fix them all simultaneously before merging. For this reason, although this step is optional, we recommend setting up `pre-commit` to check that your new code is in good shape before committing:
```
pre-commit install -t pre-commit
```

Alternatively, you can install both hooks with just one command:
```
pre-commit install
```

Notice that this tool is not a substitute of `tox`, which should still be used to run tests and ensure that lint checks pass with all relevant versions. Instead, it should be regarded simply as a convenient device for continuously performing light-weight lint checks in an incremental fashion.


## Style guide

### Code
Code in this repository should conform to [PEP8](https://www.python.org/dev/peps/pep-0008) standards, the usual [Python convention](https://namingconvention.org/python/) for naming, mandatory [type annotations](https://docs.python.org/3/library/typing.html), and a maximum line length of 100 characters —among other things.

Lint checks are run to validate this according to the following config files (no edits allowed):
- [Flake8](.flake8)
- [Isort](.isort.cfg)
- [Black](pyproject.toml)
- [Pylint](.pylintrc)
- [MyPy](.mypy.ini)

For help fixing the format and complying to the lint rules we provide a pre-configured tox environment which can be run by:
```
tox -e style
```

### Documentation
We adhere to the [google docstring guide](https://docs.idmod.org/projects/doc-guidance/en/latest/docstrings.html). If you make any changes to the code, remember updating the docstring wherever relevant.

### Copyright notice
All source files in the repository must begin with the appropriate copyright notice. For instance, for the year 2024:
```python
# This code is part of Qiskit.
#
# (C) Copyright IBM 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
```

### Commits
In order to properly conform to semantical versioning and keep track of changelogs, we adhere to the [Conventional Commits](https://www.conventionalcommits.org/) standard for (git) commit messages as defined in the following config files:
- [Gitlint](.gitlint)
- [Commitizen](.cz.toml)

These configs can be enforced through [pre-commit git hooks](#adding-git-hooks).


## GitHub issues and pull-requests

Issues in this repository are assigned a Difficulty Class (DC) and Priority Level (PL) from 1 to 5. 

Difficulty classes roughly correspond to:
- `DC-1` → Basic knowledge
- `DC-2` → Application/user level knowledge
- `DC-3` → Domain/technology specific knowledge
- `DC-4` → Multidomain knowledge
- `DC-5` → System-wide knowledge

Priority levels also apply to PRs, and denote:
- `PL-1` → High
- `PL-2` → Medium-high
- `PL-3` → Medium
- `PL-4` → Medium-low
- `PL-5` → Low


## Running tests

### Bulk testing
To run all functionality tests, lint checks, and validate coverage in one go and for different python versions we use [__tox__](https://pypi.org/project/tox/):
```
tox
```

### Granular testing
Alternatively, you can choose to run a particular batch of tests individually:
- To run functionality tests on a particular python version:
    ```
    tox -e {env}
    ```
    where you replace `{env}` with (for instance) `py38`, `py39`, `py310`, `py311` or `py312` depending on which version of python you have (to check python version, type `python --version` in the terminal).
- To run lint checks (checks formatting/style/syntax):
    ```
    tox -e lint
    ```
- Coverage validation is can be performed by:
    ```
    tox -e coverage
    ```

Additional tox environments are available for optional tasks:
- Auto-formatting for style compliance (non-comprehensive):
    ```
    tox -e style
    ```
- Building documentation:
    ```
    tox -e docs
    ```
- Runtime tests and lint checks for jupyter notebooks under different python versions:
    ```
    tox -e {env}-notebook
    ```
- Auto-formatting for style compliance in jupyter notebooks (non-comprehensive):
    ```
    tox -e style-notebook
    ```

You can run several environments in one call by passing a list of comma-separated environment names (i.e. no spaces). For instance:
```
tox -e coverage,lint
```

To see the complete list of environments with short descriptions:
```
tox -av
```

### Custom testing
For complete control over the developer tools you can invoke them directly after installation of the corresponding [optional dependencies bundle(s)](/INSTALL.md#optional-dependencies). Note that, unlike custom testing, invoking any `tox` environment only requires the `dev` bundle (i.e. other dependencies are handled internally by `tox`). Basic invocations according to the corresponding config files are:

- [__Autoflake__](https://pypi.org/project/autoflake/) for style fixing:
    ```
    autoflake [-c] [-i] --remove-all-unused-imports [-r] <TARGET>
    ```
- [__Black__](https://pypi.org/project/black/) for code formatting:
    ```
    black <TARGET> [--check]
    ```
- [__Flake8__](https://pypi.org/project/flake8/) for style enforcing:
    ```
    flake8 <TARGET>
    ```
- [__Isort__](https://pypi.org/project/isort/) for ordering imports:
    ```
    isort <TARGET> [--check-only]
    ```
- [__Mypy__](https://pypi.org/project/mypy/) for static type checking:
    ```
    mypy <TARGET>
    ```
- [__nbQA__](https://pypi.org/project/nbqa/) for plugging lint tools into jupyter notebook cells:
    ```
    nbqa <LINT-TOOL-CALL>
    ```
- [__Pylint__](https://pypi.org/project/pylint/) for static code analysis:
    ```
    pylint [-rn] <TARGET>
    ```
- [__Pytest__](https://pypi.org/project/pytest/) for functionality tests according to its [config file](pytest.ini):
    ```
    pytest --no-cov
    ```
    and code coverage:
    ```
    pytest --cov <TARGET> --cov-fail-under <PERCENTAGE>
    ```
- [__Treon__](https://pypi.org/project/treon/) for testing jupyter notebooks:
    ```
    treon <TARGET> [--threads <NUMBER>]
    ```
    _Note: treon notebook tests check for execution and time-out errors, not correctness._


## Making a pull request

### Step-by-step guide
1. To make a contribution, first set up a branch (here called `<BRANCH-NAME>`) either in your fork (i.e. `origin`) or in a clone of original repository (i.e. `upstream`). In the absence of a fork, the only remote (i.e. original) will simply be referred to all the time by the name `origin` (i.e. replace `upstream` in all commands):
   ```
   git checkout main
   git pull origin main
   git checkout -b <BRANCH-NAME>
   ```
   ... make your contribution now (edit some code, add some files) ...
   ```
   git add .
   git commit -m 'initial working version of my contribution'
   git push -u origin <BRANCH-NAME>
   ```
2. Before making a pull request always get the latest changes from `main` (`upstream` if there is a fork, `origin` otherwise):
   ```
   git checkout main
   git pull upstream
   git checkout <BRANCH-NAME>
   git merge main
   ```
   ... fix merge conflicts here if any ...
   ```
   git add .
   git commit -m 'merged updates from main'
   git push origin <BRANCH-NAME>
   ```
3. Go back to the appropriate repository on GitHub (i.e. fork or original), switch to your contribution branch (same name: `<BRANCH-NAME>`), and click _"Pull Request"_. Write a clear explanation of the feature.
4. Under _Reviewer_, select one of the repository owners.
5. Click _"Create Pull Request"_. Please mark as draft if not ready for review.
6. Once your pull request is ready, remove the draft status, and ping the reviewers. If everything is ok, the PR will be merged after review, otherwise updates will be requested.

### Pull request checklist
When submitting a pull request and you feel it is ready for review, please ensure that:
1. The code follows the _code style_ of this project.
2. Successfully passes the _unit tests_.
3. Validate appropriate _code coverage_.

This can be easily checked through the pre-configured [bulk tests](#bulk-testing).
