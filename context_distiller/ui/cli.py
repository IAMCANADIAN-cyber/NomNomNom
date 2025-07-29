import click
from context_distiller.ingest.discover import discover_files, get_file_type
from context_distiller.ingest.extract_text import extract_text_from_file
from context_distiller.ingest.extract_pdf import extract_text_from_pdf
from context_distiller.ingest.extract_docx import extract_text_from_docx
from context_distiller.represent.chunking import chunk_text
from context_distiller.represent.entities import extract_entities

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
    for filepath in discover_files(folder):
        file_type = get_file_type(str(filepath))
        text = ""
        if file_type in ['.txt', '.md', '.html']:
            text = extract_text_from_file(str(filepath))
        elif file_type == '.pdf':
            text = extract_text_from_pdf(str(filepath))
        elif file_type == '.docx':
            text = extract_text_from_docx(str(filepath))
        else:
            click.echo(f"Skipping unsupported file type: {filepath}")
            continue

        if text:
            chunks = chunk_text(text)
            for chunk in chunks:
                entities = extract_entities(chunk)
                # For now, just print the entities
                if entities:
                    click.echo(f"Entities found in {filepath}: {entities}")

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
