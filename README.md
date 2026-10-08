# CNWB｜中文叙事写作基准

**Chinese Narrative Writing Benchmark** · CNWB v1.0 · SJ6 v1.0 · 软件版本 `1.0.2`

[English](README.en.md) · [快速使用](docs/QUICKSTART.md) · [方法](docs/METHODOLOGY.md) · [题库](benchmark/TASKBOOK.md) · [评审协议](benchmark/protocols/sj6-v1/GENERAL_PROTOCOL.md) · [在线榜单与作品](https://llmstory.github.io/)

CNWB 通过32道中文创作任务，评价大模型如何组织叙事、刻画人物、运用场景、控制表达、呈现生活体验和形成有效新意。任务涵盖故事、短剧、长篇规划与开头、修订、续写和材料加工；每题评价指定三维，全库形成六维观察网络。

仓库提供题库、评审协议、请求模板、离线校验与计分工具、合成示例和测试。Python 3.10+，仅使用标准库，支持Windows/Linux/macOS。使用者自行调用模型完成生成与评审，工具负责请求构造、响应接收和成绩复算。

## 快速开始

下载仓库后，在根目录执行：

```bash
python -B -X utf8 cnwb.py check
python -B -X utf8 -m unittest discover -s tests
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --output out/demo-score.json
python -B -X utf8 cnwb.py rank out/demo-score.json --output out/demo-ranking.json
```

示例是合成数据，全部等级为3，预期总分60，不代表模型实测。输出不覆盖既有文件。真实测评流程见[快速使用](docs/QUICKSTART.md)：创作 → B1 → 入围维度独立B2 → 校验 → 计分与排名。

## 评价与计分

| 维度 | 衡量内容 | 权重 | 指定题数 |
|---|---|---:|---:|
| T1 叙事推进与结构 | 事件、感知与信息如何形成有效进程、节奏和落点 | 20% | 19 |
| T2 人物与关系 | 人物选择的具体性、可信度及相互影响 | 20% | 16 |
| T3 场景与世界 | 环境、条件与规则如何组织行动、代价和感受 | 15% | 15 |
| T4 叙述与语言 | 声音、视角、节奏、修辞与省略的控制和表现力 | 20% | 19 |
| T5 生活体验与洞察 | 行动、关系、感知与思考形成的经验和认识 | 15% | 12 |
| T6 有效新意 | 题给前提之外，本次创作自身特点及其实际作用 | 10% | 15 |

B1判1—4级或null；数字4的维度进入独立B2，B2判1—5级或null并覆盖对应B1。B2不接收B1分数或评语。保留首份符合接收契约的响应，低分、null和文学分歧不触发重抽。

维度分为指定题目等级均值×20，总分按表中权重计算。全库32题与正文28题分列；规划4题无T4，不计算六维总分。默认要求全部题目完整，缺项不填零；可用完整作品口径须显式选择并报告覆盖率。双评先独立聚合，再按未四舍五入的分数各占50%平均；任一方对应分数缺失，均分留空。详见[方法文档](docs/METHODOLOGY.md)。

## 仓库内容

| 路径 | 用途 |
|---|---|
| `benchmark/tasks.json`、`benchmark/TASKBOOK.md` | 32题的要求、材料、指定维度与交付形式 |
| `benchmark/prompts/` | 32份生成模板、256份B1/B2评委模板 |
| `benchmark/protocols/sj6-v1/` | 六维分级、两阶段评审、格式与执行要求 |
| `cnwb.py`、`tools/` | 请求构造、接收校验、评分投影、计分、均分与排名 |
| `schemas/`、`examples/`、`tests/` | 数据契约、合成示例与验证测试 |
| `results/` | 公开榜单汇总快照及其复现边界 |
| `docs/` | 使用、方法、数据格式、数据卡与验证说明 |

[数据格式](docs/DATA_FORMAT.md) · [数据卡](docs/DATASET_CARD.md) · [验证说明](docs/VALIDATION.md) · [在线阅读](https://llmstory.github.io/#library)

## 结果解释

本题库已经公开，后续模型可能接触过这些材料，成绩不能单独证明未见任务上的泛化。分数是模型评委对文本的描述性判断，不是准确率、百分位或人工金标；小分差不代表统计显著。

仓库中的榜单文件只有汇总结果，不含真实逐篇评分或评语，无法据此独立复核全部榜单等级。使用自己的完整作品和评审记录，可以复现离线校验、投影与算术；重新调用模型不保证产生相同文本或等级。

## 许可与引用

代码采用[MIT](LICENSE)；项目编写的题目、协议与文档采用[CC BY-SA 4.0](LICENSE-DATA)。第三方背景资料见[材料来源](benchmark/SOURCES.md)，作品与其他数据的使用范围见[DATA_USE.md](DATA_USE.md)。引用请使用[CITATION.cff](CITATION.cff)，并注明CNWB v1.0与SJ6 v1.0。贡献方式见[CONTRIBUTING.md](CONTRIBUTING.md)。

仓库文档与使用流程的整理参考了[WritingBench](https://github.com/X-PLUG/WritingBench)、[EQ-Bench Creative Writing](https://github.com/EQ-bench/creative-writing-bench)、[EQ-Bench Longform Writing](https://github.com/EQ-bench/longform-writing-bench)和[LLM Creative Story-Writing Benchmark](https://github.com/lechmazur/writing)的公开说明；未使用这些项目的题目、代码或模型结果。
