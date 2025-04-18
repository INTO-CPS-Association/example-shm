import click
from examples.experiment_1 import run_experiment_1
from examples.experiment_2 import run_experiment_2

@click.group()
def cli():
    pass

@cli.command()
@click.option('--config', default="config/mockPT.json", help="Path to config file")
def experiment_1(config):
    run_experiment_1(config)

@cli.command()
@click.option('--config', default="config/mockPT.json", help="Path to config file")
def experiment_2(config):
    run_experiment_2(config)

if __name__ == "__main__":
    cli()
