# Examples

This directory contains examples demonstrating how to use the EXAMPLE-SHM package.

## Installing the Package from Poetry Build

To install the package built using `poetry`, follow these steps:

### Step 1: Build the Package

```bash
poetry build
```

This will create a .whl file in the dist/ directory, e.g., dist/cp_sens-0.1.0-py3-none-any.whl. 

### Step 2: Create and Activate a Virtual Environment

python -m venv .venv
source .venv/bin/activate        # On Linux/macOS
.\.venv\Scripts\Activate.ps1     # On Windows

### Step 3: Install the Built Package
pip install dist/example_shm-<version>-py3-none-any.whl
Replace <version> with the version number found in the .whl filename. (e.g 0.1.0)


## Running the Example

A simple example is provided to run the main() function from experiment_1.py.

To run this example, use:
```bash
python examples/example.py
```
