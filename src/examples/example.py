# pylint: disable=E1120
import click
from examples.experiment_1 import run_experiment_1
from examples.experiment_2 import run_experiment_2

@click.group()
@click.option('--config', default="config/mockpt.json", help="Path to config file")
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = config

@cli.command()
@click.pass_context
def experiment_1(ctx):
    run_experiment_1(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def experiment_2(ctx):
    run_experiment_2(ctx.obj["CONFIG"])

if __name__ == "__main__":
    cli(obj={})
