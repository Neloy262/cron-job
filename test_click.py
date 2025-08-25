import click

@click.group()
def cli():
    pass

@cli.command()
def add():
    print("Add command called")

@cli.command()
def list():
    print("List command called")

if __name__ == '__main__':
    cli()