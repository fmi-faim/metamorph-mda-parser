from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal

from metamorph_mda_parser.lark import parse


class NdInfo(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_pascal,
        ),
    )

    path: Path
    name: str
    version: Literal["1.0", "2.0"]
    description: str
    do_timelapse: bool
    do_stage: bool
    do_wave: bool
    do_z_series: bool
    stage_positions: list[str] = []
    wave_names: list[str] = []
    wave_do_z: list[bool] = []
    n_stage_positions: int = 1
    n_time_points: int = 1
    n_z_steps: int = 1
    z_step_size: float | None = None
    wave_in_file_name: bool

    @staticmethod
    def from_path(path: Path):
        with open(path) as f:
            content = f.read()
        result = parse(content)
        result["Path"] = path
        result["Name"] = path.stem
        result["Version"] = "1.0"  # HACK
        return NdInfo(**result)

    def _wavelengths(self):
        for i, w in enumerate(self.wave_names):
            if self.do_wave:
                yield (
                    i,
                    w,
                    f"_w{i+1}{w}" if self.wave_in_file_name else "",
                    self.wave_do_z[i] if self.wave_do_z else False,
                )

    def _stage_positions(self):
        for s, s_name in enumerate(self.stage_positions):
            if self.do_stage:
                yield s, s_name, f"_s{s+1}"

    def _timepoints(self):
        if self.do_timelapse:
            for t in range(self.n_time_points):
                yield t, f"_t{t+1}"

    def _get_path_channel_position_time(self):
        for w_idx, w_name, w, has_z in list(self._wavelengths()) or [("", self.do_z)]:
            for s_idx, s_name, s in list(self._stage_positions()) or [(0, None, "")]:
                for t_idx, t in list(self._timepoints()) or [(0, "")]:
                    yield (
                        self.path.parent / (self.name + w + s + t + (".stk" if has_z else ".tif")),
                        w_idx,
                        w_name,
                        s_idx,
                        s_name,
                        t_idx,
                    )

    def get_files(self) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            self._get_path_channel_position_time(),
            columns=[
                "path",
                "channel",
                "channel_name",
                "position",
                "position_name",
                "time",
            ],
        )

    def get_data_array(self, channels=None, positions=None, timepoints=None):
        from metamorph_mda_parser.xarray import HAS_XARRAY
        if HAS_XARRAY:
            from metamorph_mda_parser.xarray import dataarray_from_dataframe
        else:
            raise ValueError("Dependencies for data array creation not found.")
        files = self.get_files()
        if channels:
            files = files[files["channel"].isin(channels)]
        if positions:
            files = files[files["position"].isin(positions)]
        if timepoints:
            files = files[files["time"].isin(timepoints)]
        return dataarray_from_dataframe(files, self.wave_do_z)
