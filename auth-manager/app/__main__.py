"""CLI entry point for the Auth Manager Service."""

import click
import uvicorn


@click.group()
def main() -> None:
    """Main CLI group."""


@main.command()
@click.option(
    "--host",
    default="0.0.0.0",
    envvar="HOST",
    help="Host to bind the server to",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    envvar="PORT",
    type=int,
    help="Port to bind the server to",
    show_default=True,
)
@click.option(
    "--workers",
    default=1,
    envvar="WORKERS",
    type=int,
    help="Number of worker processes",
    show_default=True,
)
@click.option(
    "--reload",
    default=False,
    envvar="RELOAD",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--log-level",
    default="info",
    envvar="UVICORN_LOG_LEVEL",
    type=click.Choice(["critical", "error", "warning", "info", "debug", "trace"]),
    help="Uvicorn log level",
    show_default=True,
)
def entrypoint(host: str, port: int, workers: int, reload: bool, log_level: str):
    """Start the Auth Manager Service using Uvicorn."""
    click.echo(f"Starting Auth Manager Service on {host}:{port}")
    click.echo(f"Workers: {workers}, Reload: {reload}, Log Level: {log_level}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level=log_level,
        access_log=True,
        proxy_headers=True,
    )


main()
