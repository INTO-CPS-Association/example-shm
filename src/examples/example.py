# pylint: disable=E1120
import click
from examples.acceleration_readings import read_accelerometers
from examples.aligning_readings import align_acceleration_readings
from examples.run_pyoma import (
    run_oma_and_plot,
    run_oma_and_publish,
    run_oma_and_print,
    run_oma_and_plot_continuously,
    read_accelerometers_and_plot,
    read_accelerometers_and_plot_continuously,
)
from examples.mode_tracking import (
    run_mode_clustering_with_local_sysid,
    run_mode_tracking_with_remote_sysid,
)
from examples.run_fatigue import (
    run_damage_print,
    run_fatigue_and_plot,
)
from examples.updating_parameters import run_model_update
from examples.cantilever_beam import run_cantilever_beam


@click.group()
@click.option('--config', default="config/production_VA.json", help="Path to config file")
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = config

@cli.command()
@click.pass_context
def accelerometers(ctx):
    read_accelerometers(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def accelerometers_and_plot(ctx):
    read_accelerometers_and_plot(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def accelerometers_and_plot_continuously(ctx):
    read_accelerometers_and_plot_continuously(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def align_readings(ctx):
    align_acceleration_readings(ctx.obj["CONFIG"])


@cli.command()
@click.pass_context
def oma_and_publish(ctx):
    run_oma_and_publish(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def oma_and_plot(ctx):
    run_oma_and_plot(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def oma_and_plot_continuously(ctx):
    run_oma_and_plot_continuously(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def oma_and_print(ctx):
    run_oma_and_print(ctx.obj["CONFIG"])


@cli.command()
@click.pass_context
def mode_tracking_with_local_sysid(ctx):
    run_mode_clustering_with_local_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def mode_tracking_with_remote_sysid(ctx):
    run_mode_tracking_with_remote_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def cantilever_beam(ctx):
    run_cantilever_beam(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def damage_print(ctx):
    run_damage_print()

@cli.command()
@click.pass_context
def fatigue_and_plot(ctx):
    run_fatigue_and_plot()

@cli.command()
@click.pass_context
def model_update(ctx):
    run_model_update(ctx.obj["CONFIG"])
if __name__ == "__main__":
    cli(obj={})
