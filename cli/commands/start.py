"""`dojo start` command."""
import shutil
from pathlib import Path

import click

from cli.core import db, kata_loader


@click.command()
@click.argument("kata_id")
@click.option("--workspace", type=click.Path(), help="Chemin du workspace.")
@click.option("--force", is_flag=True, help="Écraser le workspace s'il existe.")
def start(kata_id, workspace, force):
    """Copie les manifests d'un kata dans le workspace."""
    conn = db.get_db()
    try:
        kata = kata_loader.load_kata(kata_id)
    except FileNotFoundError:
        raise click.ClickException(f"Kata inconnue : {kata_id}")

    if workspace is None:
        workspace = db.get_data_dir() / "workspace" / kata_id
    else:
        workspace = Path(workspace).expanduser().resolve()

    if workspace.exists() and not force:
        if not click.confirm(f"Le workspace {workspace} existe déjà. L'écraser ?", default=False):
            raise click.ClickException("Annulé.")

    if workspace.exists():
        shutil.rmtree(workspace)

    initial = kata_loader.get_initial_dir(kata_id)
    if not initial.exists():
        raise click.ClickException(f"Dossier initial manquant pour {kata_id}")

    shutil.copytree(initial, workspace)
    session_id = db.create_session(conn, kata_id)

    click.echo(f"🥋 Kata '{kata['title']}' ({kata_id}) copié dans {workspace}")
    click.echo(f"   Session active : {session_id}")
