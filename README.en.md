# CNWB — Chinese Narrative Writing Benchmark

CNWB v1.0 · SJ6 v1.0 · [中文](README.md)

[Website and stories](https://llmstory.github.io/) · [Quick start](docs/QUICKSTART.md) · [Tasks](benchmark/TASKBOOK.md) · [Protocol](benchmark/protocols/sj6-v1/GENERAL_PROTOCOL.md)

CNWB evaluates Chinese narrative writing with 32 tasks covering stories, drama, planning, openings, revision, continuation and source transformation. Each task assigns three of six axes: narrative progression and structure, characters and relationships, setting and world, narration and language, lived experience and insight, and effective originality.

## Leaderboard

Public snapshot dated 2026-10-08. The full32 leaderboard averages independent judgments from DeepSeek V4.1 Flash and MiMo V2.6 Pro at 50% each. Configurations are listed separately. Ranking uses unrounded values; display rounds to two decimals.

<!-- CNWB:LEADERBOARD:BEGIN -->
| Rank | Model | Configuration | Mean | DeepSeek | MiMo | Scored tasks (DS / MiMo) |
|---:|---|---|---:|---:|---:|---|
| 1 | Opus 5.5 | max16 + xhigh16 | 82.84 | 81.14 | 84.54 | 32/32 / 32/32 |
| 2 | GPT-6 Astra | xhigh | 81.79 | 79.24 | 84.33 | 32/32 / 32/32 |
| 3 | GLM 5.3 | max | 80.45 | 77.15 | 83.75 | 32/32 / 32/32 |
| 4 | GPT-5.6 Sol | xhigh | 79.83 | 78.73 | 80.93 | 32/32 / 32/32 |
| 5 | GLM 5.3 Flash | max | 78.60 | 75.59 | 81.60 | 32/32 / 32/32 |
| 6 | Opus 5.5 | medium | 78.46 | 76.31 | 80.61 | 32/32 / 32/32 |
| 7 | Kimi K3 | max | 78.37 | 75.35 | 81.38 | 32/32 / 31/32 |
| 8 | Grok 4.7 | high | 77.84 | 74.95 | 80.74 | 31/32 / 31/32 |
| 9 | MiMo V2.6 Pro | default | 77.60 | 75.51 | 79.69 | 32/32 / 32/32 |
| 10 | Kimi K2.8 Preview | max | 77.21 | 75.21 | 79.21 | 32/32 / 32/32 |
| 11 | MiMo V2.6 Flash | default | 74.77 | 71.67 | 77.87 | 32/32 / 32/32 |
| 12 | Doubao Seed 2.1 Pro | high | 73.42 | 71.01 | 75.83 | 32/32 / 32/32 |
| 13 | Gemini 3.8 Flash | high | 73.33 | 72.37 | 74.28 | 32/32 / 32/32 |
| 14 | GPT-5.6 Luna | xhigh | 72.76 | 71.16 | 74.37 | 32/32 / 32/32 |
| 15 | Qwen 3.8 Max | xhigh | 71.81 | 68.35 | 75.27 | 32/32 / 32/32 |
| 16 | Opus 4.6 | high | 71.38 | 67.79 | 74.98 | 32/32 / 32/32 |
| 17 | DeepSeek V4.1 Flash | high | 69.54 | 67.82 | 71.26 | 32/32 / 32/32 |
| 18 | DeepSeek V4 Pro | max | 69.10 | 65.41 | 72.80 | 32/32 / 32/32 |
| 19 | Qwen 3.8 27B | xhigh | 68.85 | 65.70 | 72.00 | 32/32 / 32/32 |
| 20 | Qwen 3.8 Flash | xhigh | 68.45 | 66.96 | 69.95 | 32/32 / 32/32 |
| 21 | Tencent HY4 Preview | high | 65.80 | 63.01 | 68.60 | 32/32 / 31/32 |
| 22 | Gemini 3.1 Pro Preview | high | 65.19 | 64.02 | 66.36 | 32/32 / 32/32 |
| 23 | MiniMax M3 | default | 64.76 | 62.94 | 66.57 | 32/32 / 32/32 |
| 24 | DeepSeek V3.2 | default | 62.54 | 62.56 | 62.53 | 32/32 / 32/32 |
<!-- CNWB:LEADERBOARD:END -->

Grok lacks the A13 work for both judges; HY4 / MiMo lacks A02 judging; Kimi K3 / MiMo lacks A15 judging. These groups use the declared 31-complete-work policy, without zero filling. Each judge aggregates independently before averaging; no common-task subset is recomputed. Other groups have 32 scored tasks per judge.

Results describe this evaluation under differing generation conditions. Small differences do not establish statistical significance; scores are not accuracy or percentiles. See the [website](https://llmstory.github.io/) for axis scores and comparisons, and [results/](results/README.md) for the aggregate snapshot and reproduction limits.

## Quick start

Python 3.10+, standard library only; Windows/Linux/macOS. No dependency installation is needed.

```bash
git clone https://github.com/Lzauony/CNWB.git
cd CNWB
python -B -X utf8 cnwb.py check
python -B -X utf8 cnwb.py leaderboard
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --output out/demo-score.json
python -B -X utf8 cnwb.py rank out/demo-score.json --output out/demo-ranking.json
```

The synthetic example assigns grade 3 on every axis, yielding 60; it is not a model result. Outputs never overwrite existing files. For real evaluations, follow the [workflow](docs/QUICKSTART.md): generation → B1 → independent B2 for eligible axes → validation → scoring and ranking. Supply your own model client; these tools run offline.

## Repository guide

| Goal | Entry |
|---|---|
| Inspect results and stories | Leaderboard above and [website](https://llmstory.github.io/#library) |
| Read tasks and judging standards | [benchmark/](benchmark/TASKBOOK.md) and [protocol](benchmark/protocols/sj6-v1/GENERAL_PROTOCOL.md) |
| Evaluate your model | [Quick start](docs/QUICKSTART.md) and [examples/](examples/README.md) |
| Understand scoring and limitations | [Methodology](docs/METHODOLOGY.md) |
| Integrate or validate tools | [Data format](docs/DATA_FORMAT.md), `tools/` and `tests/` |

`cnwb.py` is the sole command entry. Materials live in `benchmark/`, public aggregates in `results/`, documentation in `docs/`, sample inputs in `examples/` and tests in `tests/`. Exchange schemas and integrity manifests are grouped under `tools/`; contributor and security guidance is under `.github/`.

B1 assigns 1–4 or null. Grade-4 axes require independent B2 (1–5 or null), which replaces B1 without seeing its judgments. Missing values are never zero-filled. Full32 and prose28 are separate; planning4 has no T4 or overall score. Two-judge averages retain missing scores. See the [method](docs/METHODOLOGY.md) and [validation](docs/VALIDATION.md).

Public tasks do not establish unseen-task generalization. Scores are descriptive model judgments, not human gold labels. The public snapshot omits per-work grades and comments, so it cannot reproduce all published judgments; offline arithmetic is reproducible from complete records.

## License and citation

Code: [MIT](LICENSE); project-authored materials: [CC BY-SA 4.0](LICENSE-DATA). See [sources](benchmark/SOURCES.md) and [data use](docs/DATA_USE.md). Cite [CITATION.cff](CITATION.cff), specifying CNWB v1.0 / SJ6 v1.0.

[Contributing](.github/CONTRIBUTING.md) · [Security](.github/SECURITY.md) · [Dataset card](docs/DATASET_CARD.md) · [Software releases](CHANGELOG.md) (current: 1.0.3)

Documentation references: [WritingBench](https://github.com/X-PLUG/WritingBench), [EQ-Bench](https://github.com/EQ-bench/creative-writing-bench) and [Story-Writing Benchmark](https://github.com/lechmazur/writing). Their tasks, code and results are not used here.
