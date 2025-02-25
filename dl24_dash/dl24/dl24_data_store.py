from __future__ import annotations
from pathlib import Path
from dl24_dash.dl24 import DL24, DL24SerialError
import polars as pl

import datetime
import asyncio


from pydantic import BaseModel

from dl24_dash.dl24.dl24 import DL24Error, DL24NoResponseError


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

    @classmethod
    def from_row(cls, df: pl.DataFrame) -> DL24Data:
        assert len(df) == 1

        return DL24Data.model_validate(df.to_dicts()[0])


class DL24DataStore:
    def __init__(self, dl24: DL24 | None, session_name: str, data_path: Path) -> None:
        self.df: pl.DataFrame | None = None

        self._dl24 = dl24
        self.session_name = session_name
        self.data_path = data_path

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
        except (DL24SerialError, DL24NoResponseError, DL24Error) as e:
            print(f"Failed to read data from DL24: {e.args[0]}")
            return

        if self.df is None:
            self.df = pl.from_dict(data.as_df_row())
        else:
            assert self._dl24
            if data.voltage < self._dl24.get_voltage_cutoff():
                return
            if (
                abs(DL24Data.from_row(self.df[-1]).voltage - data.voltage) > 0.02
            ) or data.current > 0.001:
                self.df = pl.concat([self.df, pl.from_dict(data.as_df_row())])

    async def update_loop(self):
        while True:
            self.update()
            await asyncio.sleep(0.2)

    def write_csv(self):
        if self.df is None:
            return

        self.df.write_csv(self.data_path / f"{self.session_name}.csv")

    async def write_csv_loop(self):
        while True:
            self.write_csv()
            await asyncio.sleep(5)

    def session_exists(self) -> bool:
        return (self.data_path / f"{self.session_name}.csv").is_file()

    def restore_session(self):
        if self.session_exists():
            self.df = pl.read_csv(self.data_path / f"{self.session_name}.csv")

    def filter_by_current(self, min_current: float):
        self.df = self.df.filter(pl.col("current") > min_current)