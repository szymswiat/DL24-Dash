import typer
from typer.models import CommandInfo

from dl24_dash.apps.monitor import main as monitor
from dl24_dash.apps.plot import main as plot

app = typer.Typer()

app.registered_commands.append(
    CommandInfo(
        name="monitor",
        callback=monitor,
        help="A tool for real-time discharge monitoring",
    )
)

app.registered_commands.append(
    CommandInfo(
        name="plot",
        callback=plot,
        help="A tool for comparing previously collected results",
    )
)

if __name__ == "__main__":
    app()
