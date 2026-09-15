from warnings import warn

import numpy as np
from pandas import DataFrame

try:
    import dask.array as da
    import xarray as xr
    from tifffile import TiffFile

    HAS_XARRAY = True
except ImportError:
    HAS_XARRAY = False


def dataarray_from_dataframe(df: "DataFrame", channels_3d: list[bool]):
    required_columns = ["path", "channel", "position", "time"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        msg = f"Missing columns: {missing_columns}"
        raise ValueError(msg)
    if len(channels_3d) > 0 and df["channel"].max() > len(channels_3d):
        msg = "No dimension information available for certain channels."
        raise ValueError(msg)
    data_arrays = [_load_file(row, channels_3d) for _, row in df.iterrows()]
    return xr.combine_by_coords(data_arrays)["intensity"]


def _load_file(row, channels_3d: list[bool]):
    path = row["path"]
    position = row["position"]
    time = row["time"]
    channel = row["channel"]

    chunks = (-1,) * (2 if len(channels_3d) == 0 or not channels_3d[channel] else 3)
    with TiffFile(path) as tif:
        store = tif.series[0].aszarr()
        data = da.from_zarr(store, chunks=chunks)
        metadata = tif.stk_metadata

    # Determine if the array is 2D or 3D
    if data.ndim == 2:
        data = data[None, ...]  # Add a dummy Z dimension

    if not metadata:
        msg = f"Missing stk metadata: {path}"
        warn(msg)
        x_calibration = 1.0
        y_calibration = 1.0
        z_distance = [1.0] * data.shape[0]
    else:
        x_calibration = metadata.get("XResolution", 1.0)
        y_calibration = metadata.get("YResolution", 1.0)
        z_distance = metadata.get("ZDistance", [1.0] * data.shape[0])

    data_array = xr.DataArray(
        data[
            None, None, None, ...
        ],  # Add singleton dimensions for position, time, and channel
        dims=["position", "time", "channel", "z", "y", "x"],
        coords={
            "position": [int(position)],
            "time": [int(time)],
            "channel": [int(channel)],
            "z": np.cumsum(z_distance),
            "y": np.arange(data.shape[1]) * y_calibration,
            "x": np.arange(data.shape[2]) * x_calibration,
        },
    )

    return xr.Dataset({"intensity": data_array})
