"""`dojo build-dashboard` command."""
import json
import shutil
from datetime import datetime
from pathlib import Path

import click
import jinja2

from cli.core import db, kata_loader


@click.command("build-dashboard")
@click.option("--output", default="public", type=click.Path(), help="Dossier de sortie.")
def build_dashboard(output):
    """Génère le dashboard statique (index.html)."""
    conn = db.get_db()
    skill_rows = db.get_skill_snapshots(conn, tool="k8s")
    sessions = db.get_sessions(conn)
    pub_dir = db.get_data_dir() / "public" / "journal"
    journals = sorted(pub_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True) if pub_dir.exists() else []
    latest_journal = journals[0].name if journals else None

    latest = skill_rows[-1] if skill_rows else None

    def row_to_dict(row):
        return {k: row[k] for k in row.keys()} if row else {}

    sessions_data = [row_to_dict(s) for s in sessions]
    latest_data = {**json.loads(latest["scores"]), "date": latest["date"]} if latest else None
    if not latest_data:
        latest_data = {
            "pods": 0, "services": 0, "storage": 0, "networking": 0,
            "rbac": 0, "git": 0, "architecture": 0,
        }
    snapshots_data = [{"date": r["date"], **json.loads(r["scores"])} for r in skill_rows]
    success_count = sum(1 for s in sessions if s["success"])

    # Badges
    badges = []
    if latest_data:
        if latest_data["storage"] >= 80:
            badges.append("Storage Master")
        if latest_data["pods"] >= 80 and latest_data["services"] >= 80:
            badges.append("Cluster Builder")
    boss_win = False
    for s in sessions:
        if s["success"] and s["ia_score"] is not None and s["ia_score"] >= 90:
            try:
                kata = kata_loader.load_kata(s["kata_id"])
            except FileNotFoundError:
                kata = {}
            if kata.get("level") == "boss":
                boss_win = True
    if boss_win:
        badges.append("Boss Slayer")
    if latest_data and latest_data["git"] >= 50:
        badges.append("Git Apprentice")

    completed = [s for s in sessions if s["success"]]
    avg = 0
    if completed:
        avg = round(sum(s["duration_seconds"] or 0 for s in completed) / len(completed))

    template_dir = Path(__file__).resolve().parents[1] / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    template = env.get_template("dashboard.html")

    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    style_src = template_dir / "style.css"
    if style_src.exists():
        shutil.copy2(style_src, out / "assets" / "style.css")

    (out / "index.html").write_text(
        template.render(
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            latest=latest_data,
            snapshots=snapshots_data,
            sessions=sessions_data,
            success_count=success_count,
            badges=badges,
            average_time=avg,
            journal_count=len(journals),
            latest_journal=latest_journal,
        ),
        encoding="utf-8",
    )
    click.echo(f"📊 Dashboard généré : {out / 'index.html'}")
