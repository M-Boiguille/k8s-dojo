"""`dojo test` command."""
import sys

import click

from cli.core import kata_loader, validator


@click.command()
@click.argument("kata_id", required=False)
@click.option("--all", "run_all", is_flag=True, help="Tester tous les katas.")
@click.option("--dry-run", is_flag=True, help="Exécuter les checks sans cluster.")
def test(kata_id, run_all, dry_run):
    """Valide le schéma des katas (et optionnellement en dry-run)."""
    if run_all:
        ids = kata_loader.list_katas()
    elif kata_id:
        ids = [kata_id]
    else:
        raise click.ClickException("Précise --all ou un kata_id.")

    if not ids:
        raise click.ClickException("Aucun kata trouvé dans katas-library/.")

    failed = False
    for kid in ids:
        try:
            kata = kata_loader.load_kata(kid)
        except FileNotFoundError as exc:
            click.echo(f"{kid}: ❌ {exc}")
            failed = True
            continue

        errors = validator.validate_kata_schema(kata)
        if errors:
            click.echo(f"{kid}: ❌ schema invalide")
            for err in errors:
                click.echo(f"   - {err}")
            failed = True
            continue

        if dry_run:
            validator.run_dry_run_checks(kata)
            click.echo(f"{kid}: ✅ schema OK (dry-run)")
        else:
            click.echo(f"{kid}: ✅ schema OK")

    if failed:
        sys.exit(1)
