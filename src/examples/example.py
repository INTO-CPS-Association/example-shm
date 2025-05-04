# pylint: disable=E1120
import click
from examples.experiment_1 import run_experiment_1
from examples.experiment_2 import run_experiment_2
from examples.experiment_3 import (
    run_experiment_3_plot,
    run_experiment_3_publish,
    run_experiment_3_print,
)


@click.group()
@click.option('--config', default="config/production.json", help="Path to config file")
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


@cli.command()
@click.pass_context
def experiment_3_publish(ctx):
    run_experiment_3_publish(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def experiment_3_plot(ctx):
    run_experiment_3_plot(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def experiment_3_print(ctx):
    run_experiment_3_print(ctx.obj["CONFIG"])

if __name__ == "__main__":
    cli(obj={})
