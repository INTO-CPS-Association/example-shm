# pylint: disable=E1120
import click
from examples.acceleration_readings import read_accelerometers
from examples.aligning_readings import align_acceleration_readings
from examples.run_sysid import (
    run_sysid_and_plot,
    run_sysid_and_publish,
    run_sysid_and_print,
    live_sysid_and_publish
)
from examples.run_mode_clustering import (
    run_mode_clustering_with_local_sysid,
    run_mode_clustering_with_remote_sysid,
    run_live_mode_clustering_with_remote_sysid,
    run_live_mode_clustering_with_remote_sysid_and_publish
)
from examples.run_mode_tracking import (
    run_mode_tracking_with_local_sysid,
    run_mode_tracking_with_remote_sysid,
    run_live_mode_tracking_with_remote_sysid
)
from examples.run_model_update import (
    run_model_update_local_sysid, 
    run_model_update_remote_sysid,
    run_live_model_update_remote_clustering,
    run_live_model_update_with_remote_clustering_and_publish,
)

@click.group()
@click.option('--config', default="config/production.json", help="Path to config file")
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
def align_readings(ctx):
    align_acceleration_readings(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def sysid_and_print(ctx):
    run_sysid_and_print(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def sysid_and_plot(ctx):
    run_sysid_and_plot(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def sysid_and_publish(ctx):
    run_sysid_and_publish(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def live_sysid_publish(ctx):
    live_sysid_and_publish(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def clustering_with_local_sysid(ctx):
    run_mode_clustering_with_local_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def clustering_with_remote_sysid(ctx):
    run_mode_clustering_with_remote_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def live_clustering_with_remote_sysid(ctx):
    run_live_mode_clustering_with_remote_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def live_clustering_with_remote_sysid_and_publish(ctx):
    run_live_mode_clustering_with_remote_sysid_and_publish(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def mode_tracking_with_local_sysid(ctx):
    run_mode_tracking_with_local_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def mode_tracking_with_remote_sysid(ctx):
    run_mode_tracking_with_remote_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def live_mode_tracking_with_remote_sysid(ctx):
    run_live_mode_tracking_with_remote_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def model_update_local_sysid(ctx):
    run_model_update_local_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def live_model_update_remote_sysid(ctx):
    run_model_update_remote_sysid(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def live_model_update_remote_clustering(ctx):
    run_live_model_update_remote_clustering(ctx.obj["CONFIG"])

@cli.command()
@click.pass_context
def live_model_update_remote_clustering_and_publish(ctx):
    run_live_model_update_with_remote_clustering_and_publish(ctx.obj["CONFIG"])


if __name__ == "__main__":
    cli(obj={})
