#!/usr/bin/env python3
"""
Train the ecological-condition model and export the intermediate arrays that
the figure scripts consume.

Input  : data/sultan_driver_stack.tif   (12 bands: 11 predictors + ECI target)
           pr, pet, def, soil, tmmx, elevation, NDVI, NDWI, MNDWI, NDMI, BSI, ECI
Outputs: data/confusion.npy   data/clf_meta.json      (feed figure8_model.py)
         data/shap_values.npy data/shap_X.npy data/shap_meta.json (feed figure9_shap.py)

Two models are fitted on the wetland pixels:
  1. Classification of the five ecological-condition classes (Random Forest and
     gradient boosting) with a 70/30 stratified split -> accuracy metrics.
  2. Regression of the continuous condition index with a Random Forest, then
     SHapley Additive exPlanations for the driver attribution.

Run from the repository root:  python model/train_condition_model.py
"""
import json
import numpy as np
import rasterio
from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor,
                              HistGradientBoostingClassifier)
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, cohen_kappa_score, roc_auc_score,
                             confusion_matrix)

SRC   = "data/sultan_driver_stack.tif"
SEED  = 42
BREAKS = [0.30, 0.40, 0.50, 0.60]          # 5 condition classes from the index
FEATS = ["Precipitation", "PET", "Water deficit", "Soil moisture",
         "Max temperature", "Elevation", "NDVI", "NDWI", "MNDWI", "NDMI", "BSI"]

# ---- read the driver stack ------------------------------------------------
with rasterio.open(SRC) as ds:
    A = ds.read().astype("float32")        # (12, H, W): 11 predictors + ECI
X = A[:11].reshape(11, -1).T               # (n_pixels, 11)
eci = A[11].reshape(-1)                     # continuous condition index
ok = np.isfinite(X).all(1) & np.isfinite(eci)
X, eci = X[ok], eci[ok]
y = np.digitize(eci, BREAKS)               # ordinal classes 0..4

rng = np.random.default_rng(SEED)
# ---- 1. classification: RF vs gradient boosting ---------------------------
n = min(40000, X.shape[0])
idx = rng.choice(X.shape[0], n, replace=False)
Xc, yc = X[idx], y[idx]
Xtr, Xte, ytr, yte = train_test_split(Xc, yc, test_size=0.30,
                                      stratify=yc, random_state=SEED)

def metrics(model, proba=True):
    model.fit(Xtr, ytr)
    p = model.predict(Xte)
    row = [accuracy_score(yte, p),
           precision_score(yte, p, average="macro", zero_division=0),
           recall_score(yte, p, average="macro", zero_division=0),
           f1_score(yte, p, average="macro", zero_division=0),
           cohen_kappa_score(yte, p)]
    if proba:
        pr = model.predict_proba(Xte)
        row.append(roc_auc_score(yte, pr, multi_class="ovr", average="macro"))
    return [round(float(v), 3) for v in row], p

rf = RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=SEED)
gb = HistGradientBoostingClassifier(max_iter=300, random_state=SEED)
rf_row, rf_pred = metrics(rf)
gb_row, _       = metrics(gb)

json.dump({"Random Forest": rf_row, "Gradient Boosting": gb_row},
          open("data/clf_meta.json", "w"), indent=2)
np.save("data/confusion.npy", confusion_matrix(yte, rf_pred))
print("Random Forest      [OA,P,R,F1,kappa,AUC] =", rf_row)
print("Gradient Boosting  [OA,P,R,F1,kappa,AUC] =", gb_row)

# ---- 2. regression + SHAP attribution -------------------------------------
try:
    import shap
except ImportError:
    raise SystemExit("Install shap to compute the attribution:  pip install shap")

reg = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=SEED)
Xtr_r, Xte_r, etr, ete = train_test_split(Xc, eci[idx], test_size=0.30,
                                          random_state=SEED)
reg.fit(Xtr_r, etr)
r2 = round(float(reg.score(Xte_r, ete)), 3)
print("Condition regressor R2 =", r2)

m = min(2000, Xte_r.shape[0])
Xs = Xte_r[rng.choice(Xte_r.shape[0], m, replace=False)]
sv = shap.TreeExplainer(reg).shap_values(Xs)

imp = np.abs(sv).mean(0)
order = list(np.argsort(imp)[::-1])
tbl = [[FEATS[i], round(float(imp[i]), 4),
        round(float(100 * imp[i] / imp.sum()), 1)] for i in order]
np.save("data/shap_values.npy", sv)
np.save("data/shap_X.npy", Xs)
json.dump({"feat": FEATS, "order": order, "tbl5": tbl, "R2": r2},
          open("data/shap_meta.json", "w"))
print("wrote data/confusion.npy, clf_meta.json, shap_values.npy, shap_X.npy, shap_meta.json")
