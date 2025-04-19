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
poetry run experiment_1          # run one experiment with real data
```

The `poetry build` will create a `.whl` file in the `dist/` directory, e.g., `dist/cp_sens-0.1.0-py3-none-any.whl`.

## Testing

Write tests in the _tests_ directory. Be sure to name any new files as
_test_*_.py_. To run all tests, with coverage:

```bash
pytest -m unit         # run unit tests
pytest -m integration  # run integration tests
pytest                 # run all the tests
```

## Use
To run the examples with the default config
```bash
python .\src\examples\example.py experiment-1
python .\src\examples\example.py experiment-2
```

To run the examples with specified config
```bash
python .\src\examples\example.py --config .path_to\config.json experiment-1
```
Example
```bash
python .\src\examples\example.py --config .\config\mockpt.json experiment-1
```

Please see [examples](src/examples/README.md) for typical usage of the package.
