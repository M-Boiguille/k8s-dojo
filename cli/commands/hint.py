"""`dojo hint` command."""
import click

from cli.core import db, kata_loader, llm_client


@click.command()
def hint():
    """Demande un indice socratique (4 niveaux)."""
    conn = db.get_db()
    session = db.get_active_session(conn) or db.get_last_session(conn)
    if not session:
        raise click.ClickException("Aucune session active. Lance `dojo start <kata>` d'abord.")

    kata = kata_loader.load_kata(session["kata_id"])
    next_level = min(4, session["hint_level_reached"] + 1)

    prompt = llm_client.load_prompt(
        "system_tutor",
        kata_title=kata.get("title", session["kata_id"]),
        category=kata.get("category", "pods"),
        hint_level=next_level,
    )
    result = llm_client.call_deepseek(prompt)

    if result and "question" in result:
        question = result["question"]
    else:
        # Fallback : utiliser l'indice défini dans le kata
        local = next((h for h in kata.get("hints", []) if h.get("level") == next_level), {})
        question = local.get("question") or local.get("explanation") or "Continue ton investigation Kubernetes."
        if result and "_error" in result:
            click.echo("⚠️  IA offline – indice local utilisé.")

    db.update_hint_level(conn, session["id"], next_level)
    db.bump_total_hints(conn)

    click.echo(f"💡 Indice niveau {next_level}/4 : {question}")
