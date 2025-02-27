from __future__ import annotations
from pathlib import Path
from threading import Thread
from functools import partial
from dl24_dash import conf
from dl24_dash.dl24 import DL24, DL24DataStore
from typing_extensions import Annotated
from dl24_dash.plotting import DischargePlotter

import dash
import typer
import asyncio


def main(
    session_name: Annotated[str, typer.Argument(help="Session name")],
    port: Annotated[
        str,
        typer.Option(help="Path to bluetooth serial port device"),
    ] = conf.DEFAULT_SERIAL_PORT,
    data_path: Annotated[
        Path,
        typer.Option(help="Path to store data"),
    ] = conf.DEFAULT_DATA_STORAGE_PATH,
    start_new_session: Annotated[
        bool,
        typer.Option(help="Start new session or append to existing one"),
    ] = False,
    current: Annotated[
        float | None,
        typer.Option(help="Current to set at the beginning of the session"),
    ] = None,
):
    if data_path.exists() is False:
        data_path.mkdir()

    try:
        dl24 = DL24(port)
        data_store = DL24DataStore(dl24, session_name, data_path)

        if start_new_session and data_store.session_exists():
            raise Exception(
                "Session already exists. Cannot start a new session with the same name."
            )

        data_store.restore_session()

        dash_app = dash.Dash()
        plotter = DischargePlotter(dash_app)
        plotter.add_data_stores([data_store])

        plotter.bind_and_auto_update()

        if current:
            dl24.set_current(current)

        if start_new_session:
            dl24.reset_counters()

            data_store.update()  # log initial voltage
            dl24.enable()

        # run all async stuff in another thread
        th = Thread(target=partial(async_main_wrapper, data_store))

        th.start()

        dash_app.run(debug=False)

        th.join()

    finally:
        if dl24:
            dl24.disable()
            dl24.close()
        if data_store:
            data_store.write_csv()


async def async_main(data_store: DL24DataStore) -> None:
    update_task = asyncio.create_task(data_store.update_loop())
    write_csv_task = asyncio.create_task(data_store.write_csv_loop())

    await asyncio.gather(update_task, write_csv_task)


def async_main_wrapper(data_store: DL24DataStore) -> None:
    asyncio.run(async_main(data_store))
