# entry.py
# entry points from command line calls.

import os
import click

import main

@click.command()
def launch_gui():
    main.main()
