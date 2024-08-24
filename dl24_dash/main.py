import typer
from typer.models import CommandInfo

from dl24_dash.apps.monitor import main as monitor
from dl24_dash.apps.plot import main as plot

app = typer.Typer()

app.registered_commands.append(
    CommandInfo(
        name="monitor",
        callback=monitor,
    )
)

app.registered_commands.append(
    CommandInfo(
        name="plot",
        callback=plot,
    )
)

if __name__ == "__main__":
    app()
