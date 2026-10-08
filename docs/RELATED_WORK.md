# 参考创作测评基准

核查日期：2026-10-08。以下是原项目资料，不采用第三方榜单转述。借鉴仓库结构、方法报告和可复现流程；未复制第三方题库、作品、评语、代码或分数。各项目的分数不可直接与CNWB比较。

| 基准 | 原项目特征 | 本版采用的组织方式 | 保留的CNWB差异 |
|---|---|---|---|
| [WritingBench](https://github.com/X-PLUG/WritingBench) · [论文](https://arxiv.org/abs/2503.05244) | 写作任务、任务相关判据、生成/评审/聚合工具分别提供 | 题库、请求模板和算术工具分目录，记录生成条件 | 中文叙事专轨；固定T1—T6及每题三维；保持SJ6分级，不采用其10分尺度 |
| [EQ-Bench Creative Writing v3](https://github.com/EQ-bench/creative-writing-bench) | 多轮创作、rubric及成对比较组合，生成设置与评委说明公开 | 独立标识生成轮次/评委、方法与偏差说明 | 不移植Elo/Glicko；当前仍是六维加权描述指数，不新增收费比较 |
| [EQ-Bench Longform Writing](https://github.com/EQ-bench/longform-writing-bench) | 规划、反思、角色、分章写作与整体评审，多阶段代码/模板 | 清楚列出阶段职责、交付范围和重评边界 | CNWB规划题只评价设定/提纲；不宣称测过完整长篇实写 |
| [Short Story Creative Writing](https://github.com/lechmazur/writing) | 同一创作简报上的成对比较，顺序交换、多评委、覆盖率与不确定性说明 | 缺席和完成题数可追踪，评委差异与测量范围分开报告 | 不复制其故事元素或统计模型；未给CNWB历史单轮成绩生成置信区间 |

CNWB选择提供通用离线接口，不把供应商账户配置、评测预算或私人响应带入开源包。当前公开参考集和未来私有测试集应分别管理，透明协议不能替代新题目对未见能力的检验。

污染管理参考：[LiveBench](https://arxiv.org/abs/2406.19314)采用持续更新任务降低固定公开测试材料的污染风险；[改写样本研究](https://arxiv.org/abs/2311.04850)说明仅改写不能可靠消除测试泄露。CNWB尚未建立新的私有测试集，本版不宣称完成此项措施。
