# CNWB｜中文叙事写作基准 · 开源参考版

**Chinese Narrative Writing Benchmark** · `1.0.0-open.1` · STORY32 v2-r10 × SJ6 r0

[GitHub仓库](https://github.com/Lzauony/CNWB) · [English](README.en.md) · [快速使用](docs/QUICKSTART.md) · [方法](docs/METHODOLOGY.md) · [数据卡](docs/DATASET_CARD.md) · [数据格式](docs/DATA_FORMAT.md) · [验证](docs/VALIDATION.md) · [参考基准](docs/RELATED_WORK.md) · [公开边界](docs/PUBLICATION.md)

本版本提供32道中文创作任务、完整SJ6 r0协议、32份生成请求模板和256份评委请求模板、离线接收校验、两阶段评分投影、六维计分、双评均分、排名、合成样例与测试。Python 3.10+，核心工具仅用标准库，Windows/Linux/macOS均可运行，不依赖原CLLB工作区。

这是**已公开题目的参考集**，不是未见测试集。题库和量尺保持既有版本，未新增题目、未重评、未调整历史分数。适合研究、工具复现与方法比较；未来模型可能已接触这些材料，不能仅凭本集成绩证明未见情境上的泛化。

## 快速验证

在本目录执行：

```bash
python -B -X utf8 cnwb.py check
python -B -X utf8 -m unittest discover -s tests
python -B -X utf8 cnwb.py tasks
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --output out/demo-score.json
python -B -X utf8 cnwb.py rank out/demo-score.json --output out/demo-ranking.json
```

样例是明确标注的合成格式测试数据，32题等级均为3，因此总分60；这不代表任何模型的实测成绩。工具不含联网执行或付费API运行命令。真实作答/评审通过外部工具获得，再按[数据契约](docs/DATA_FORMAT.md)导入复算。

## 包含内容

| 目录 | 内容 |
|---|---|
| `benchmark/tasks.json` | 冻结任务结构：题文、材料、三维、观察项、交付形式及建议篇幅 |
| `benchmark/TASKBOOK.md` | 完整答题者题册；保留冻结时标题 |
| `benchmark/display_titles.json` | 网站现用标题别名，只用于展示 |
| `benchmark/prompts/` | 可直接构造消息的生成与B1/B2模板 |
| `benchmark/protocols/sj6-r0/` | 六维分级、阶段协议、格式与历史执行契约 |
| `tools/` | 请求构造、冻结SJ6核验/投影、接收容错、计分与排序 |
| `schemas/` | 作品与评审交换格式；评审另须通过动态材料绑定schema |
| `examples/` | 合成作品、评审、B1/B2及预期算术输出 |
| `tests/` | 阶段、哈希、容错、缺项、均分、排序与CLI测试 |
| `results/` | 已公开榜单的汇总快照与复现边界说明 |
| `docs/` | 方法、数据卡、操作、局限、贡献与发布边界 |

[公开网站](https://llmstory.github.io/)及[题目与作品](https://llmstory.github.io/#library)提供既有阅读体验。本包不携带私有逐篇评分/评语、原始HTTP响应、内部运行记录、凭证或未公开题目；也不复制真实模型作品。公开汇总快照可以查看，**无法仅凭该快照独立核验当前榜单的所有逐题评分**。对自有完整评审记录，本工具可执行离线复算。

## 评价与计分

每题只测指定三维。B1判1—4或null，数字4的维度进入独立B2，B2判1—5或null并覆盖对应B1；不平均、不择高。B2不接收B1分数与评语。只有交付完整且三维最终等级均为整数的作品进入完整作品聚合。

| 维度 | 全名（当前展示） | 权重 | 指定题数 |
|---|---|---:|---:|
| T1 | 叙事推进与结构 | 20% | 19 |
| T2 | 人物与关系 | 20% | 16 |
| T3 | 场景与世界 | 15% | 15 |
| T4 | 叙述与语言 | 20% | 19 |
| T5 | 生活体验与洞察 | 15% | 12 |
| T6 | 有效新意 | 10% | 15 |

T5冻结协议沿用“意义与经验”；当前展示名是别名，不改判据。每维在指定题目中等权平均，百分分=等级均值×20；总分按六维权重计算，理论范围20—100。全库32题与正文28题独立计算；规划4题无T4，故没有六维总分。

默认采用严格完整口径，缺项/null/非交付/未完成B2不填零，完整总分留空。需要可用完整作品口径时必须显式选择并记录理由，覆盖率仍保留；这种结果须与完整32题成绩区分。双评均分直接平均双方独立计算的未四舍五入分数，不另取共同题重算，任一方对应分数为空则均分为空。

结果是模型评委对文本的描述性判断，不是准确率、百分位、人工金标或统计显著性结论。格式通过不等于文学论证正确。见[方法与局限](docs/METHODOLOGY.md)。

## 版本、许可与引用

冻结材料中的 `development`、`adopted: false` 和 `api_calls: 0` 是原构建快照字段，不代表没有历史实测；本次开源整理本身API 0。历史执行文档提到的CLLB运行器没有随本包提供，不能据此声称本包具有HTTP调度或原生schema能力。

代码：[MIT](LICENSE)。项目编写的题目、协议与文档：[CC BY-SA 4.0](LICENSE-DATA)。第三方材料保留来源说明，合成样例不是模型实测或人类金标。详见[数据使用](DATA_USE.md)、[材料来源](benchmark/SOURCES.md)、[引用](CITATION.cff)。

参考了WritingBench的任务/评审/计分拆分，以及EQ-Bench和Short Story基准对生成条件、独立评委与覆盖率的说明方式；没有移植其题目、评分尺度、模型结果或代码。[比较与来源](docs/RELATED_WORK.md)
