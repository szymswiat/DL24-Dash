from __future__ import annotations
import plotly.graph_objects as go
import numpy as np

from dash.dependencies import Input, Output

import dash
from dash import dcc, html

from dl24_dash.dl24 import DL24DataStore


class DischargePlotter:
    def __init__(
        self,
        dash_app: dash.Dash,
    ) -> None:
        self.dash_app = dash_app

        self.data_stores: list[DL24DataStore] = []

    def add_data_stores(self, data_stores: list[DL24DataStore]):
        self.data_stores.extend(data_stores)

    def write_graph(self):
        self.dash_app.layout = html.Div(
            dcc.Graph(figure=self.plot_data()),
        )

    def bind_and_auto_update(self):
        self.dash_app.layout = html.Div(
            [
                dcc.Graph(id="graph"),
                dcc.Interval(id="graph-update", interval=5 * 1000),
            ]
        )

        @self.dash_app.callback(
            Output("graph", "figure"), [Input("graph-update", "n_intervals")]
        )
        def update_figure(n: int):
            return self.plot_data()

    def plot_data(self) -> go.Figure:
        fig = go.Figure()

        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Courier"
            )
        )

        for data_store in self.data_stores:
            if data_store.df is None:
                continue

            fig.add_traces(
                go.Scatter(
                    x=data_store.df["capacity"],
                    y=data_store.df["voltage"],
                    customdata=np.stack(
                        (
                            data_store.df["current"],
                            data_store.df["time_sec"],
                            data_store.df["time_str"],
                        ),
                        axis=-1,
                    ),
                    name=data_store.session_name,
                    mode='lines',
                    line={ 'width': 1.2 },
                )
            )

        fig.update_traces(mode="lines", hovertemplate=None)
        fig.update_layout(hovermode="closest", height=1000)

        fig.update_traces(
            hovertemplate="<br>" + "<br>".join(
                [
                    "capacity  | %{x}",
                    "voltage   | %{y}",
                    "current   | %{customdata[0]}",
                    "time sec  | %{customdata[1]}",
                    "time      | %{customdata[2]}",
                ]
            )
        )

        fig.update_xaxes(autorange=True)

        return fig
