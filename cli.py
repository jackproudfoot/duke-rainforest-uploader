import click

from importer import commands as import_commands

@click.group()
def entry_point():
    pass

entry_point.add_command(import_commands.importer)

if __name__ == '__main__':
    entry_point()