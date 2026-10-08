# CNWB — Chinese Narrative Writing Benchmark

[中文](README.md) · Release `1.0.0-open.1` · STORY32 v2-r10 / SJ6 r0

A standalone **public reference set**, not a hidden or contamination-free test: 32 Chinese narrative tasks, three assigned axes per task, a six-axis rubric, exact generation and judge message templates, offline validation, two-stage score projection, aggregation, two-judge averaging, ranking and synthetic contract tests.

Python 3.10+, standard library only. No model API calls, credentials or original CLLB installation are needed.

```bash
python -B -X utf8 cnwb.py check
python -B -X utf8 -m unittest discover -s tests
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --output out/demo-score.json
```

Examples are synthetic fixtures, not literary evaluations or model results. Real model outputs and private per-work judgments are not bundled. A previously public aggregate leaderboard snapshot is included, but it is insufficient to independently verify historical per-work grades. Imported evaluations can be recomputed offline.

B1 grades each assigned axis from 1 to 4 or null. Grade-4 axes require independent B2, which may assign **1 to 5 or null**, replacing B1 rather than taking a maximum. B2 never receives B1 grades or critiques. Only delivered works with three final integer grades enter complete-work aggregation. Missing, null, incomplete and pending-B2 records are never zero-filled.

Axis scores equal mean grade ×20, weighted 20/20/15/20/15/10%. Planning tasks have no T4 and no six-axis overall score. Two-judge means use unrounded independently aggregated scores; no intersection-only recomputation. Results are model-judge descriptive assessments, not accuracy, percentiles or human-certified gold labels.

See [quick start](docs/QUICKSTART.md), [methodology](docs/METHODOLOGY.md), [dataset card](docs/DATASET_CARD.md), [data contract](docs/DATA_FORMAT.md), [related work](docs/RELATED_WORK.md) and [publication boundaries](docs/PUBLICATION.md).

Code: MIT. Project-authored task materials, protocols and prose documentation: CC BY-SA 4.0. Third-party materials and generated records have separate boundaries described in [DATA_USE.md](DATA_USE.md). Future unpublished evaluations should use newly authored held-out tasks, not merely renamed versions of this released set.
