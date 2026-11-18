# Adaptive Alert Presentation Simulation (CIC-IDS2017)

This repository contains the code and results for the paper *"Enhancing Critical Alert Visibility Through Adaptive Alert Presentation and Prioritization: A Data-Driven Simulation Study."*

The study uses labeled CIC-IDS2017 network flows as **proxy alert-generating events**. They are not native SOC alert logs, and the study does not measure human workload. A chronological alert display is compared with an adaptive display (severity ordering and grouping of repeated alerts) under fixed review budgets, and next-window alert-load prediction is evaluated.

## Contents

| File | Purpose |
|---|---|
| `soc_alert_fatigue_simulation.ipynb` | Full pipeline, executed with outputs: data loading, simulation, workload proxy, workflow comparison, prediction, figures, export |
| `run_notebook_inprocess.py` | Runs the notebook without Jupyter: `python run_notebook_inprocess.py soc_alert_fatigue_simulation.ipynb` |
| `execute_notebook.py` | Runs the notebook with Jupyter (`nbclient`) |
| `run_seed_sensitivity.py` | Re-runs the pipeline with seeds 1–10 and writes `seed_summary.csv` (about 10 minutes) |
| `exported_results/` | Results of the reported run (seed 42), the seed summary, and all figures |
| `TrafficLabelling/` | Put the eight CIC-IDS2017 TrafficLabelling CSV files here |

## Data

Download the CIC-IDS2017 dataset from the Canadian Institute for Cybersecurity: <https://www.unb.ca/cic/datasets/ids-2017.html>. Then place the eight `TrafficLabelling` CSV files in `TrafficLabelling/`. The dataset is not redistributed here.

## Reproduce

```bash
pip install -r requirements.txt
python run_notebook_inprocess.py soc_alert_fatigue_simulation.ipynb   # about 1-2 minutes
python run_seed_sensitivity.py                                         # optional: seeds 1-10
```

The reported results were produced with Python 3.13, pandas 3.0.5, numpy 2.5.3, and scikit-learn 1.9.1. Other library versions may change the model metrics slightly. `exported_results/paper_numbers.json` contains every number reported in the paper.

## Data handling decisions

- **Timestamps:** the TrafficLabelling timestamps use a 12-hour clock without an AM/PM marker. Hours 1–7 are shifted by 12 hours, which gives a timeline from Monday 08:56 to Friday 17:02.
- **Windows:** seven of the eight files record time only to the minute, so alerts are aggregated into 60-second windows.
- **Tie-breaking:** alerts that share a timestamp are ordered by a seeded random permutation.
- **Sampling:** the analysis uses a fixed-seed, 50,000-flow label-coverage sample. It keeps up to 50 flows per label and fills the rest at random.
- **Pre-specified settings:** review budgets are Low 50, Moderate 35, High 20, and Burst 10 alerts. The missed-risk coverage threshold is 0.20. None of these were tuned on outcomes.
- **Budget units:** the adaptive workflow is evaluated under a group-level budget (one displayed group counts as one review item) and an alert-level budget (each underlying alert counts as one item).
- **Prediction:** prediction uses consecutive active windows and a chronological 75/25 split. Each task includes a persistence baseline.

## Citation

If you use this code, please cite:

N. T. Natasha and S. R. Islam, "Enhancing Critical Alert Visibility Through Adaptive Alert Presentation and Prioritization: A Data-Driven Simulation Study," in *Proc. IEEE International Conference on Big Data (BigData), BDACPS Workshop*, 2026.
