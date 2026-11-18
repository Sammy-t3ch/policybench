"""PolicyBench command-line interface entry point."""

from typing import Annotated

import typer

from policybench import __version__

app = typer.Typer(
    name="policybench",
    help="CLI-first benchmark for measuring policy compliance in tool-using AI agents.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"policybench {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show PolicyBench version and exit.",
        ),
    ] = None,
) -> None:
    """PolicyBench CLI."""
