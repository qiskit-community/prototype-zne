# Repository structure

## Guidelines

- [`CITATION.bib`](CITATION.bib) --
  BibTeX file including the bibliographic reference to cite the software.
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) --
  participation in the repository is subject to these conduct guidelines.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) --
  guidelines to contribute to the repository.
- [`DEPRECATION.md`](DEPRECATION.md) --
  deprecation policy.
- [`FILEMAP.md`](FILEMAP.md) --
  a summary of the repository structure and explanations of the different files and folders.
- [`INSTALL.md`](INSTALL.md) --
  guidelines to install the software contained in this repo.
- [`LICENSE.txt`](LICENSE.txt) --
  one of the [standard legal requirements](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) for an open source project. There are different types of [licenses for software](https://en.wikipedia.org/wiki/Software_license), some of the most popular being [open source](https://opensource.org/licenses).
- [`README.md`](README.md) -- 
  main readme for repository.


## Software package/library

- `<pyproject_qiskit>` -- 
  it will have a different name for each repository using the [`pyproject-qiskit` template](https://github.com/pedrorrivero/pyproject-qiskit), and it holds the source code for the software. This name will determine how the software is imported after installation (e.g. `from <pyproject_qiskit> import __version__`).
- [`CHANGELOG.md`](CHANGELOG.md) --
  file that logs all the changes made to the software on each new version release.
- [`docs`](docs) -- 
  documentation for the repository (e.g. tutorials, API docs, reference guide).
- [`test`](test) -- 
  folder where all project tests are located. It is a good practice to cover your project with tests to ensure correctness of implementation.
  - [`acceptance`](test/acceptance/) -- 
    folder for [acceptance tests](https://en.wikipedia.org/wiki/Acceptance_testing).
  - [`integration`](test/integration/) -- 
    folder for [integration tests](https://en.wikipedia.org/wiki/Integration_testing).
  - [`system`](test/system/) -- 
    folder for [system tests](https://en.wikipedia.org/wiki/System_testing).
  - [`unit`](test/unit/) -- 
    folder for [unit tests](https://en.wikipedia.org/wiki/Unit_testing).
- [`pyproject.toml`](pyproject.toml) --
  file containing the [build and package configurations](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) for the python project. This file also contains configurations for:
  - [Black](https://black.readthedocs.io/) --
    a tool for automatic code formatting.
  - [Autoflake](https://github.com/PyCQA/autoflake) -- 
    a tool for removing unused imports and variables.


## CI/CD

- [`.cz.toml`](.cz.toml) --
  configuration file for [commitizen](https://commitizen-tools.github.io/commitizen/), a tool for software release management.
- [`.github`](.github) -- 
  folder for configuring anything related to GitHub.
  - [`ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE/) -- 
    folder holding the [templates for issues](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/manually-creating-a-single-issue-template-for-your-repository) in the repository.
  - [`workflows`](.github/workflows/) -- 
    configurations for [GitHub Actions](https://docs.github.com/en/actions) (e.g. CI/CD scripts).
  - [`.templatesyncignore`](.github/.templatesyncignore) -- 
    file declaring paths to be ignored by the [template sync action](https://github.com/marketplace/actions/actions-template-sync).
  - [`CODEOWNERS`](.github/CODEOWNERS) -- 
    file defining individuals and teams that are [responsible for code](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) in the repository.
  - [`PULL_REQUEST_TEMPLATE`](.github/PULL_REQUEST_TEMPLATE.md) -- 
    file holding the [template for pull requests](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) in the repository.
- [`.gitignore`](.gitignore) --
  git-specific file that tells which files to ignore when tracking/pushing/committing code (those files will not be tracked by git).
- [`.pre-commit-config.yaml`](.pre-commit-config.yaml) --
  configuration for [pre-commit](https://pre-commit.com/), a framework for managing and maintaining [git hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks).
- [`.travis.yaml`](.travis.yaml) --
  configuration file for [Travis-CI](https://www.travis-ci.com/); similar to [GitHub Actions](https://docs.github.com/en/actions) (e.g. CI/CD scripts).
- [`tools`](tools) -- 
  auxiliary tools and scripts for repository maintenance.
  - [`extremal_dependency_versions.py`](tools/extremal_dependency_versions.py) --
    script for testing against minimum and development versions of specific dependencies.
  - [`symlink_submodule.py`](tools/symlink_submodule.py) -- 
    auxiliary script to create symlinks to submodule files in base repo.
  - [`travis_before_script.bash`](tools/travis_before_script.bash) --
    auxiliary script for extremal dependency testing using [Travis-CI](https://www.travis-ci.com/).


## Testing and style

- [`.coveragerc`](.coveragerc) --
  configuration for the [code coverage tool](https://coverage.readthedocs.io) used in testing.
- `coverage-html` -- 
  autogenerated folder holding html documents to explore code coverage after running the coverage tool. The entry point is `coverage-html/index.html`.
- [`.flake8`](.flake8) --
  configuration for [Flake8](https://flake8.pycqa.org/), a tool for code style enforcing.
- [`.gitlint`](.gitlint) --
  configuration for [Gitlint](https://jorisroovers.com/gitlint/latest/), a tool for checking commit message style.
- [`.isort.cfg`](.isort.cfg) --
  configuration for [isort](https://pycqa.github.io/isort/), a tool to sort and group python imports automatically.
- [`.mypy.ini`](.mypy.ini) --
  configuration for [mypy](https://www.mypy-lang.org/), a tool to for static type checking in python via [type annotations](https://docs.python.org/3/library/typing.html).
- [`.pylintrc`](.pylintrc) --
  configuration for [Pylint](https://pylint.readthedocs.io/), a tool for static code analysis (e.g. lint errors).
- [`pytest.ini`](pytest.ini) --
  configuration for the [PyTest framework](https://pytest.org) used for testing the software.
- [`tox.ini`](tox.ini) -- 
  configuration file for [tox](https://tox.readthedocs.io/en/latest/) framework that aims to automate and standardize testing in Python. Eases the packaging, testing and release process of Python software.
