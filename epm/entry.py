# entry points for command line calls via click.

import os
import click

import main

@click.command()
def launch_gui():
    main.main()
