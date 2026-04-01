# The Impact of SIPOC on Process Reengineering and Sustainability of Enterprise Procurement Management in E-Commerce Environments Using Deep Learning

## 论文信息
- 标题：The Impact of SIPOC on Process Reengineering and Sustainability of Enterprise Procurement Management in E-Commerce Environments Using Deep Learning
- 作者：Hui Zhang, Lijun Fan, Min Chen, Chen Qiu
- 年份：2022
- 会议/期刊：Journal of Organizational and End User Computing
- 用户搜索主题：电商点击率影响因素
- 原文链接：https://www.igi-global.com/viewtitle.aspx?TitleId=306270&isxn=9781668462638

## 中文详细解读
这篇论文的核心研究对象是电商环境下的企业采购管理流程重构，而不是电商点击率或点击率影响因素。就用户所关心的“电商点击率影响因素”而言，论文正文片段未提供关于用户点击行为、曝光、转化漏斗、商品展示、推荐排序、广告创意、价格敏感度、评价数量等点击率相关变量的分析，因此不能据此提炼点击率影响因素。

从正文可明确看出，论文主要做了四件事：
1. 在理论层面，引入SIPOC模型、深度学习和企业采购管理相关理论，强调采购是企业管理中的核心环节，采购效率会影响企业生产经营效率。
2. 在案例层面，选取中国一家电力科研企业D Electric作为样本，梳理其采购管理现状与问题。
3. 在算法应用层面，用深度学习进行风险预警分析，并用Python的Scrapy框架识别与企业采购需求相似的供应商，辅助供应商筛选。
4. 在流程优化层面，用SIPOC模型对材料备案、耗用方案、进口材料申报与供应链管理流程进行优化。

就论文发现而言，D Electric存在一系列采购管理问题。正文明确提到：采购管理流程“复杂且模糊”，此前采购“目标不清、思路模糊”，供应商与企业之间“缺乏统一整体”，采购管理流程“与企业总体战略无关”。此外，ERP自动生成的物料需求“不能直接传递给报关部门”，从而可能造成“信息遗漏、信息错误或信息转换错误”。进口材料还有明显延迟问题，表中给出的延期情况包括“10到15天”与“超过15天”的多次发生。这些都说明论文重点关注的是采购流程效率、信息传递准确性、供应链协同和风险控制，而非前台电商用户行为。

深度学习在文中的作用主要有两类：
第一类是供应商识别。论文写到，所提方法使用Python语言的Scrapy框架，为D Electric识别具有相似采购需求的供应商，并进一步获得企业近期经营、评价、信誉和材料质量等信息，以“准确和快速”找到满足需求的供应商，同时减轻采购人员工作量。
第二类是风险预警。论文从多种预警指标中选了10个指标作为研究样本，对D Electric进行风险预警分析。正文明确指出，2017年总资产净利率和营业收入增长率为负，说明该年企业经营和管理水平较差；2017到2019年的模拟输出结果均为1，表示企业“很可能发生风险危机”，而采购管理流程被认定为导致危机的原因之一，具体表现为“流程繁琐、物料延误严重、出错概率大”。

SIPOC模型在文中的作用是采购流程再造。论文指出，针对D Electric在进口材料管理中容易混淆“海关备案号”和“企业备案号”的问题，作者利用SIPOC模型优化了物料备案与耗用方案。与传统方案相比，优化后增加了CMS内容管理系统，通过持续强化CMS功能，建立D Electric中企业备案号与海关备案号之间的对应关系，实现“专用化”和“一对一对应”。

在供应链和管理流程方面，SIPOC优化还体现在进口材料申报流程被拆分为两个阶段：先让材料进入海关，再核验材料信息并分类海关备案号，最后再送往D Electric。论文认为，这样可避免海关备案号与企业备案号不一致或不规范的问题，也更符合供应商与客户整体一致性的原则，并且让相关人员贯穿全过程，以便第一时间解决问题。论文还特别说明，虽然“先入关后报企业信息”表面看起来会占用海关时间，但实际上海关备案号本身有管理流程，该做法有利于标识对应关系和物流动态跟踪，实现对备案记录的正确跟踪。

