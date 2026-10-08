# 贡献指南

阅读[方法](../docs/METHODOLOGY.md)和[数据格式](../docs/DATA_FORMAT.md)，用最小合成输入描述问题、复现步骤及预期行为。不要提交私有作品、评语、原始HTTP响应或凭证。

题库、协议与计分工具按版本发布。题文或判据变化须新增基准或协议版本；工具和文档变化须说明范围。测评验收不能以目标排名或等级分布为依据。修复测试应覆盖实际边界。

## 材料与执行模板

CNWB v1.0的材料是共同审核、按哈希冻结的一套文件：

| 文件 | 作用与使用者 |
|---|---|
| benchmark/tasks.json | 结构化题文、源文、指定维度和观察项；工具读取任务定义 |
| benchmark/display_titles.json、TASKBOOK.md | 阅读导航标题与面向创作者的题册 |
| benchmark/scoring.json | 离线权重、范围与规划题集合 |
| benchmark/protocols/sj6-v1/ | 完整可读规则、分级判据及格式契约 |
| benchmark/prompts/generation/ | 实际创作消息模板 |
| benchmark/prompts/judge/ | 实际B1/B2消息和动态输出契约模板 |

`tools/protocol.py`读取冻结JSON模板，填入作品、作品哈希和指定B2维度；**不会在运行时把协议Markdown编译成请求**。评委模板是按题目和阶段整理的执行材料，不是完整协议文档的简单拼接。读者用完整协议理解判据，模型调用使用生成的消息；出现二者不一致应报告并审查，不能临时任选一份定义。

维护普通工具或导览文档时，保持benchmark/全部文件不变。新题文、新判据或新模板属于新基准/协议材料，应另立版本，明确结构化任务、题册、协议、模板和计分定义之间的变化，审核所有受影响的阶段和B2维度组合，再冻结新的清单。仅修改Markdown不会更新模型实际收到的规则。本包不提供通用新协议模板编译器；现有`manifest`命令也不用于把改过的材料重新声明为CNWB v1.0。

模型、生成轮次、评委和评审revision分别保存。保留首份有效响应；低分、null及内容诊断不触发重抽。缺项不填零，未测维度不推算，覆盖率和计分口径必须明确。

提交前执行：

```bash
python -B -X utf8 cnwb.py check
python -B -X utf8 -m unittest discover -s tests
```

`check`允许工具与普通文档的开发修改，但继续核验冻结材料。贡献者无需为每个PR重算发布清单；维护者在审核合并内容后发布新软件版本。开发与发布检查的区别见[验证说明](../docs/VALIDATION.md)。

## 维护者发布流程

1. 审查差异、许可与来源，排除私有记录、凭证、本地配置、缓存和out/。工具输入清单与真实作品不属于发布示例。
2. 运行上方开发检查与测试；更新CHANGELOG.md、CITATION.cff、数据卡及首页的软件版本说明。基准或协议版本不因普通软件改动而改变。
3. 将审核后的文件加入Git暂存区（特别是新增或删除文件），检查`git diff --cached`。命令以Git文件集合限定发布范围，同时读取工作区实际内容。
4. 预览清单，再明确写入清单：

```bash
python -B -X utf8 cnwb.py manifest --version 1.0.5
python -B -X utf8 cnwb.py manifest --version 1.0.5 --write
git add tools/manifests/source.json tools/manifests/release.json
python -B -X utf8 cnwb.py check --release
python -B -X utf8 -m unittest discover -s tests
```

上例版本号应替换为待发布版本。默认只预览；`--write`只更新两个维护清单，保留冻结材料清单和公开成绩来源哈希，更新工具哈希及发布文件哈希。命令要求Git，禁止未纳入Git的发布文件、常见私有文件及题库/协议/模板变化；公开成绩快照变化也会被拒绝，需另行审核来源与发布范围。哈希检查不是自动安全审计，提交前仍应审核全部暂存差异。

提交并发布前确认所有改动（包括清单）已暂存且工作区一致；发布后检查GitHub CI的四组结果。复用第三方材料或方法应说明具体来源，遵守对应许可。
