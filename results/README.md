# 公开榜单汇总

`published-leaderboard.json`是2026-10-08公开网站的汇总快照，保留原值精度。来源及SHA-256见[来源清单](../tools/manifests/source.json)。包含23个模型、24个生成配置和两位评委的汇总，不含真实逐篇评语或逐题等级。

[仓库首页](../README.md#测评榜单)展示按两位评委总分各占50%平均的全库排行。生成配置单列；Grok / 两评委、HY4 / MiMo和Kimi K3 / MiMo使用31题完整作品口径，覆盖率在表内显示。缺项不填零，不重新计算双方共同题目。

在根目录运行：

```bash
python -B -X utf8 cnwb.py leaderboard
python -B -X utf8 cnwb.py leaderboard --output out/published-ranking.json
```

第一条打印首页表格；第二条保存含六维均分、原精度总分、名次、来源评审ID与双方覆盖率的JSON。`cnwb.py check`校验中英文首页表格与快照一致。快照更新时，维护者核验来源后同步表格和发布清单。

这是网站汇总结构，不是`score`的generation/evaluation输入。复算逐篇判断需要完整作品和评审记录；仅有汇总不足以复核全部等级。工具不调用模型；合成示例只在examples/，不混入实测排行。
