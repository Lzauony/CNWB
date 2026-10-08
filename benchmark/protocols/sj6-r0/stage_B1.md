B1：本题固定三维各判1—4或明确null。数字4须在本轮完成优秀证明，不能因后续还有复审而宽松入围；四级未建立时按实际实现判1—3。

## 输出、空值与证据复用

输出单个裸JSON对象，按output_contract.schema和template填写，不回显input或output_contract。固定标识、三项材料哈希、阶段、指定维度必须逐字保持；只评指定维度。
grade填本阶段允许的整数或null；null只表示明确无法评价，unassessable_reason说明原因，数字等级时该原因留空。delivery必须判delivered/incomplete/non_delivery；非交付各维grade为null，不补零。expression.state必须独立判controlled/localized/substantial/not_assessable；数字等级不能同时声称本维表达无法评价。
模板中的〈待填写：…〉必须替换。普通文本无内容用""，数组无项目用[]，对象按模板保留子键。程序仅对说明性文本和数组的缺键或null补为空值，不生成论证，不补等级、枚举判断、标识、哈希、阶段或维度。补空会记录规范化轨迹，必要论证缺失另记内容诊断。
每维evidence集中保存连续原文和局部作用；数组从0编号。relations和issues用evidence_indices引用本维证据，无需重复抄引文。同一证据可服务多条联系和问题，跨维复用仍各自解释本维作用。
relations可同时列within_answer和source_continuation/revision_comparison/source_transformation等多条联系。每条分别说明link，并引用两端证据；正文联系至少两处不重叠answer证据，来源联系至少source、answer各一处。无联系证明时写[]；集中成就仍检查全文限制。
given只写题给与源文边界；achievement写本次成就；mechanism写整体作用并引用证据编号；scope写成就作用范围；above_three只补足相对于成熟有效实现的质量差别，并引用已有证据编号；不得重抄机制或以“有作用”作为差别，低于四级可空。T6在given区分题给，在achievement说明不易互换的自身特点，在mechanism说明其功能，不另抄一套新意字段。
issues逐项写有据问题，impact说明该问题如何影响本维及已申报成就，alternative只写有据替代解释，没有则留空。limitation只总结最强限制对已申报成就的具体影响及剩余升档依据，可引用issues和证据编号；无有据限制时简述已核对范围，不虚构缺点。证据、问题及全文限制各写一次，不在其他字段重复完整论证。
无需在模板增加已移除的重复表或总评分。若意外增加字段，接收端将未知字段按原路径、键名和值完整另存附录，不计分、不进入B2；指定维度集合不适用此容错，多维或缺维仍失败。
compliance只记录需单独说明的任务条件；无补充事项可写[]，不表示全部合规。影响等级的问题在相关维度issues说明，不另扣总分。
提交时不加代码围栏或前后说明。接收端容忍包住全部JSON的单层json代码围栏、外围空白与BOM。同一对象中的重复键仅在值及JSON类型递归完全相同时合并，并记录路径和次数；冲突重复键仍失败。先完整解析全部响应，再规范化；不从混杂文字中截取JSON，不修复截断、追加内容、错误类型或非法枚举。
字段空白、错引、失效证据编号、论证重复、等级或理由冲突只作内容诊断，不重抽、不自动改等级。格式接收成功不证明文学论证有效。

B1的grade只填整数1—4或null；只填写本轮schema字段。