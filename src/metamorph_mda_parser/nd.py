from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal

if TYPE_CHECKING:
    from pathlib import Path

import pandas as pd


class NdInfo:
    path: Path
    name: str
    version: Literal["1.0", "2.0"]
    description: str
    do_timelapse: bool
    do_stage: bool
    do_wave: bool
    do_z: bool
    stage_positions: list[str]
    wave_names: list[str]
    wave_do_z: list[bool]
    n_timepoints: int
    n_z_steps: int
    z_step_size: float
    wave_in_file_name: bool

    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self._parse_nd()

    def _parse_nd(self) -> None:
        with open(self.path) as nd:
            # Version
            self.version = self._parse_line(nd.readline(), "NDInfoFile", self._extract_version)
            self.description = self._parse_line(nd.readline(), "Description", str)
            self.start_time = self._parse_line(nd.readline(), "StartTime1", str)
            # Time lapse
            self.do_timelapse = self._parse_line(nd.readline(), "DoTimelapse", self._parse_bool)
            if self.do_timelapse:
                self.n_timepoints = self._parse_line(nd.readline(), "NTimePoints", int)

            # Stage positions
            self.do_stage = self._parse_line(nd.readline(), "DoStage", self._parse_bool)
            if self.do_stage:
                n_stage_positions = self._parse_line(nd.readline(), "NStagePositions", int)
                self.stage_positions = []
                for s in range(n_stage_positions):
                    self.stage_positions.append(self._parse_line(nd.readline(), f"Stage{s+1}", str))

            # Wavelengths
            self.do_wave = self._parse_line(nd.readline(), "DoWave", self._parse_bool)
            if self.do_wave:
                n_wavelengths = self._parse_line(nd.readline(), "NWavelengths", int)
                self.wave_names = []
                self.wave_do_z = []
                for w in range(n_wavelengths):
                    self.wave_names.append(self._parse_line(nd.readline(), f"WaveName{w+1}", str))
                    self.wave_do_z.append(self._parse_line(nd.readline(), f"WaveDoZ{w+1}", self._parse_bool))

            # Z steps
            self.do_z = self._parse_line(nd.readline(), "DoZSeries", self._parse_bool)
            self.n_z_steps = self._parse_line(nd.readline(), "NZSteps", int)
            self.z_step_size = self._parse_line(nd.readline(), "ZStepSize", float)

            self.wave_in_file_name = self._parse_line(nd.readline(), "WaveInFileName", self._parse_bool)

            # End of file
            last_line = nd.readline()
            if last_line.strip(' "\n') != "EndFile":
                message = f"Expected end of file, got: {last_line}"
                raise ValueError(message)

    def _parse_line(self, line: str, key: str, value_function: Callable):
        tokens = line.split(",")
        if tokens[0].strip(' "') != key:
            message = f"Invalid nd file contents.\n\texpected: {key}\n\tgot: {line}"
            raise ValueError(message)
        return value_function(tokens[1].strip(' "\n'))

    def _extract_version(self, value: str) -> str:
        return value[8:]

    def _parse_bool(self, value: str) -> bool:
        return value.lower() == "true"

    def _wavelengths(self):
        for i, w in enumerate(self.wave_names):
            if self.do_wave:
                yield (
                    i,
                    w,
                    f"_w{i+1}{w}" if self.wave_in_file_name else "",
                    self.wave_do_z[i],
                )

    def _stage_positions(self):
        for s, s_name in enumerate(self.stage_positions):
            if self.do_stage:
                yield s, s_name, f"_s{s+1}"

    def _timepoints(self):
        if self.do_timelapse:
            for t in range(self.n_timepoints):
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
