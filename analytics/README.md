# Analytics Pipeline

Titanic dataset, loaded once (`01_eda.py`), profiled/cleaned/EDA'd, saved to `titanic.csv`,
then `02_modeling.py` continues from that same CSV into a full classification + regression
modeling pipeline. Full stdout in `eda_output.txt` / `modeling_output.txt`.

## Run — local

```bash
pip install -r requirements.txt
python 01_eda.py
python 02_modeling.py
```

## Run — Google Colab

```python
!git clone <your-repo-url>
%cd zepto-data-ai-platform/analytics
!python 01_eda.py
!python 02_modeling.py
```
Both scripts auto-install their requirements on Colab. `sns.load_dataset` needs internet
the first time only (Colab always has it); `titanic.csv` is the offline fallback either way.

## Part A — key findings

| Column | % missing | Strategy |
|---|---|---|
| `deck` | 77.2% | own `"Missing"` category (too high to impute; excluded from modeling features) |
| `age` | 19.9% | median-impute (5–30% bracket; median chosen since age is right-skewed) |
| `embarked`/`embark_town` | 0.2% | drop those rows (<5% bracket) |

IQR outliers: age 65, fare 114. `fare` mean(32.10) > median(14.45) > mode(8.05) →
right-skewed. Survival: female 74.0% vs male 18.9%; class 1→62.6%, 2→47.3%, 3→24.2%.
Strongest correlations: `pclass`↔`fare` (r=-0.548), `sibsp`↔`parch` (r=0.415). 4
multivariate charts (`charts/03-06`) build the story: sex dominates, class/fare compound
it, moderate family size is protective. Standardization sanity check confirms mean≈0,
std=1 after z-scoring (EDA-only — the model pipeline fits its own scaler on train only).

## Part B — model comparison

| Model | Accuracy | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.809 | 0.783 | 0.691 | 0.734 | **0.861** |
| Decision Tree | 0.764 | 0.760 | 0.559 | 0.644 | 0.837 |
| Random Forest (tuned) | **0.815** | **0.818** | 0.662 | 0.748 | 0.840 |

Split is **stratified** (61.8%/38.2% imbalance). Preprocessing (imputer/scaler/encoder) is
fit on the training split only via a `ColumnTransformer`+`Pipeline`. Imbalance comparison
(baseline / `class_weight='balanced'` / SMOTE-on-train-only) all land within 0.001 F1 —
SMOTE edges out slightly (0.735) with the most balanced precision/recall. `GridSearchCV`
best RF params: `n_estimators=100, max_depth=4, max_features='sqrt'`; **OOB score 0.8214**.

**Regression (predict fare):** MAE=21.10, RMSE=41.70, R²=0.348, Adj R²=0.321. Residual std
roughly 4.3x larger in the high-predicted-fare half → **heteroscedastic**.

**Recommendation: Logistic Regression.** Highest AUC (0.861, best ranking across
thresholds) and F1 within 0.014 of the tuned Random Forest, at a fraction of the
complexity — cheaper to retrain/serve, more interpretable, and recall (0.691, fewer missed
survivors) matters more than Random Forest's slight precision edge for this kind of
"who needs priority" use case. Saved to `models/best_pipeline.joblib`; reload-and-predict
on raw test rows confirmed identical output to the in-memory pipeline.

## Files

`01_eda.py` (Part A) · `02_modeling.py` (Part B) · `titanic.csv` (committed offline
fallback, cleaned version) · `charts/01-09*.png` · `models/best_pipeline.joblib`
