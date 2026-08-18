CODE ATLAS for pydata/xarray — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- to_unstacked_dataset broken for single-dim variables
    -> xarray/core/dataarray.py
- Trailing whitespace in DatasetGroupBy text representation
    -> xarray/core/groupby.py
- Ignore missing variables when concatenating datasets?
    -> xarray/core/concat.py
