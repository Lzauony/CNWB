# 合成格式样例

所有generation/evaluation/B1/B2均为发布工具构造的技术夹具，文本明确标注“不是模型作品”。不存在作者身份、真实模型输出、人工金标或真实文学评语。

generation.json含32条合成作品；evaluation.json每题三维B1等级3，用于验证总分60及规划无T4。expected-score.json是离线算术预期。

answer.txt与B1.json/B2.json对应A15的独立演示，B1三个维度均4，B2分别1、5、null，用于测试覆盖/降级/空值路径。它们不是evaluation.json中A15的实测补评，也不能据此修改网站分数。

合成评分文字没有文学证据效力；测试可以产生机械诊断，诊断不触发自动改级。实际文学评审应遵守完整协议的举证责任。
