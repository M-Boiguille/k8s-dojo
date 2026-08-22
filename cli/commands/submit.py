"""`dojo submit` command."""
import re
from datetime import datetime
from pathlib import Path

import click

from cli.core import db, k8s_client, kata_loader, llm_client


def _read_manifests(workspace: Path) -> str:
    parts = []
    for ext in ("*.yaml", "*.yml"):
        for f in sorted(workspace.glob(ext)):
            parts.append(f"--- {f.name}\n{f.read_text()}")
    return "\n".join(parts)


def _parse_datetime(value):
    if value is None:
        return None
    text = str(value)
    # Supporte à la fois ISO 8601 et le format SQLite YYYY-MM-DD HH:MM:SS...
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    return datetime.fromisoformat(text)


@click.command()
@click.option("--no-ia", is_flag=True, help="Sauter la validation IA.")
def submit(no_ia):
    """Valide la solution kubectl puis demande un score IA."""
    conn = db.get_db()
    session = db.get_active_session(conn)
    if not session:
        raise click.ClickException("Aucune session active. Lance `dojo start <kata>` d'abord.")

    kata = kata_loader.load_kata(session["kata_id"])
    started = _parse_datetime(session["started_at"])
    ended = datetime.now()
    duration = int((ended - started).total_seconds()) if started else 0

    checks = kata.get("validation", {}).get("checks", [])
    log = [f"🥋 Kata : {kata.get('title', session['kata_id'])}"]
    success = True

    for idx, check in enumerate(checks, 1):
        ok, output = k8s_client.exec_check(check)
        status = "✅" if ok else "❌"
        log.append(f"{status} [{idx}] {check.get('description', 'check')}")
        log.append(f"   command: {check.get('command')}")
        log.append(f"   output: {output}")
        if not ok:
            success = False

    ia_score = None
    if success and not no_ia:
        workspace = db.get_data_dir() / "workspace" / session["kata_id"]
        manifests = _read_manifests(workspace)
        prompt = llm_client.load_prompt(
            "system_validator",
            kata_title=kata.get("title", session["kata_id"]),
            manifests_content=manifests,
        )
        result = llm_client.call_deepseek(prompt)
        if result and "score" in result and "comment" in result:
            ia_score = int(result["score"])
            log.append(f"🤖 Score IA : {ia_score}/100")
            log.append(f"   Commentaire : {result['comment']}")
        else:
            log.append("⚠️  IA_OFFLINE : validation textuelle uniquement.")

    raw_log = "\n".join(log)
    db.update_session_end(conn, session["id"], duration, session["hint_level_reached"], success, raw_log, ia_score)

    if success:
        db.bump_total_katas(conn)
        db.add_competence_snapshot(conn, kata.get("category", "pods"))
        click.echo("🎉 Kata validé avec succès !")
        if ia_score is not None:
            click.echo(f"   Score IA : {ia_score}/100")
    else:
        click.echo("💥 Échec de la validation kubectl. Corrige et réessaie.")

    click.echo(raw_log)
