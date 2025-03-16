# Purpose

This project creates a fully-functional demo of CP-SENS project.
The demo is to be run inside the
[DTaaS platform](https://github.com/into-cps-association/DTaaS).

## Development Setup

This is a [poetry-based project](https://python-poetry.org/docs/).
The relevant commands to run the project are:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # On Windows
source .venv/bin/activate        # On Linux

pip install poetry               #Specifically install poetry to your system
# If you have poetry installed globally
poetry env activate              # shows the command to activate venv
poetry install                   # installs all required python packages
pylint src tests --rcfile=.pylintrc    # runs linting checks

poetry build                     # builds cp-sens package that can be published on pip
poetry run start                 # runs the main script
poetry run experiment_1          # run one experiment with real data
```

## Testing

Write tests in the _tests_ directory. Be sure to name any new files as
_test_*_.py_. To run all tests, with coverage:

```bash
pytest
```
