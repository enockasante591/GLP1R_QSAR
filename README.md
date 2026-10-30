# Predicting GLP-1 receptor agonist potency (pEC50) from four molecular descriptors

A reproducible workflow that takes a small descriptor table (EC50 + four descriptors per compound) through
**data division → model training and comparison → validation**. Four regression models are trained and compared:
**Linear Regression, Ridge, XGBoost and a multilayer perceptron (MLP)**.

> The compound data used in the original work are **not included**. See [`data/README.md`](data/README.md) for the
> expected format, and run the pipeline on the synthetic example to see every output.

## Workflow

| step | script | what it does |
|---|---|---|
| 1 | `src/01_data_division.py` | reads the table, converts EC50 → pEC50, keeps the descriptors, splits 80/20 (`random_state = 42`) |
| 2 | `src/02_data_division_figure.py` | figure of the split and of the pEC50 range of each set |
| 3 | `src/03_train_and_compare_models.py` | tunes and compares the four models (scaling inside each pipeline) and saves them |
| 4 | `src/04_learning_curves.py` | validation: learning curves |
| 5 | `src/05_y_randomization.py` | validation: y-randomization (scrambled-activity test) |
| 6 | `src/06_applicability_domain.py` | validation: applicability domain (leverage / Williams plot, descriptor ranges, kNN distance) |
| 7 | `src/07_evaluate_all_compounds.py` | predicted vs experimental for all compounds (saved and cross-validated predictions), agreement between models, bootstrap comparison |
| 8 | `src/08_validation_figures.py` | publication figures, panels (a)–(d) = Linear Regression, Ridge, XGBoost, MLP |
| 9 | `src/09_y_randomization_boxplot.py` | y-randomization box plot with p-values |
| 10 | `src/10_summary_tables.py` | summary tables (R², Pearson r, Spearman ρ) |

Optional steps in `extras/` (run with `--extras`): a consensus model saved as one `.pkl`, prediction of new compounds
with applicability-domain flags, performance versus training-set size, and an alternative 70/41 split.

## Repository layout

```
├── data/        input tables (not committed)         ├── src/       workflow steps 1-10 + shared code
├── models/      saved models (.pkl, not committed)   ├── extras/    optional steps
├── results/     tables and figures (generated)       ├── examples/  synthetic example data generator
└── run_pipeline.py
```

## Installation

```bash
git clone <your-repository-url>
cd <repository>
pip install -r requirements.txt
```
Developed with Python 3.12, scikit-learn 1.8, XGBoost 3.4, pandas 3.0, NumPy 2.4, SciPy 1.17 and
Matplotlib 3.10. Other recent versions should work.

## Quick start

```bash
python examples/make_example_data.py            # synthetic data - format demo only
python run_pipeline.py --data data/example_dataset.csv --new data/example_new_compounds.csv --extras --quick
```

On your own data:

```bash
cp my_descriptors.csv data/Descriptors_combined.csv      # see data/README.md for the columns
python run_pipeline.py                                    # steps 1-10
python run_pipeline.py --extras --new my_new_compounds.csv
```
`--quick` uses fewer repeats and skips nested cross-validation: it is a smoke test, **not for reported results**.
Resume with `--from 5`, run one step with `--only 8`, list the steps with `--list`. Every script also runs alone:
`python src/08_validation_figures.py`.

## Methods summary

* **Target.** pEC50 = −log10(EC50 in mol/L). EC50 can be a number or text such as `9.81×1E-9`; censored values (`<`, `>`) are dropped.
* **Division.** One random 80/20 split of the compounds (`random_state = 42`), saved so every step uses the same sets.
* **Models.** Each model is a scikit-learn `Pipeline` of `StandardScaler` (fitted on the training data only) followed by the regressor.
* **Tuning.** Grid search with 5-fold cross-validation on the training set only (criterion: RMSE):
  Ridge `alpha` (13 values, 10⁻³–10³); XGBoost `n_estimators`, `max_depth`, `learning_rate`, `reg_lambda` (24 combinations);
  MLP hidden-layer sizes, `alpha`, initial learning rate (32 combinations, up to 2000 iterations). Linear Regression has nothing to tune.
* **Comparison.** Training, nested 5-fold cross-validation (mean ± SD) and test R², RMSE and MAE (step 3); cross-validated predictions for
  all compounds with a paired bootstrap of the RMSE differences (step 7).
* **Learning curves.** Training and cross-validated error for growing training sets, repeated 5-fold CV, tuned settings.
* **Y-randomization.** The activity is scrambled 100 times; each model is re-trained and cross-validated. The empirical
  p-value is (1 + number of scrambled models with Q² ≥ real Q²) / (N + 1), so with N = 100 the smallest possible value is 0.0099.
  The regression line of R²/Q² against |correlation| is also reported (Wold criterion).
* **Applicability domain.** Defined by the training set: leverage h\* = 3(p + 1)/n, the min–max range of each descriptor, and the mean
  distance to the 3 nearest training compounds (cut-off mean + 1 SD, standardized descriptors). Standardized residuals beyond ±3 are flagged.

All random seeds are fixed (`SEED` in `src/common.py`), so reruns reproduce the same numbers on the same library versions.

## Limitations

* The data set is small, so performance estimates are noisy: a single test set of about 20 compounds can differ a lot from another
  random split. Prefer the cross-validated results (steps 3 and 7) and the spread across splits (`extras/split_70_41.py`).
* If the four descriptors were chosen using all compounds before the split, every score is somewhat optimistic.
* Predictions for compounds outside the applicability domain are extrapolations and should not be used to rank compounds.
* Models are meant for ranking and prioritisation; the typical error is of the order of one pEC50 unit on this kind of data.
* Pickled models (`.pkl`) can execute code when loaded: load only files you trust, with the library versions that created them.

## License and citation

*Add a license file of your choice and your citation details here.*
