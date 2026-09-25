"""Part A: load Titanic ONCE, profile, clean, EDA. Works in Colab or locally.
Run: python 01_eda.py
"""
import sys, subprocess, pathlib
if "google.colab" in sys.modules:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                     str(pathlib.Path(__file__).parent / "requirements.txt")])

import pandas as pd, seaborn as sns
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

pathlib.Path("charts").mkdir(exist_ok=True)

# --- 1. Load + profile (the ONE load for the whole module) ---
df = sns.load_dataset("titanic")
print("shape:", df.shape)
df.info()
print(df.describe().T)
miss = (df.isna().mean() * 100).round(2)
miss = miss[miss > 0].sort_values(ascending=False)
print("\n% missing:\n", miss)
df.to_csv("titanic.csv", index=False)  # offline fallback, saved right after load

# --- 2. Missing-value handling (<5% drop, 5-30% impute, very-high -> own category) ---
df["age"] = df["age"].fillna(df["age"].median())                 # ~19.9% -> median impute
df = df.dropna(subset=["embarked", "embark_town"])                # ~0.2% -> drop rows
df["deck"] = df["deck"].astype(object).fillna("Missing")          # ~77% -> own category, excluded from modeling
print(f"\nage 19.9% missing -> median-imputed ({df['age'].median()}).")
print("embarked/embark_town 0.2% missing -> rows dropped.")
print("deck 77% missing -> encoded as its own 'Missing' category (too high to impute reliably).")
df.to_csv("titanic.csv", index=False)  # overwrite with the cleaned version for 02_modeling.py

# --- 3. Univariate: age & fare ---
def iqr_outliers(s):
    q1, q3 = s.quantile([.25, .75])
    iqr = q3 - q1
    return ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()

print(f"\nIQR outliers -> age: {iqr_outliers(df['age'])}, fare: {iqr_outliers(df['fare'])}")
fig, ax = plt.subplots(2, 2, figsize=(10, 7))
ax[0, 0].hist(df["age"], bins=30); ax[0, 0].set_title("Age hist")
ax[0, 1].boxplot(df["age"]); ax[0, 1].set_title("Age box")
ax[1, 0].hist(df["fare"], bins=30); ax[1, 0].set_title("Fare hist")
ax[1, 1].boxplot(df["fare"]); ax[1, 1].set_title("Fare box")
plt.tight_layout(); plt.savefig("charts/01_univariate.png", dpi=100); plt.close()

m, med, mode = df["fare"].mean(), df["fare"].median(), df["fare"].mode()[0]
print(f"fare mean={m:.2f} median={med:.2f} mode={mode:.2f} -> "
      f"{'right-skewed' if m > med > mode else 'not clearly right-skewed'} (mean > median > mode)")

# --- 4. Bivariate: survival rate + correlation heatmap ---
print("\nSurvival by sex:\n", df.groupby("sex")["survived"].mean().round(3))
print("Survival by pclass:\n", df.groupby("pclass")["survived"].mean().round(3))
print("Survival by sex+pclass:\n", df.groupby(["sex", "pclass"])["survived"].mean().round(3))

cols = ["survived", "pclass", "age", "sibsp", "parch", "fare"]
corr = df[cols].corr()
pairs = sorted(((corr.loc[a, b], a, b) for i, a in enumerate(cols) for b in cols[i + 1:]),
               key=lambda x: abs(x[0]), reverse=True)
print("\nTop 2 |correlation| pairs:", [(a, b, round(r, 3)) for r, a, b in pairs[:2]])
plt.figure(figsize=(6, 5)); sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.tight_layout(); plt.savefig("charts/02_correlation.png", dpi=100); plt.close()

# --- 5. Multivariate data story (4 charts) ---
sns.barplot(data=df, x="pclass", y="survived", hue="sex"); plt.title("Survival by class & sex")
plt.tight_layout(); plt.savefig("charts/03_class_sex.png", dpi=100); plt.close()

sns.boxplot(data=df, x="survived", y="age"); plt.title("Age by survival")
plt.tight_layout(); plt.savefig("charts/04_age_survival.png", dpi=100); plt.close()

sns.scatterplot(data=df, x="fare", y="age", hue="survived", alpha=.6); plt.title("Fare vs age by survival")
plt.tight_layout(); plt.savefig("charts/05_fare_age.png", dpi=100); plt.close()

fam = df["sibsp"] + df["parch"]
sns.barplot(x=fam, y=df["survived"]); plt.title("Survival by family size")
plt.tight_layout(); plt.savefig("charts/06_family_size.png", dpi=100); plt.close()
print("\nSaved charts/01-06.png. See README.md for the written interpretation of each.")

# --- 6. Exploratory standardization check (age, fare) — EDA-only, not reused in modeling ---
before = df[["age", "fare"]].agg(["mean", "std"])
z = df[["age", "fare"]].apply(lambda s: (s - s.mean()) / s.std())
print("\nBefore standardization:\n", before)
print("After z-score:\n", z.agg(["mean", "std"]))
