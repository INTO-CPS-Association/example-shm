# Examples

This directory contains examples demonstrating how to use
the **EXAMPLE-SHM** package.

## Install the Package from Poetry Build

To install the package built using `poetry`, follow these steps:

### Step 1: Build the Package

```bash
poetry build
```

This will create a `.whl` file in the `dist/` directory,
e.g., `dist/cp_sens-0.1.0-py3-none-any.whl`.

### Step 2: Create and Activate a Virtual Environment

```py
python -m venv .venv
source .venv/bin/activate        # On Linux/macOS
.\.venv\Scripts\Activate.ps1     # On Windows
```

### Step 3: Install the Built Package

```py
pip install example_shm-<version>-py3-none-any.whl
```

Replace `<version>` with the version number found in the `.whl`
filename. (e.g `0.1.0`).

## Running the Examples

There are two examples.

* **example_1** demonstrates the use of `Accelerometer` class to extract
  accelerometer measurements from MQTT data stream.
* **example_2** demonstrates the use of `Aligner` class to collect and
  align accelerometer measurements from multiple MQTT data streams.

To run these examples, use:

```bash
python src/examples/example_1.py
python src/examples/example_2.py
```

You can also run these examples in **poetry** environment using

```bash
poetry run example_1
poetry run example_2
```
