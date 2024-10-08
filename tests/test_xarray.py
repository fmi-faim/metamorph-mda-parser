import pytest
from pathlib import Path

from metamorph_mda_parser.nd import NdInfo

pytest.importorskip("xarray")

@pytest.fixture
def sample_3ch_2pos_mixed_z():
    return Path("tests/resources/data/sample_3ch_2pos_mixed-z.nd")

def test_data_array_from_nd(sample_3ch_2pos_mixed_z):
    ndinfo = NdInfo.from_path(sample_3ch_2pos_mixed_z)
    dataarray2d = ndinfo.get_data_array(channels=[0])
    dataarray3d = ndinfo.get_data_array(channels=[1, 2])

    assert dataarray2d.dims == ("position", "time", "channel", "z", "y", "x")
    assert dataarray2d[0, 0, 0, 0, :, :].data.compute().tolist() == [[0,0], [0,128], [0,0]]
    assert dataarray2d[1, 0, 0, 0, :, :].data.compute().tolist() == [[0,1], [0,128], [0,0]]

    assert dataarray3d.dims == ("position", "time", "channel", "z", "y", "x")
    assert dataarray3d[0, 0, 0, 0, :, :].data.compute().tolist() == [[1,0], [0,128], [0,0]]
    assert dataarray3d[0, 0, 1, 0, :, :].data.compute().tolist() == [[2,0], [0,128], [0,0]]
    assert dataarray3d[1, 0, 0, 0, :, :].data.compute().tolist() == [[1,1], [0,128], [0,0]]
    assert dataarray3d[1, 0, 1, 0, :, :].data.compute().tolist() == [[2,1], [0,128], [0,0]]
