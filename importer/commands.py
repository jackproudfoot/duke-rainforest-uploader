import click

from .import_media import *

@click.group()
def importer():
    pass

@importer.command()
@click.argument('media', type=click.Path(exists=True))
@click.argument('harddrive', type=click.Path(exists=True))
def plan(media, harddrive):
    """Import media from SD card to hard drive"""
    
    click.echo(click.style("🦜 Squawk. Generating import plan. Squawk.", fg='cyan'))
    
    plan = import_plan(media, harddrive)

    _print_plan(plan)

    click.echo(click.style("🦜 Squawk. Plan is complete. Squawk.", fg='cyan'))

@importer.command(name = 'import')
@click.argument('media', type=click.Path(exists=True))
@click.argument('harddrive', type=click.Path(exists=True))
def execute_plan(media, harddrive):
    click.echo(click.style("🦜 Squawk. Importing media. Squawk.", fg='cyan'))

    plan = import_plan(media, harddrive)

    _print_plan(plan)

    import_media(plan)

    click.echo(click.style("🦜 Squawk. Import complete. Squawk.", fg='cyan'))

def _print_plan(plan):
    if (len(plan['flight']) > 0):
        click.echo('Flight changes:')

    for flight in plan['flight']:
        if flight['type'] == 'rename_flight':
            click.echo(click.style('\t~ Rename Flight {} -> Flight {}'.format(flight['current_flight_num'], flight['flight_num']), fg='yellow'))
        elif flight['type'] == 'create_flight':
            click.echo(click.style('\t+ Create Flight {}'.format(flight['flight_num']), fg='green'))

    click.echo('\nMedia to be imported:')
    
    for media in plan['media']:
        media_dir = media['new_path'].parent.name

        color = 'red' if media_dir == 'unparsed' else 'yellow' if media_dir == 'unsorted' else 'green'
        
        click.echo(click.style('\t+ {}'.format(media['new_path']), fg=color))