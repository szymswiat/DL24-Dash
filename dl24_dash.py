from pathlib import Path
from threading import Thread
from functools import partial
from typing import cast
import plotly.express as px
import plotly.graph_objs as go
from dl24 import DL24, DL24SerialError
import polars as pl
from dash.dependencies import Input, Output
from typing_extensions import Annotated

import dash
import typer
import datetime
import asyncio
from dash import dcc, html


from pydantic import BaseModel


class DL24Data(BaseModel):
    date: str
    voltage: float
    current: float
    power: float
    energy: float
    capacity: float
    temperature: float
    time_sec: int
    time_str: str

    # add as_df_row method that will return a dictionary with each field as a key and [value]
    def as_df_row(self) -> dict[str, list[float | int | str]]:
        return {k: [v] for k, v in self.model_dump().items()}


class DL24DataHandler:
    def __init__(self, dl24: DL24 | None, session_name: str, log_path: str) -> None:
        self.all_df: pl.DataFrame | None = None

        self._dl24 = dl24
        self.session_name = session_name
        self.log_path = log_path

    def read_dl24_data(self) -> DL24Data:
        assert self._dl24

        dl24 = self._dl24
        dl24.wait_for_broadcast()
        voltage = dl24.get_voltage()
        current = dl24.get_current()
        temp = dl24.get_temp()
        energy = dl24.get_energy()
        capacity = dl24.get_capacity() * 1000
        on_time = dl24.get_time()

        days = on_time.days
        seconds = on_time.seconds
        hours = seconds // 3600
        minutes = (seconds // 60) % 60
        seconds = seconds % 60

        time_sec = int(on_time.total_seconds())
        time_str = f"{days:01d}d {hours:02d}:{minutes:02d}:{seconds:02d}"

        return DL24Data(
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            voltage=voltage,
            current=current,
            power=voltage * current,
            energy=energy,
            capacity=capacity,
            temperature=temp,
            time_sec=time_sec,
            time_str=time_str,
        )

    def update(self):
        try:
            data = self.read_dl24_data()
        except DL24SerialError:
            print("Failed to read data from DL24")
            return

        # if cast(float, data['current']) < 0.001:
        #     return

        if self.all_df is None:
            self.all_df = pl.from_dict(data.as_df_row())
        else:
            if (
                abs(DL24Data.model_validate(self.all_df[-1]).voltage - data.voltage)
                > 0.02
            ) or data.current > 0.001:
                self.all_df = pl.concat([self.all_df, pl.from_dict(data.as_df_row())])

    async def update_loop(self):
        while True:
            self.update()
            await asyncio.sleep(0.2)

    def write_csv(self):
        if self.all_df is None:
            return

        self.all_df.write_csv(f"{self.log_path}/{self.session_name}.csv")

    async def write_csv_loop(self):
        while True:
            self.write_csv()
            await asyncio.sleep(5)

    def restore_session(self):
        if Path(f"{self.log_path}/{self.session_name}.csv").is_file():
            self.all_df = pl.read_csv(f"{self.log_path}/{self.session_name}.csv")


class DL24DashApp:
    def __init__(self, data_handler: DL24DataHandler, dl24: DL24 | None) -> None:
        self.data_handler = data_handler
        self.dl24 = dl24

        self.app = dash.Dash()

    def init_app(self):
        self.app.layout = html.Div(
            [
                dcc.Graph(id="graph"),
                dcc.Interval(id="graph-update", interval=5 * 1000),
            ]
        )
        self._register_callbacks()

    def run(self):
        self.app.run(debug=False)

    def _register_callbacks(self):
        @self.app.callback(
            Output("graph", "figure"), [Input("graph-update", "n_intervals")]
        )
        def update_figure(n: int):
            return self.create_fig()

    def create_fig(self) -> go.Figure:
        fig = px.line(
            self.data_handler.all_df,
            "capacity",
            "voltage",
            custom_data=["current", "time_sec", "time_str"],
        )

        fig.update_traces(mode="lines", hovertemplate=None)
        fig.update_layout(hovermode="x unified")

        fig.update_traces(
            hovertemplate="<br>".join(
                [
                    "capacity: %{x}",
                    "voltage: %{y}",
                    "current: %{customdata[0]}",
                    "time sec: %{customdata[1]}",
                    "time: %{customdata[2]}",
                ]
            )
        )

        fig.update_xaxes(autorange=True)

        return fig


async def async_main(data_handler: DL24DataHandler) -> None:
    update_task = asyncio.create_task(data_handler.update_loop())
    write_csv_task = asyncio.create_task(data_handler.write_csv_loop())

    await asyncio.gather(update_task, write_csv_task)


def async_main_wrapper(data_handler: DL24DataHandler) -> None:
    asyncio.run(async_main(data_handler))


def main(
    session_name: str,
    just_plot: Annotated[bool, typer.Option()] = False,
    save_html: Annotated[bool, typer.Option()] = False,
    port: Annotated[str, typer.Option()] = "/dev/rfcomm0",
    log_path: Annotated[str, typer.Option()] = "./cell_tests",
):
    data_handler: DL24DataHandler | None = None
    dl24: DL24 | None = None

    try:
        if just_plot or save_html:
            data_handler = DL24DataHandler(None, session_name, log_path)
            data_handler.restore_session()

            dash_app = DL24DashApp(data_handler, None)

            if just_plot:
                dash_app.init_app()
                dash_app.run()
            if save_html:
                dash_app.create_fig().write_html(f"{log_path}/{session_name}.html")

        else:
            dl24 = DL24(port)
            data_handler = DL24DataHandler(dl24, session_name, log_path)
            data_handler.restore_session()

            dash_app = DL24DashApp(data_handler, dl24)

            async_main_wrapper_partial = partial(async_main_wrapper, data_handler)

            # run all async stuff in another thread
            th = Thread(target=async_main_wrapper_partial)

            th.start()

            dash_app.init_app()
            dash_app.run()

            th.join()

    finally:
        if dl24:
            dl24.disable()
            dl24.close()
        if data_handler:
            data_handler.write_csv()


if __name__ == "__main__":
    typer.run(main)
