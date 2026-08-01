CODE ATLAS for mwaskom/seaborn — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- PolyFit is not robust to missing data
    -> seaborn/_core/plot.py, seaborn/_stats/regression.py
- pairplot fails with hue_order not containing all hue values in seaborn 0.11.1
    -> seaborn/_oldcore.py
- pairplot raises KeyError with MultiIndex DataFrame
    -> seaborn/axisgrid.py
- Color mapping fails with boolean data
    -> seaborn/_core/scales.py
