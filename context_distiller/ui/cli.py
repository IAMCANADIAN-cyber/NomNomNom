import click

@click.group()
def cli():
    pass

@cli.command()
@click.argument('folder', type=click.Path(exists=True))
def ingest(folder):
    """
    Ingests a folder into the context distiller.
    """
    click.echo(f"Ingesting folder: {folder}")
    # This is a stub for now.
    # In the future, this will call the ingestion pipeline.
    click.echo("Ingestion complete.")

@cli.command()
@click.argument('task')
@click.option('--capsule', 'capsule_path', type=click.Path(), default='out.txt', help='The path to save the capsule to.')
def query(task, capsule_path):
    """
    Queries the context distiller with a task.
    """
    click.echo(f"Querying with task: {task}")
    click.echo(f"Saving capsule to: {capsule_path}")
    # This is a stub for now.
    # In the future, this will call the retrieval and capsule assembly pipeline.
    with open(capsule_path, 'w') as f:
        f.write("This is a stub capsule.")
    click.echo("Capsule generated.")

if __name__ == '__main__':
    cli()
