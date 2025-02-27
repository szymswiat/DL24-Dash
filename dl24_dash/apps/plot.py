from __future__ import annotations
import dash
import typer

from pathlib import Path
from typing_extensions import Annotated

from dl24_dash.dl24 import DL24DataStore
from dl24_dash.plotting.plotting import DischargePlotter


def main(
    data_dirs: Annotated[
        list[Path],
        typer.Argument(help="Data directories to scan"),
    ],
    save: Annotated[
        Path | None,
        typer.Option(help="Save plot to file"),
    ] = None,
    min_current: Annotated[
        float | None,
        typer.Option(help="Filter out all data rows with current below this value"),
    ] = None,
):
    files: list[Path] = []

    for data_dir in data_dirs:
        files.extend(sorted(data_dir.glob("**/*.csv")))

    store_list = [
        DL24DataStore(None, session_file.stem, session_file.parent)
        for session_file in files
    ]

    for store in store_list:
        store.restore_session()

        if min_current is not None:
            store.filter_by_current(min_current)
    for store in store_list:
        store.restore_session()

        if min_current is not None:
            store.filter_by_current(min_current)

    dash_app = dash.Dash()

    plotter = DischargePlotter(dash_app)
    plotter.add_data_stores(store_list)
    plotter.write_graph()

    if save:
        plotter.plot_data().write_html(
            f"{'__'.join(data_dir.as_posix().replace('/', '_') for data_dir in data_dirs)}/{save}"
        )
    else:
        dash_app.run(debug=False)
