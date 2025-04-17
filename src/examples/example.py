import argparse
import importlib
import sys

from data.sources.mqtt import load_config  


def parse_args():
    parser = argparse.ArgumentParser(description="Run selected experiment.")
    parser.add_argument("--config", required=True, help="Path to config JSON file.")
    parser.add_argument("experiment", help="e.g., experiment_1")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)

    try:
        # Import from examples (sibling files)
        experiment_module = importlib.import_module(f"examples.{ args.experiment}")
    except ModuleNotFoundError:
        print(f"Could not find 'examples/{ args.experiment}.py'")
        sys.exit(1)

    experiment_module.main(config)


if __name__ == "__main__":
    main()
