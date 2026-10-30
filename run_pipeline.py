"""
run_pipeline.py - run the workflow from data division to validation.

  python run_pipeline.py                      steps 1-10 (core workflow)
  python run_pipeline.py --extras             also the optional extras (consensus model, new compounds, ...)
  python run_pipeline.py --quick              fast smoke test (fewer repeats, no nested CV) - not for reported results
  python run_pipeline.py --data my.csv        use another descriptor table
  python run_pipeline.py --new  new.csv       descriptor table of new compounds (extras)
  python run_pipeline.py --from 4 / --only 8  start at / run a single step
  python run_pipeline.py --list               show the steps
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = [
    (1, "src/01_data_division.py", "prepare the data (EC50 -> pEC50) and split 80/20"),
    (2, "src/02_data_division_figure.py", "figure: data division and pEC50 range"),
    (3, "src/03_train_and_compare_models.py", "tune and compare Linear Regression, Ridge, XGBoost, MLP"),
    (4, "src/04_learning_curves.py", "validation: learning curves"),
    (5, "src/05_y_randomization.py", "validation: y-randomization"),
    (6, "src/06_applicability_domain.py", "validation: applicability domain (Williams plots)"),
    (7, "src/07_evaluate_all_compounds.py", "predicted vs experimental for all compounds, model agreement"),
    (8, "src/08_validation_figures.py", "figures: learning curves, y-randomization, domain (panels a-d)"),
    (9, "src/09_y_randomization_boxplot.py", "figure: y-randomization box plot"),
    (10, "src/10_summary_tables.py", "summary tables (R2, Pearson r, Spearman rho)"),
]
EXTRAS = [
    (11, "extras/consensus_model.py", "save the consensus model (.pkl)"),
    (12, "extras/predict_new_compounds.py", "predict new compounds + applicability domain"),
    (13, "extras/new_compound_tables.py", "tables for the new compounds"),
    (14, "extras/reduced_training_set.py", "performance vs training-set size"),
    (15, "extras/split_70_41.py", "alternative 70/41 split"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--extras", action="store_true")
ap.add_argument("--quick", action="store_true")
ap.add_argument("--data")
ap.add_argument("--new")
ap.add_argument("--from", dest="start", type=int, default=1)
ap.add_argument("--only", type=int)
ap.add_argument("--list", action="store_true")
a = ap.parse_args()

steps = CORE + (EXTRAS if (a.extras or (a.only and a.only > 10)) else [])
if a.list:
    for n, f, d in CORE + EXTRAS:
        print(f"{n:>2}  {f:38} {d}")
    sys.exit()

env = dict(os.environ)
if a.data:
    env["GLP1_DATA"] = str(Path(a.data).resolve())
if a.new:
    env["GLP1_NEW"] = str(Path(a.new).resolve())
if a.quick:
    env.update({"QUICK": "1", "N_PERM": "10", "LC_REPEATS": "1", "N_REPEATS": "20"})
    print("QUICK mode: for testing only, not for reported results.\n")

t0, done = time.time(), []
for n, f, d in steps:
    if (a.only and n != a.only) or n < a.start:
        continue
    if n >= 12 and n <= 13 and not Path(env.get("GLP1_NEW", ROOT / "data" / "Descriptors_designed_compounds.csv")).exists():
        print(f"[{n:>2}] skipped {f}: no new-compound file (use --new)")
        continue
    print(f"[{n:>2}] {f} - {d}", flush=True)
    t = time.time()
    if subprocess.run([sys.executable, str(ROOT / f)], cwd=str(ROOT), env=env).returncode != 0:
        sys.exit(f"\nStep {n} ({f}) failed. Fix it and resume with:  python run_pipeline.py --from {n}")
    done.append(n)
    print(f"     done in {time.time() - t:.0f}s\n", flush=True)

print(f"Finished steps {done} in {(time.time() - t0) / 60:.1f} min.  Results: {ROOT / 'results'}")
