# 数据交换与材料绑定

所有文本按UTF-8解码后，以完整Unicode文本重新编码UTF-8计算SHA-256。保留CRLF、BOM、外围空白及标题，不做Unicode归一化。读取作品文件必须使用`read_bytes().decode('utf-8')`，不能通过自动换行转换改变作品。

## 作品记录

```json
{
  "schema_version": 1,
  "benchmark_id": "cnwb-story32-v1",
  "id": "my-model-round-1",
  "model_id": "my-model",
  "works": [
    {"task_id": "A15", "text": "完整作品正文", "sha256": "正文的64位十六进制SHA-256"}
  ]
}
```

id标识一次生成轮次，不能只用模型名覆盖多轮。task_id为短ID，例如A15；一轮每题最多一份作品，未交付可缺席或保留空白文本及其真实哈希。工具允许任意题目子集，但严格完整总分仍需全部计划题目。`synthetic:true`专用于技术样例。

可以添加generation元数据（模型精确ID、思考档位、日期、参数、结束原因等）；附加运行元数据可保留在本地，不将私有元数据送给评委。

## 评审记录

```json
{
  "schema_version": 1,
  "benchmark_id": "cnwb-story32-v1",
  "id": "my-model-judge-a-r1",
  "generation_id": "my-model-round-1",
  "judge_id": "judge-a",
  "protocol_id": "sj6-v1",
  "revision": 1,
  "reviews": [
    {"task_id": "A15", "answer_sha256": "对应作品哈希", "B1": {}, "B2": null}
  ]
}
```

上述B1空对象仅表示结构位置，实际B1必须使用动态请求中`output_contract.schema`定义的完整对象，不能只填grade。stage、材料哈希、完整任务标识（如CNWB-S32-A15）和协议常量保持逐字一致；外层task_id使用A15短ID。B2只在B1有入围维度时提供，且指定维度集合必须完全匹配。

`cnwb.py receive`产出的是接收证据包，包含`review`、原始文本、容错和附录。组装B1/B2时取其中`review`，不是整个证据包。可选`projection`如已保存，计分时必须与本版投影函数的重算结果完全相同，不能当作可信分数输入。

交换schema位于tools/schemas/；它描述外围JSON类型，不能代替精确的动态SJ6 schema、哈希和阶段检查。`score`按真实作品重新构造schema并执行SJ6投影。

## 分数与覆盖率

`score`输出all32/prose28/planning4三个scopes，各有n/planned/complete/total、dimensions和excluded_tasks。每维保留n/planned/mean/score/distribution。排除原因区分missing_review、awaiting_B2、unassessable、incomplete、non_delivery和delivery_conflict；missing_works另列生成缺席。

明确null、缺失、bool、浮点或数字字符串不能转换成整数等级。数值分布仅用于描述，不用于调整分数或重抽。API调用数0表示工具执行本身，不推断实际模型评审的成本。

`average`输出两个独立评委的均分及judge_coverage；不输出伪造的共同题目n。`rank`保留未舍入分数和并列名次，null最后且rank=null。不同评委集合不能放入同一排名文件。

## 更新约定

新作品用新generation_id，新评委用新judge_id，修订同评委记录增加revision并用新evaluation_id。工具是无状态的离线计分器，无法验证目录之外是否还有更高revision；保存与选用责任属于调用方。记录应独立保存，不覆盖已存在的评审文件。修改题文或协议须新版本，并说明实际变化。
