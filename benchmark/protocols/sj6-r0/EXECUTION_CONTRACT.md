## 生成与评审分开接收

生成阶段的实际HTTP请求不带response_format。候选只交纯正文，程序将完整响应原样放入本地text字段；任务号、材料哈希和阶段由请求包在发送前绑定。标题、引号、CRLF、BOM及外围空白不剪裁；不尝试从JSON或代码围栏中抽取正文。包装或篇幅偏离属于交付/内容诊断，不能借此重抽。只有确认正常结束的响应可接收；空白内容记non_delivery，不补成有作品。local_artifact_schema用于保存后的作品对象，不是候选输出schema。

评委仍输出单个JSON。先完整解析，再将相同值且递归JSON类型完全相同的重复键合并；1、1.0、true不视为相同类型。不修复冲突重复键、截断、多个JSON或对象后追加文字。每个被合并的键保存路径、操作及值哈希，原始answer.txt保留所有重复项。

未知字段在任意已知对象位置移入supplements.extra_fields，每项保留parent_path、完整键名和完整原值（包括对象和数组）。validation.json与supplements.json保留附录；评分投影和B2请求只接规范化对象。$.dimensions是指定维度集合，不移除额外维度以求通过。关键等级、枚举、哈希和身份仍不得缺失、错填或转换；拼错grade为score只会留下附录且因grade缺失失败。缺少说明字段延续r11的空值容错和内容诊断。

## 共享限流冷却

story32_sj6_r0_runtime.StageRunner是新的可调用阶段运行器，必须在新事件上下文中使用。事件plan.json先冻结routes、concurrency、request_sha256s、max_attempts_per_stage、max_api_attempts、retry_backoff_seconds及timeout_seconds；真实执行另需api_execution_authorized=true、source_files包含本运行器及传输与协议全部依赖，以及execute_api=True。没有内置任务队列，不会复用旧事件授权。

HTTP Retry-After支持整数秒和HTTP日期；等待值取本地退避与服务器要求的较大值，不把服务器较长等待截成30秒。无效、负数或缺失头使用事件原定退避。429、503和带有效Retry-After的响应更新同路由共享截止时间，只延长不缩短；重新发送前及新阶段首次发送前都检查冷却。错误流中的429/503同样适用，无头时用预定退避。

路由按provider、base_url、model及固定provider_endpoint分组；同一组的不同本地id共享冷却与并发上限。不同模型/端点不会因局部限流全部停摆。route_cooldowns.json保存截止时刻，retry.json保存状态码、原始头、解析秒数、本地退避和最终not_before；进程重启继续遵守。等待每30秒重新检查。事件runner.lock保证一个进程拥有调度权，进程内多个任务共享同一冷却对象；已发出的在途请求不能撤回。

最多尝试数、总预算和停止条件由新事件固定。401/402/403/404/400阻断路由；请求体漂移停止，未知在途请求先核查。完整评分或finished_incomplete事件不能重启。第一份接收有效响应即保留；证据不足、重复论证、等级矛盾等诊断不能触发重试。重试发送完全相同请求，不添加旧分或错误反馈诱导改分。

## 原生schema验证与模式选择

能力依据见CAPABILITY_REVIEW.md。原生schema的范围必须包括精确provider、base_url+/chat/completions、model、OpenRouter上游端点及本次完整schema。supports_json_schema=true或一条文档链接不足以启用。

story32_sj6_r0_capability.prepare_probe离线生成独立技术探针请求；实际发送必须在另行授权并冻结的能力事件中完成，探针不是作品评分。verify_probe要求实际请求逐字相等、流正常结束、返回模型相符、裸JSON未经容错即符合完整schema，之后生成包含请求/响应哈希和证据事件的验证记录。本次仅有模拟测试，没有真实探针记录。材料哈希等常量或schema变更后，旧验证不能自动覆盖新schema；未来可另行研究并核定可复用的schema特征验证方案。

prepare_request默认auto：生成选text；评委仅在上述精确验证通过时选json_schema，否则明确记录native_unverified_json_object。显式指定json_schema而无有效验证直接报错；已经发送的原生请求失败后不自动降级。OpenRouter原生请求固定only端点、require_parameters=true及allow_fallbacks=false。实际输出始终经本地校验，原生通过不代表文学论证正确。

DeepSeek当前/chat/completions的response_format只列text/json_object。strict函数调用、Responses API属于不同接口契约，不能假装当前接口已经支持；如后续采用，须另建适配器并验证流解析、阶段投影和材料绑定。

## 离线验收与历史边界

格式、冷却与原生能力门槛由SJ5 r12迁入新的SJ6命名空间，连接SJ6判据；不是继续旧事件。父版的历史接收回放曾保留122份有效响应、恢复13份格式失败，本版不据此回填或重新评分。新命名空间通过离线模拟检查相同接收及运行行为。

题库、候选消息、篇幅、三维、评分权重及字段集合保持；文学三四边界已变化。输出模板把grade放在各维证据与理由之后，JSON键顺序不作为接收门槛。新诊断仅作待查提示，不能自动裁定错分或触发语义重试。

新事件真实执行仍须明确授权并冻结完整源码依赖，包括story32_sj6_boundaries.py及既有来源依赖；此构建API 0。schema或材料常量变化后重新核定精确原生能力，旧SJ5能力记录不自动覆盖SJ6。
