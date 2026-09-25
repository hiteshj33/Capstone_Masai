"""Part B: modeling, continuing from the same cleaned titanic.csv (no reload).
Run: python 02_modeling.py
"""
import sys, subprocess, pathlib, warnings
warnings.filterwarnings("ignore")
if "google.colab" in sys.modules:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                     str(pathlib.Path(__file__).parent / "requirements.txt")])

import joblib, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                              confusion_matrix, roc_curve, roc_auc_score,
                              mean_absolute_error, mean_squared_error, r2_score)
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

pathlib.Path("charts").mkdir(exist_ok=True)
pathlib.Path("models").mkdir(exist_ok=True)

df = pd.read_csv("titanic.csv")
NUM, CAT = ["age", "fare", "sibsp", "parch", "pclass"], ["sex", "embarked"]
X, y = df[NUM + CAT], df["survived"]

# --- 7. Stratified split (imbalanced classes: 61.8%/38.2%) ---
print("Class balance:\n", y.value_counts(normalize=True).round(3))
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, random_state=42, stratify=y)
print("Stratified because the target is imbalanced; a plain random split could "
      "over/under-represent survivors in the test set.")

# --- 8. Preprocessing pipeline (fit on train only) ---
pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), NUM),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("oh", OneHotEncoder(handle_unknown="ignore"))]), CAT),
])

# --- 9-10. Train + evaluate 3 classifiers ---
models = {"Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
          "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42),
          "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42)}
fitted, rows = {}, []
plt.figure(figsize=(6, 5))
for name, clf in models.items():
    pipe = Pipeline([("pre", pre), ("model", clf)]).fit(Xtr, ytr)
    fitted[name] = pipe
    pred, proba = pipe.predict(Xte), pipe.predict_proba(Xte)[:, 1]
    print(f"\n{name} confusion matrix:\n{confusion_matrix(yte, pred)}")
    fpr, tpr, _ = roc_curve(yte, proba)
    plt.plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(yte, proba):.3f})")
    rows.append({"Model": name, "Accuracy": accuracy_score(yte, pred), "Precision": precision_score(yte, pred),
                 "Recall": recall_score(yte, pred), "F1": f1_score(yte, pred), "AUC": roc_auc_score(yte, proba)})
plt.plot([0, 1], [0, 1], "k--", alpha=.4); plt.legend(); plt.title("ROC curves")
plt.tight_layout(); plt.savefig("charts/07_roc.png", dpi=100); plt.close()
results = pd.DataFrame(rows).set_index("Model")
print("\nClassifier comparison:\n", results.round(3))

feat_names = NUM + list(fitted["Decision Tree"].named_steps["pre"].named_transformers_["cat"].named_steps["oh"].get_feature_names_out(CAT))
plt.figure(figsize=(18, 8))
plot_tree(fitted["Decision Tree"].named_steps["model"], feature_names=feat_names,
          class_names=["Died", "Survived"], filled=True, max_depth=3, fontsize=7)
plt.savefig("charts/08_tree.png", dpi=100); plt.close()

