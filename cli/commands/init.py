"""`dojo init` command."""
import os
from pathlib import Path

import click

from cli.core import db


@click.command()
@click.option("--local", is_flag=True, help="Initialiser dans le répertoire courant.")
def init(local):
    """Initialise le Dojo (profil, DB, dossiers)."""
    target = Path.cwd() if local else db.DEFAULT_HOME
    os.environ["K8S_DOJO_HOME"] = str(target)
    conn = db.get_db()
    db.init_db(conn)
    profile = db.ensure_profile(conn)
    click.echo(f"✅ Dojo initialisé dans {target}")
    click.echo(f"   Profil ID : {profile['id']}")
