# CNWB｜中文叙事写作基准

**Chinese Narrative Writing Benchmark** · CNWB v1.0 · SJ6 v1.0

[English](README.en.md) · [在线榜单与作品](https://llmstory.github.io/) · [快速使用](docs/QUICKSTART.md) · [题库](benchmark/TASKBOOK.md) · [评审协议](benchmark/protocols/sj6-v1/GENERAL_PROTOCOL.md)

CNWB通过32道中文创作任务，评价大模型的叙事推进、人物关系、场景与世界、叙述语言、生活体验与洞察，以及有效新意。涵盖故事、短剧、长篇规划与开头、修订、续写和材料加工；每题评价指定三维，全库形成六维观察网络。

## 测评榜单

2026-10-08公开快照，按DeepSeek V4.1 Flash与MiMo V2.6 Pro同文评审的总分各占50%平均，范围为全库32题。生成配置分别列出，使用未四舍五入的原值排序，表中保留两位小数。

<!-- CNWB:LEADERBOARD:BEGIN -->
| 排名 | 模型 | 生成配置 | 均分 | DeepSeek | MiMo | 完整计分题数（DS / MiMo） |
|---:|---|---|---:|---:|---:|---|
| 1 | Opus 5.5 | max16 + xhigh16 | 82.84 | 81.14 | 84.54 | 32/32 / 32/32 |
| 2 | GPT-6 Astra | xhigh | 81.79 | 79.24 | 84.33 | 32/32 / 32/32 |
| 3 | GLM 5.3 | max | 80.45 | 77.15 | 83.75 | 32/32 / 32/32 |
| 4 | GPT-5.6 Sol | xhigh | 79.83 | 78.73 | 80.93 | 32/32 / 32/32 |
| 5 | GLM 5.3 Flash | max | 78.60 | 75.59 | 81.60 | 32/32 / 32/32 |
| 6 | Opus 5.5 | medium | 78.46 | 76.31 | 80.61 | 32/32 / 32/32 |
| 7 | Kimi K3 | max | 78.37 | 75.35 | 81.38 | 32/32 / 31/32 |
| 8 | Grok 4.7 | high | 77.84 | 74.95 | 80.74 | 31/32 / 31/32 |
| 9 | MiMo V2.6 Pro | 默认 | 77.60 | 75.51 | 79.69 | 32/32 / 32/32 |
| 10 | Kimi K2.8 Preview | max | 77.21 | 75.21 | 79.21 | 32/32 / 32/32 |
| 11 | MiMo V2.6 Flash | 默认 | 74.77 | 71.67 | 77.87 | 32/32 / 32/32 |
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
| 23 | MiniMax M3 | 默认 | 64.76 | 62.94 | 66.57 | 32/32 / 32/32 |
| 24 | DeepSeek V3.2 | 默认 | 62.54 | 62.56 | 62.53 | 32/32 / 32/32 |
<!-- CNWB:LEADERBOARD:END -->

Grok两评委均缺A13作品；HY4 / MiMo缺A02评分；Kimi K3 / MiMo缺A15评分。这些组沿用已声明的31题完整作品口径，缺项不填零；双方先独立聚合，再平均，不另取共同题目重算。其他组两评委各计32题。

模型能力或有波动，生成条件也有差异；榜单仅描述本次实测，小分差不代表统计显著。分数不是准确率或百分位。六维成绩及分组比较见[在线榜单](https://llmstory.github.io/)，原始汇总与复现边界见[results/](results/README.md)。

## 快速开始

Python 3.10+，仅使用标准库，支持Windows/Linux/macOS。克隆后在根目录执行，无需安装依赖：

```bash
git clone https://github.com/Lzauony/CNWB.git
cd CNWB
python -B -X utf8 cnwb.py check
python -B -X utf8 cnwb.py leaderboard
```

运行一次合成计分示例：

```bash
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --output out/demo-score.json
python -B -X utf8 cnwb.py rank out/demo-score.json --output out/demo-ranking.json
```

示例全部等级为3，预期总分60，不是模型实测。输出写入新文件，不覆盖既有结果。

测评自己的模型：按[快速使用](docs/QUICKSTART.md)完成 **创作 → B1 → 入围维度独立B2 → 校验 → 计分与排名**。使用者自行调用模型，仓库工具负责构造请求、接收响应及离线算分。B1判1—4级或null；数字4的维度进入独立B2，B2判1—5级或null并覆盖对应B1。

## 从哪里开始

| 你想做什么 | 入口 |
|---|---|
| 看模型成绩、读作品 | 上方榜单与[网站](https://llmstory.github.io/#library) |
| 看32题与评审标准 | [benchmark/](benchmark/TASKBOOK.md)与[协议](benchmark/protocols/sj6-v1/GENERAL_PROTOCOL.md) |
| 测自己的模型 | [docs/QUICKSTART.md](docs/QUICKSTART.md)与[examples/](examples/README.md) |
| 了解计分、方法与局限 | [docs/METHODOLOGY.md](docs/METHODOLOGY.md) |
| 接入工具或验证修改 | [数据格式](docs/DATA_FORMAT.md)、`tools/`与`tests/` |

项目只有一个命令入口`cnwb.py`。`benchmark/`保存基准材料，`results/`保存公开成绩，`docs/`集中说明，`examples/`和`tests/`用于试用与验证。交换schema和文件清单归入`tools/`；贡献与安全说明归入`.github/`。

默认计分要求完整覆盖，缺项不填零。全库32题、正文28题分别计算；规划4题无T4，不计算六维总分。双评任一方缺少对应分数时均分留空。完整定义见[方法](docs/METHODOLOGY.md)，发布核验见[验证说明](docs/VALIDATION.md)。

本题库已公开，不能单凭成绩证明未见任务上的泛化。公开汇总不含真实逐篇评分或评语，无法据此独立复核全部等级；自己的完整作品与评审记录可用于复现离线算分。

## 许可与引用

代码采用[MIT](LICENSE)；项目编写的题目、协议与文档采用[CC BY-SA 4.0](LICENSE-DATA)。第三方背景资料见[材料来源](benchmark/SOURCES.md)，作品与其他数据见[数据使用说明](docs/DATA_USE.md)。引用使用[CITATION.cff](CITATION.cff)，注明CNWB v1.0与SJ6 v1.0。

[贡献](.github/CONTRIBUTING.md) · [安全](.github/SECURITY.md) · [数据卡](docs/DATASET_CARD.md) · [软件发布说明](CHANGELOG.md)（当前1.0.3）

文档与使用流程参考了[WritingBench](https://github.com/X-PLUG/WritingBench)、[EQ-Bench Creative Writing](https://github.com/EQ-bench/creative-writing-bench)、[EQ-Bench Longform Writing](https://github.com/EQ-bench/longform-writing-bench)和[LLM Creative Story-Writing Benchmark](https://github.com/lechmazur/writing)的公开说明；未使用其题目、代码或模型结果。
