# 离线使用流程

Python 3.10+，无需pip安装。以下命令在本包根目录执行，Windows PowerShell与Linux/macOS均可使用。所有命令API 0；输出只允许写入包内`out/`或包外新路径，既有文件不覆盖。

## 1. 核验与测试

```bash
python -B -X utf8 cnwb.py check
python -B -X utf8 -m unittest discover -s tests
python -B -X utf8 cnwb.py tasks
```

`check`核验完整文件清单/哈希、32题及六维覆盖数，复算合成样例。测试不需要真实评语，也不调用模型。

## 2. 构造候选请求

```bash
python -B -X utf8 cnwb.py prompt --task A15 --output out/generation-A15.json
```

输出system/user消息数组，与冻结候选消息一致。外部调用程序应只发送这些消息及预先记录的生成参数，不发送评委协议、观察项、身份或旧分。模型输出按原始Unicode文本保存，保留CRLF、BOM、标题及外围空白；正常结束与截断需要由调用方区分。

本包没有HTTP客户端或队列。用户可使用自己的供应商SDK、CLI或本地模型；生成模型ID、日期、档位、参数及结束状态需记入独立运行元数据。模板不是完整HTTP请求，不保证任意供应商支持原生JSON schema。

## 3. 构造B1并接收响应

```bash
python -B -X utf8 cnwb.py prompt --task A15 --answer examples/answer.txt --output out/B1-request.json
python -B -X utf8 cnwb.py receive --task A15 --answer examples/answer.txt --response examples/B1.json --output out/B1-received.json
```

`examples/answer.txt`和B1只是合成格式演示，不能作为真实作品质量示例。`receive`返回`review`规范对象、原始响应文本、原始/规范化哈希、容错轨迹、额外字段附录和机械诊断。组装评审记录时使用`review`字段；接收证据留在本地，不直接发布该文件。

保留第一份符合材料、结构及阶段接收契约的响应。语义诊断、低分、null和排名变化不触发重抽。技术重试范围需由新实验计划提前固定；本工具不自动重试。

## 4. 独立B2

从规范B1取grade=4且有交付的维度，仅这些维度构造B2。本演示三个维度均入围：

```bash
python -B -X utf8 cnwb.py prompt --task A15 --answer examples/answer.txt --stage B2 --dimensions T1 T3 T6 --output out/B2-request.json
python -B -X utf8 cnwb.py receive --task A15 --answer examples/answer.txt --response examples/B2.json --stage B2 --dimensions T1 T3 T6 --output out/B2-received.json
```

B2消息只包含原题、源文、作品、指定维度与协议，不包含B1对象。示例B2故意覆盖低分、高分与null路径，不代表文学判断。B1非4维度不得送B2；正式计分时完整检查入围集合。不需要B2时省略B2字段。

## 5. 复算与排序

```bash
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --output out/demo-score.json
python -B -X utf8 cnwb.py rank out/demo-score.json --output out/demo-ranking.json
python -B -X utf8 cnwb.py rank out/demo-score.json --scope planning4 --metric T3 --output out/demo-planning-T3.json
```

真实记录按[数据格式](DATA_FORMAT.md)组装；`score`不信任已有投影或总分，而从B1/B2重新核验和计算。严格口径默认：未全部完整则总分null。可用完整作品口径需明确选择：

```bash
python -B -X utf8 cnwb.py score --generation examples/generation.json --evaluation examples/evaluation.json --missing-policy available-complete-works --missing-reason "Predeclared available-work analysis" --output out/demo-available.json
```

实际缺题与原因始终单列。无对应观测的维度保持null，不重分配六维权重。请把该口径与完整32题结果分别报告。

## 6. 两评委平均

```bash
python -B -X utf8 cnwb.py average --left out/judge-a-score.json --right out/judge-b-score.json --output out/average-score.json
python -B -X utf8 cnwb.py rank out/average-score.json --output out/average-ranking.json
```

先用两个独立评委的记录各运行`score`生成上述输入。两者必须使用同一generation及其内容哈希，且judge_id不同。双方覆盖率和缺题保留；不另取共同题重算。`rank`只能混合相同评委轨道或相同双评组合，不把不同评委当作模型差异。

## 运行元数据建议

保存模型实际返回ID、请求模型ID、供应商、评委ID/版本、生成轮次、日期、思考档位、temperature/top_p/max_tokens、种子（若支持）、结束原因、实际用量与费用。未知值写null或明确unreported，不推测。账户标识、请求头、密钥和传输调试数据不得放入公开记录。改变题文、协议或主要生成条件时新增版本/实验ID，不覆盖旧结果。