如果从“电商点击率影响因素”这个用户主题来评估本文价值，这篇论文只能间接提供一个很弱的启发：在电商环境中，深度学习可被用于企业运营过程中的识别、预警和流程优化；但这种启发并不能外推为点击率建模结论，因为论文既没有CTR任务定义，也没有点击数据、用户特征、商品特征、会话特征、推荐位置特征或评估指标。关于深度学习模型的具体结构、训练数据来源、特征构成、10个预警指标的完整名称、供应商筛选准确率、优化前后绩效提升幅度等，论文片段均未明确说明。

## 结合主题的实际运用
基于正文，这篇论文可支持的实际运用主要集中在企业采购管理，而不能直接支持“电商点击率影响因素”分析。可支持的应用包括：
1. 采购流程诊断：可用于识别企业采购流程中的复杂、模糊、与战略脱节、信息传递不畅等问题。
2. 供应商识别与信息收集：可利用文中提到的Scrapy框架抓取并整理潜在供应商的公司名称、业务范围、近期经营、评价、信誉和材料质量等信息，以辅助采购方筛选供应商。
3. 风险预警：可借助深度学习对企业经营风险进行预警，特别是识别采购管理流程可能对企业财务管理和经营稳定性造成的风险。
4. 进口材料备案与申报流程优化：可通过SIPOC模型和CMS建立企业备案号与海关备案号的一对一对应关系，减少编号混淆、信息错误和流程不规范问题。
5. 供应链流程重构：可将进口材料流程划分为“材料入海关—信息核验与备案号分类—送达企业”这样的分阶段流程，以提高一致性和跟踪能力。
6. 物流与记录跟踪：可用于加强材料物流动态追踪和备案记录对应管理。

与用户主题“电商点击率影响因素”相关的可支持应用：
- 论文未明确说明。
- 论文未提供点击率预测、CTR特征工程、推荐排序、广告投放优化或用户点击行为分析的可落地方法。
- 若要把本文用于点击率场景，正文没有直接证据支持。

## 证据摘录
- However, there are a series of problems in its management process. For example, the purchasing management process is complex and fuzzy. Prior procurements had unclear objectives, vague ideas, and suppliers separate from the enterprise (lack of a unified whole). The purchasing management process is not related to the enterprise’s overall strategy.
- The proposed method uses the Scrapy framework of Python language to identify suppliers with similar procurement requirements for D Electric... It also provides the evaluation, reputation, and material quality of enterprises on this supplier. This method can liberate the workload of buyers, as well as accurately and quickly find suppliers that meet the requirements of D Electric.
- In a variety of early warning indicators, 10 indicators were selected as the research sample... the net profit margin of total assets and growth rate of operating income in 2017 are negative, indicating that D Electric has poor management and low management levels...
- The data from 2017 to 2019 shows that the output value of risk prediction is 1. This indicates a very likely risk crisis of D Electric. The procurement management process of the enterprise is one cause of the crisis. The procurement process is cumbersome, the material delay is serious, and the error probability is large.
- Unlike traditional material filing and consumption, the content management system (CMS) is added to the optimized SIPOC model... This process achieves “dedicated” and “one-to-one correspondence” effects.

## 依据说明
“详细解读”中关于论文主题是采购管理而非点击率，来自标题、摘要及正文对D Electric采购流程、风险预警和SIPOC优化的描述。关于D Electric存在流程复杂、目标不清、与战略脱节、信息错误、材料延期等问题，直接由正文片段3及片段2支撑。关于深度学习用于供应商识别和风险预警，由正文片段3中Scrapy识别供应商、10个预警指标、2017-2019输出结果为1等内容支撑。关于SIPOC用于备案号对应、CMS加入、供应链流程分阶段优化，由正文片段3支撑。关于“可支持的实际运用”中的采购流程诊断、供应商信息收集、风险预警、备案与供应链流程优化，均有正文直接支撑。关于用户主题“电商点击率影响因素”的任何变量、模型、业务应用，正文未明确说明，因此相关部分均明确写为‘论文未明确说明’。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
