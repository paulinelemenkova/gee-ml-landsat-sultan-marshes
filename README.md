# Google Earth Engine + explainable ML for Landsat time-series analysis

A cloud-native remote-sensing pipeline that couples **Google Earth Engine (GEE)**
with **explainable machine learning**. It ingests the **complete Landsat
Collection 2 archive (1984–2025)**, masks/harmonises/composites every TM, ETM+
and OLI scene server-side, derives multi-index time series, and then applies
per-pixel **Theil–Sen / Mann–Kendall** trend statistics and
**Random Forest / gradient-boosting classifiers with SHAP** attribution.
The workflow is demonstrated on the Sultan Marshes (Develi Basin, Central
Anatolia, Türkiye) but is generic and transferable to any Landsat-monitored
site.

**Tech stack:** Google Earth Engine (JavaScript) · Python (rasterio, scikit-learn,
SHAP, Matplotlib) · GMT. **Methods:** archive-scale cloud compositing ·
non-parametric trend detection · index-threshold classification · ensemble ML ·
explainable AI (SHAP).

The pipeline has two stages:

1. **Cloud processing (Google Earth Engine).** The JavaScript scripts in
   [`gee/`](gee) filter, mask, harmonise and composite every Landsat TM/ETM+/OLI
   scene, compute the spectral indices, and export compact GeoTIFFs and tables.
2. **Local analysis & figures (Python + GMT).** The scripts in
   [`figures/`](figures) and [`model/`](model) read those exports and reproduce
   the trend maps, condition maps, land-cover maps, the classifier/attribution
   analysis and the drying-risk map.

## Repository layout

```
.
├── gee/       Google Earth Engine scripts (run in the GEE Code Editor)
├── figures/   Python + GMT scripts that build each figure
├── model/     Random Forest / gradient boosting + SHAP training
├── data/      inputs (downloaded from the archive) — see data/README.md
├── requirements.txt
└── LICENSE
```

## Google Earth Engine scripts (`gee/`)

| Script | Produces |
|---|---|
| `gee_trends.js` | Per-pixel Theil–Sen slope and Mann–Kendall significance for the spectral indices |
| `gee_landcover.js` | Growing-season land-cover composites for four epochs |
| `gee_condition.js` | Continuous Ecological Condition Index (ECI) per epoch |
| `gee_drivers.js` | 12-band predictor + label stack for the machine-learning step |
| `gee_water_check.js` | Independent surface-water cross-check (JRC Global Surface Water vs Landsat) |

Open each in the [Earth Engine Code Editor](https://code.earthengine.google.com/),
set the export folder if needed, and run the `Export` tasks. The exported files
go to the `data/` folder (see [`data/README.md`](data/README.md)).

## Local scripts (`figures/`, `model/`)

| Script | Output |
|---|---|
| `figure1_framework.py` | Conceptual framework diagram |
| `figure2_studyarea.sh` | Study-area relief map (GMT) |
| `figure3_workflow.py` | Processing-workflow diagram |
| `figure5_trends.py` | Trend maps of the spectral indicators |
| `figure6_condition.py` | Ecological-condition maps (4 epochs) |
| `figure7_landcover.py` | Land-cover evolution maps + composition chart |
| `figure8_model.py` | Classifier performance (confusion matrix + metrics) |
| `figure9_shap.py` | SHAP driver attribution |
| `figure10_dryingrisk.py` | Wetland drying-risk map |
| `model/train_condition_model.py` | Trains the models and writes the SHAP/metrics arrays |

## Requirements

- **Python ≥ 3.10** with the packages in [`requirements.txt`](requirements.txt):
  `numpy`, `rasterio`, `matplotlib`, `pyproj`, `scikit-learn`, `shap`.
- **[GMT ≥ 6](https://www.generic-mapping-tools.org/)** for the study-area map.
- A Google Earth Engine account for the `gee/` scripts.
- (Optional) the *Nimbus Sans* font for exact figure typography; the scripts
  fall back to the Matplotlib default if it is absent.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Reproduce

```bash
# 0. get the input rasters/tables (see data/README.md) into ./data

# 1. train the condition model -> writes the SHAP / metric arrays into ./data
python model/train_condition_model.py

# 2. build the figures (run from the repository root)
python figures/figure5_trends.py
python figures/figure6_condition.py
python figures/figure7_landcover.py
python figures/figure8_model.py
python figures/figure9_shap.py
python figures/figure10_dryingrisk.py
python figures/figure1_framework.py
python figures/figure3_workflow.py
bash   figures/figure2_studyarea.sh
```

Each script writes its `Figure_*.png` / `.pdf` to the current directory.

## Data availability

The Landsat archive and ancillary layers are open. Derived rasters and tables
are archived on Zenodo: **https://doi.org/10.5281/zenodo.XXXXXXX** *(replace with
your DOI)*.

## Citation

If you use this code, please cite the associated publication *(citation details
will be added here on publication)* and this repository.

## Authors

Polina Lemenkova and Abdullah Can Zülfikar.

## License

Released under the [MIT License](LICENSE).
