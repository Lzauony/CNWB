# CNWB — Chinese Narrative Writing Benchmark

[中文](README.md) · CNWB v1.0 · SJ6 v1.0 · Software `1.0.2`

CNWB evaluates Chinese narrative writing through 32 tasks: stories, drama, planning, openings, revision, continuation and source transformation. Each task assigns three of six axes: narrative structure, characters and relationships, setting and world, narration and language, lived experience and insight, and effective originality.

Includes tasks, the SJ6 protocol, generation and judge templates, offline tools, synthetic examples and tests. Python 3.10+, standard library only; Windows/Linux/macOS. Use your own model client for generation and judging.

## Quick start

Run from the repository root:

```bash
python -B -X utf8 cnwb.py check
python -B -X utf8 -m unittest discover -s tests
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --output out/demo-score.json
python -B -X utf8 cnwb.py rank out/demo-score.json --output out/demo-ranking.json
```

Examples are synthetic, not model results: grade 3 on every axis gives a total of 60. Outputs never overwrite existing files. See the [workflow](docs/QUICKSTART.md) for real evaluations.

## Evaluation

B1 assigns 1–4 or null. Grade-4 axes require independent B2 (1–5 or null), which replaces B1 without seeing its judgments. Low scores, nulls and literary disagreements do not justify retries.

Axis scores equal mean grade ×20, weighted 20/20/15/20/15/10%. Full32 and prose28 are separate; planning4 has no T4 or overall score. Missing judgments are not zero-filled. Totals require complete coverage by default; available-work analysis must disclose its policy and coverage. Two-judge means average independently aggregated, unrounded scores; missing scores remain empty.

## Documentation and data

See the [tasks](benchmark/TASKBOOK.md), [protocol](benchmark/protocols/sj6-v1/GENERAL_PROTOCOL.md), [method](docs/METHODOLOGY.md), [data contract](docs/DATA_FORMAT.md), [dataset card](docs/DATASET_CARD.md) and [validation](docs/VALIDATION.md). Read real works on the [website](https://llmstory.github.io/#library).

Public tasks do not establish unseen-task generalization. Scores are descriptive model judgments, not accuracy, human gold labels or significance tests. The aggregate leaderboard snapshot cannot reproduce private per-work grades. Offline scoring is reproducible from complete records; new model calls may differ.

## License and citation

Code: [MIT](LICENSE); project-authored materials: [CC BY-SA 4.0](LICENSE-DATA). See [sources](benchmark/SOURCES.md), [data use](DATA_USE.md) and [contributing](CONTRIBUTING.md). Cite [CITATION.cff](CITATION.cff), specifying CNWB v1.0 / SJ6 v1.0.

Documentation references: [WritingBench](https://github.com/X-PLUG/WritingBench), [EQ-Bench](https://github.com/EQ-bench/creative-writing-bench) and [Story-Writing Benchmark](https://github.com/lechmazur/writing). Their tasks, code and results are not used here.
