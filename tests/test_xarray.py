from pathlib import Path

import pytest

from metamorph_mda_parser.nd import NdInfo
from metamorph_mda_parser.xarray import HAS_XARRAY


@pytest.fixture
def ndinfo():
    return NdInfo.from_path(Path("tests/resources/data/sample_3ch_2pos_mixed-z.nd"))


@pytest.mark.filterwarnings("ignore:Missing stk metadata")
def test_xarray(ndinfo):
    if HAS_XARRAY:
        array = ndinfo.get_data_array()
        assert array.dims == ("position", "time", "channel", "z", "y", "x")
    else:
        with pytest.raises(ValueError):
            ndinfo.get_data_array()
