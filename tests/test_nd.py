from pathlib import Path

import pytest

from metamorph_mda_parser.nd import NdInfo


@pytest.fixture
def sample_4ch_4pos():
    return Path("tests/resources/sample_4ch_4pos.nd")


@pytest.fixture
def sample_2ch_75pos_361t():
    return Path("tests/resources/sample_2ch_75pos_361t.nd")


def test_sample_4ch_4pos(sample_4ch_4pos):
    nd_info = NdInfo(sample_4ch_4pos)

    assert nd_info.version == "1.0"
    assert nd_info.description == "File recreated from images."
    assert not nd_info.do_timelapse
    assert nd_info.do_stage
    assert len(nd_info.stage_positions) == 4
    assert nd_info.do_wave
    assert len(nd_info.wave_names) == 4
    assert nd_info.do_z
    assert nd_info.n_z_steps == 42
    assert nd_info.z_step_size == 3.0
    assert nd_info.wave_in_file_name
    assert nd_info.wave_names == ["Conf640", "Conf561", "Conf488", "Conf405"]

    files = nd_info.get_files()

    assert len(files) == 16
    assert files["channel"].unique().tolist() == [0, 1, 2, 3]
    assert files["channel_name"].unique().tolist() == nd_info.wave_names
    assert files["position"].unique().tolist() == [0, 1, 2, 3]
    assert files["position_name"].unique().tolist() == [
        "Position1",
        "Position2",
        "Position3",
        "Position4",
    ]
    assert files["time"].unique().tolist() == [0]


def test_sample_2ch_75pos_361t(sample_2ch_75pos_361t):
    nd_info = NdInfo(sample_2ch_75pos_361t)

    assert nd_info.version == "1.0"
    assert nd_info.description == "File recreated from images."
    assert nd_info.do_timelapse
    assert nd_info.n_timepoints == 361
    assert nd_info.do_stage
    assert len(nd_info.stage_positions) == 75
    assert nd_info.do_wave
    assert len(nd_info.wave_names) == 2
    assert nd_info.do_z
    assert nd_info.n_z_steps == 25
    assert nd_info.z_step_size == 2.0
    assert nd_info.wave_in_file_name
    assert nd_info.wave_names == ["BF-488-Cam1", "488-BF-Cam0"]

    files = nd_info.get_files()

    assert len(files) == 54150
