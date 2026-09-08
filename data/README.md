# Data

The scripts read their inputs from this folder. The raster/tabular inputs are
**not stored in the repository** (they are large); they are produced by the
Google Earth Engine scripts in [`../gee`](../gee) and archived on Zenodo.

> **Archive:** https://doi.org/10.5281/zenodo.XXXXXXX  *(replace with your DOI)*

Download the archive and unzip it here so the folder looks like:

```
data/
├── sultan_trends_fig5_60m.tif        # 15-band per-pixel trend raster   (from gee_trends.js)
├── sultan_ECI_4epochs.tif            # 4-band Ecological Condition Index (from gee_condition.js)
├── sultan_landcover_4epochs/         # tiled 4-epoch land-cover raster   (from gee_landcover.js)
│   └── sultan_landcover_4epochs-*.tif
├── sultan_driver_stack.tif           # 12-band predictors + ECI target   (from gee_drivers.js)
├── sultan_condition_areas.csv        # per-class condition areas
└── sultan_water_areas.csv            # JRC vs Landsat water cross-check   (from gee_water_check.js)
```

The model intermediates consumed by `figure8_model.py` and `figure9_shap.py`
(`confusion.npy`, `clf_meta.json`, `shap_values.npy`, `shap_X.npy`,
`shap_meta.json`) are **generated locally** by
[`../model/train_condition_model.py`](../model/train_condition_model.py) from
`sultan_driver_stack.tif` — you do not need to download them.

| Band order in `sultan_driver_stack.tif` | |
|---|---|
| 1–5 | precipitation, PET, water deficit, soil moisture, max temperature (TerraClimate) |
| 6 | elevation (SRTM) |
| 7–11 | NDVI, NDWI, MNDWI, NDMI, BSI |
| 12 | Ecological Condition Index (regression/classification target) |
