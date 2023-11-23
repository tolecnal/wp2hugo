"""__main__.py"""

import click

from . import commands


@click.group()
def cli():
    """Start the CLI application"""


cli.add_command(commands.create)
cli.add_command(commands.stats)