# --- 11. Imbalance handling comparison ---
imb = []
for label, clf in [("Baseline", LogisticRegression(max_iter=1000, random_state=42)),
                    ("class_weight=balanced", LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced"))]:
    pred = Pipeline([("pre", pre), ("model", clf)]).fit(Xtr, ytr).predict(Xte)
    imb.append({"Strategy": label, "Precision": precision_score(yte, pred), "Recall": recall_score(yte, pred), "F1": f1_score(yte, pred)})

Xtr_p, Xte_p = pre.fit_transform(Xtr, ytr), pre.transform(Xte)
Xtr_sm, ytr_sm = SMOTE(random_state=42).fit_resample(Xtr_p, ytr)  # train fold only, no leakage
clf = LogisticRegression(max_iter=1000, random_state=42).fit(Xtr_sm, ytr_sm)
pred = clf.predict(Xte_p)
imb.append({"Strategy": "SMOTE (train only)", "Precision": precision_score(yte, pred), "Recall": recall_score(yte, pred), "F1": f1_score(yte, pred)})
imb_df = pd.DataFrame(imb).set_index("Strategy")
print("\nImbalance comparison:\n", imb_df.round(3))
print(f"Best F1: {imb_df['F1'].idxmax()}")

# --- 12. GridSearchCV + OOB on Random Forest ---
rf_pipe = Pipeline([("pre", pre), ("model", RandomForestClassifier(oob_score=True, random_state=42))])
grid = GridSearchCV(rf_pipe, {"model__n_estimators": [100, 200, 300], "model__max_depth": [4, 6, 8, None],
                               "model__max_features": ["sqrt", "log2"]}, cv=5, scoring="f1", n_jobs=-1).fit(Xtr, ytr)
best_rf = grid.best_estimator_
print(f"\nBest RF params: {grid.best_params_}\nOOB score: {best_rf.named_steps['model'].oob_score_:.4f}")
fitted["Random Forest"] = best_rf
pred, proba = best_rf.predict(Xte), best_rf.predict_proba(Xte)[:, 1]
results.loc["Random Forest"] = [accuracy_score(yte, pred), precision_score(yte, pred), recall_score(yte, pred), f1_score(yte, pred), roc_auc_score(yte, proba)]
print("\nUpdated comparison (RF now tuned):\n", results.round(3))

# --- 13. Regression side-task: predict fare ---
rX, ry = df[["pclass", "age", "sibsp", "parch", "survived", "sex", "embarked"]], df["fare"]
rXtr, rXte, rytr, ryte = train_test_split(rX, ry, test_size=.2, random_state=42)
rpre = ColumnTransformer([("num", StandardScaler(), ["pclass", "age", "sibsp", "parch", "survived"]),
                           ("cat", OneHotEncoder(handle_unknown="ignore"), ["sex", "embarked"])])
reg = Pipeline([("pre", rpre), ("model", LinearRegression())]).fit(rXtr, rytr)
rpred = pd.Series(reg.predict(rXte), index=ryte.index)
mae, rmse, r2 = mean_absolute_error(ryte, rpred), mean_squared_error(ryte, rpred) ** .5, r2_score(ryte, rpred)
n, p = rXte.shape; adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)
print(f"\nRegression: MAE={mae:.2f} RMSE={rmse:.2f} R2={r2:.3f} AdjR2={adj_r2:.3f}")

resid = ryte - rpred
plt.scatter(rpred, resid, alpha=.5); plt.axhline(0, color="red", ls="--")
plt.xlabel("Predicted fare"); plt.ylabel("Residual"); plt.title("Residuals — fare regression")
plt.tight_layout(); plt.savefig("charts/09_residuals.png", dpi=100); plt.close()
lo, hi = resid[rpred < rpred.median()].std(), resid[rpred >= rpred.median()].std()
print(f"Residual std low-half={lo:.1f} high-half={hi:.1f} -> heteroscedastic (spread grows with predicted fare).")

# --- 14. Final comparison + recommendation ---
print("\nClassification metrics:\n", results.round(3))
print("\nRegression metrics (separate scale):\n", pd.DataFrame([{"MAE": mae, "RMSE": rmse, "R2": r2, "AdjR2": adj_r2}], index=["Linear Regression (fare)"]).round(3))
best = results["F1"].idxmax()
print(f"\nRecommendation: {best} — see README.md for the full written justification.")

# --- 15. Save best pipeline + reload check ---
best_pipe = fitted["Logistic Regression"]  # highest AUC, near-best F1, simplest to serve (see README)
joblib.dump(best_pipe, "models/best_pipeline.joblib")
reloaded = joblib.load("models/best_pipeline.joblib")
print("Reload matches original:", (best_pipe.predict(Xte.iloc[:3]) == reloaded.predict(Xte.iloc[:3])).all())
