"""`dojo publish` command."""
import shutil
from pathlib import Path

import click

from cli.core import db


@click.command()
def publish():
    """Publie le dernier brouillon validé dans public/journal/."""
    draft_dir = db.get_data_dir() / "private" / "drafts"
    if not draft_dir.exists():
        raise click.ClickException("Aucun brouillon. Lance `dojo journal generate` d'abord.")

    files = sorted(draft_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise click.ClickException("Aucun brouillon à publier.")

    latest = files[0]
    pub_dir = db.get_data_dir() / "public" / "journal"
    pub_dir.mkdir(parents=True, exist_ok=True)
    dest = pub_dir / latest.name
    shutil.copy2(latest, dest)

    conn = db.get_db()
    session = db.get_last_finished_session(conn)
    if session:
        db.mark_session_published(conn, session["id"])

    click.echo(f"📰 Journal publié : {dest}")
