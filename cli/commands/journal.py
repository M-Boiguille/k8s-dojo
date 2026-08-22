"""`dojo journal` sub-commands."""
import os
import subprocess
from datetime import datetime
from pathlib import Path

import click

from cli.core import db, llm_client


@click.group()
def journal():
    """Gestion du journal réflexif."""


@journal.command("generate")
def generate():
    """Génère un brouillon de journal avec l'IA."""
    conn = db.get_db()
    session = db.get_last_finished_session(conn) or db.get_last_session(conn)
    if not session:
        raise click.ClickException("Aucune session terminée. Lance `dojo submit` d'abord.")

    profile = db.ensure_profile(conn)
    raw = session["raw_log"] or "Aucun log brut enregistré."
    history = (
        f"Total de katas : {profile['total_katas']}, "
        f"indices utilisés : {profile['total_hints_used']}"
    )

    prompt = llm_client.load_prompt(
        "system_journalist",
        session_raw_log=raw,
        user_history=history,
    )
    result = llm_client.call_deepseek(prompt)

    content = result.get("markdown_content") if result and "markdown_content" in result else None
    if not content:
        date = datetime.now().strftime("%Y-%m-%d")
        content = f"# {date}\n\n## 🎯 Objectif\nRésoudre le kata {session['kata_id']}.\n\n## 🔨 Ce que j'ai fait\n{raw[:500]}\n\n## 🐛 Cause racine\nÀ compléter.\n\n## ✅ Correction\nÀ compléter.\n\n## 📚 Leçon retenue\nÀ compléter.\n"
        if result and "_error" in result:
            click.echo("⚠️  IA offline – brouillon généré localement.")

    draft_dir = db.get_data_dir() / "private" / "drafts"
    draft_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y-%m-%d')}.md"
    path = draft_dir / filename
    path.write_text(content, encoding="utf-8")
    click.echo(f"✏️  Brouillon créé : {path}")


@journal.command("review")
def review():
    """Ouvre le dernier brouillon dans $EDITOR."""
    draft_dir = db.get_data_dir() / "private" / "drafts"
    if not draft_dir.exists():
        raise click.ClickException("Aucun brouillon. Lance `dojo journal generate` d'abord.")

    files = sorted(draft_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise click.ClickException("Aucun brouillon à relire.")

    editor = os.environ.get("EDITOR", "nano")
    target = files[0]
    click.echo(f"Ouverture de {target} dans {editor}...")
    subprocess.call([editor, str(target)])

    if click.confirm("Valider ce journal ? (o/N)", default=False):
        # On ne fait que valider le brouillon ; publish effectue la copie publique
        click.echo("✅ Brouillon validé. Utilise `dojo publish` pour le publier.")
