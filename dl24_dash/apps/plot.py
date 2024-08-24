from __future__ import annotations
import dash
import typer

from pathlib import Path
from typing_extensions import Annotated

from dl24_dash import conf
from dl24_dash.dl24 import DL24DataStore
from dl24_dash.plotting.plotting import DischargePlotter


def main(
    session_names: Annotated[list[str], typer.Argument()],
    save: Annotated[Path | None, typer.Option()] = None,
    data_path: Annotated[Path, typer.Option()] = conf.DEFAULT_DATA_STORAGE_PATH,
    plot_all: Annotated[bool, typer.Option()] = False,
):
    if plot_all:
        session_names = sorted([p.stem for p in data_path.glob("*.csv")])

    handlers = [
        DL24DataStore(None, session_name, data_path) for session_name in session_names
    ]
    for handler in handlers:
        handler.restore_session()

    dash_app = dash.Dash()

    plotter = DischargePlotter(dash_app)
    plotter.add_data_stores(handlers)
    plotter.write_graph()

    if save:
        plotter.plot_data().write_html(f"{data_path}/{save}")
    else:
        dash_app.run(debug=False)
