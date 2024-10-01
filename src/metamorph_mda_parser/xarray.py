try:
    import dask.array as da
    import xarray as xr
    from tifffile.tifffile import imread
    from pandas import DataFrame
    HAS_XARRAY = True
except ImportError:
    HAS_XARRAY = False


def dataarray_from_dataframe(df: "DataFrame", channels_3d: list[bool]):
    required_columns = ["path", "channel", "position", "time"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        msg = f"Missing columns: {missing_columns}"
        raise ValueError(msg)
    if df["channel"].max() > len(channels_3d):
        msg = f"No dimension information available for certain channels."
        raise ValueError(msg)
    data_arrays = [_load_file(row, channels_3d) for _, row in df.iterrows()]
    return xr.combine_by_coords(data_arrays)["intensity"]


def _load_file(row, channels_3d: list[bool]):
    path = row['path']
    position = row['position']
    time = row['time']
    channel = row['channel']
    
    chunks = (-1,) * (3 if channels_3d[channel] else 2)
    with imread(path, aszarr=True) as store:
        data = da.from_zarr(store, chunks=chunks)
    
    # Determine if the array is 2D or 3D
    if data.ndim == 2:
        data = data[None, ...]  # Add a dummy Z dimension
    
    data_array = xr.DataArray(
        data[None, None, None, ...],  # Add singleton dimensions for position, time, and channel
        dims=['position', 'time', 'channel', 'z', 'y', 'x'],
        coords={
            'position': [int(position)],
            'time': [int(time)],
            'channel': [int(channel)],
            'z': range(data.shape[0]),
            'y': range(data.shape[1]),
            'x': range(data.shape[2])
        }
    )

    return xr.Dataset({'intensity': data_array})
