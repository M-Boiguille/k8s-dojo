"""K8s Dojo CLI entrypoint."""
import click

from cli.commands import (
    dashboard,
    hint,
    init,
    journal,
    publish,
    start,
    submit,
    test,
)


@click.group()
@click.version_option(version="0.1.0", prog_name="dojo")
def cli():
    """K8s Dojo – moteur d'apprentissage adaptatif Kubernetes/DevOps."""


cli.add_command(init.init, name="init")
cli.add_command(start.start, name="start")
cli.add_command(hint.hint, name="hint")
cli.add_command(submit.submit, name="submit")
cli.add_command(journal.journal, name="journal")
cli.add_command(publish.publish, name="publish")
cli.add_command(dashboard.build_dashboard, name="build-dashboard")
cli.add_command(test.test, name="test")


def main():
    cli()


if __name__ == "__main__":
    main()
