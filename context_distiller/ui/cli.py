import click
from context_distiller.ingest.discover import ingest_pipeline
from context_distiller.retrieval.retrieve import retrieve_chunks
from context_distiller.core.db import get_engine, create_tables

@click.group()
def cli():
    pass

@cli.command()
def initdb():
    """Initializes the database."""
    engine = get_engine()
    create_tables(engine)
    click.echo("Database initialized.")

@cli.command()
@click.argument('folder', type=click.Path(exists=True))
def ingest(folder):
    """
    Ingests a folder into the context distiller.
    """
    click.echo(f"Ingesting folder: {folder}")
    ingest_pipeline(folder)
    click.echo("Ingestion complete.")

@cli.command()
@click.argument('task')
@click.option('--capsule', 'capsule_path', type=click.Path(), default='out.txt', help='The path to save the capsule to.')
def query(task, capsule_path):
    """
    Queries the context distiller with a task.
    """
    click.echo(f"Querying with task: {task}")

    chunks = retrieve_chunks(task, top_k=1)

    with open(capsule_path, 'w') as f:
        for chunk in chunks:
            f.write(chunk.text)
            f.write("\n\n")

    click.echo(f"Capsule generated and saved to: {capsule_path}")

if __name__ == '__main__':
    cli()
