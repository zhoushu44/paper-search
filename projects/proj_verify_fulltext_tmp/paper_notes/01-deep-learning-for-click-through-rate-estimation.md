# Deep learning for click-through rate estimation

## 论文信息
- 标题：Deep learning for click-through rate estimation
- 作者：W Zhang, J Qin, W Guo, R Tang, X He
- 年份：2021
- 会议/期刊：arxiv.org
- 用户搜索主题：CTR verify
- 原文链接：https://arxiv.org/pdf/2104.10584

## 中文详细解读
这篇论文是一篇关于CTR estimation（点击率估计）的综述，核心目标是回顾深度学习模型在CTR估计任务中的发展脉络、关键模块与自动化设计方向。根据给定正文，可作如下解读：

1. 论文对CTR估计任务的基本定义
正文指出，CTR estimation是多种个性化在线服务中的核心功能模块，包括在线广告、推荐系统和网页搜索。训练数据通常表示为表格形式，经过特征工程处理后，每条样本被表示为multi-field categorical data（多域类别型数据），标签是二值的：点击为1，未点击为0。模型训练被表述为二分类问题，并采用交叉熵损失。

2. 论文对CTR模型发展趋势的总体判断
正文明确用两个维度概括CTR模型的发展：
- feature engineering complexity（特征工程复杂度）
- model capacity（模型容量）
早期模型受限于算力，更多依赖人工设计更好的特征，同时使用简单模型；之后逐渐引入更复杂的深度结构，以减少人工特征工程的负担；而更新的趋势则是重新重视“可学习的特征工程”，因为单纯依靠更复杂的深模型已遇到性能瓶颈。因此，正文认为新的方向是“复杂模型 + 可学习特征工程”的结合。

3. 从浅层模型到深层模型的演化逻辑
正文从LR开始说明：LR部署快、效率高，是基础模型，但它难以直接捕捉有判别力的组合特征。比如多个字段组合后可能共同提升某广告的点击概率，因此人工构造cross features曾是重要途径。POLY2给每个二阶组合特征分配权重，但参数空间达到O(m^2)，而且在稀疏数据下效果可能较差，因为很多交互特征很少或从未共同出现，导致参数难以正确估计。

GBDT也被提到可自动学习特征交互，但正文指出它难以并行训练，而且只能利用全部可能交互中的一小部分，因此在大规模场景中的性能和应用受限。

FM是浅层模型向更强交互建模过渡的重要代表。正文给出FM通过为每个特征分配k维embedding向量，使特征间组合效应能够通过embedding内积灵活表达。如果某一组合特征与点击概率正相关，则其内积会被学习为正；负相关则会被学习为负。正文还提到FFM是FM的重要扩展，但给定片段未完整展开其机制，因此更细节部分论文片段未明确说明。

4. 深度CTR模型中的显式特征交互学习
正文第二段重点讨论了深度CTR中的feature interaction operators（特征交互算子），并列举了几类代表方式：

(1) Product类算子
NFM提出在embedding层和深度网络之间加入bi-interaction layer，用线性交互与DNN的非线性交互结合，正文认为它比已有深模型更易训练。正文还指出，DNN最终可以学习任意函数，因此仅靠DNN并不能在理论上保证各阶特征交互都被建模。

Cross Network针对这个问题，在每一层显式执行feature crossing，使交互阶数随层深增加且由网络深度决定。正文同时指出原始Cross Network使用向量乘法，表达能力有限；Cross Network V2进一步将cross vector替换为cross matrix，以提高表达能力。CIN被描述为受Cross Network启发、用于捕捉有界阶数特征交互的更有效模型。KPNN和PIN分别利用kernel product和micro-net来建模特征交互。

(2) Convolutional算子
正文介绍了CCPM、FGCNN和FiGNN。CCPM通过卷积、池化和非线性激活反复堆叠生成任意阶特征交互，但其问题是对field order敏感，因此只能学到部分相邻特征之间的交互。FGCNN通过加入recombination layer改进CCPM，以建模非相邻特征，并把CNN生成的新特征与原始特征一起用于最终预测。正文明确说FGCNN验证了CNN生成特征能够扩展原始特征空间，并降低现有深结构的优化难度。FiGNN则把多域类别数据看成一个全连接图：字段作为节点，字段间交互作为边，再通过图传播建模特征交互；其出发点是认为简单、无结构的字段组合方式对复杂交互的建模能力有限。

(3) Attention类算子
AFM在FM基础上增加attention network，使不同特征交互对预测的贡献可不同。交互向量先送入attention network得到分数，再经softmax归一化后用于加权预测。FiBiNET利用SENET学习特征重要性，再用双线性函数学习特征交互。AutoInt利用带残差连接的multi-head self-attention显式建模不同阶特征交互，并且可通过attention weights提供可解释预测。InterHAt将transformer网络与多层attention aggregation结合，在正文中被描述为具有较高训练效率、性能可比，并能解释不同特征交互的重要性。

5. DNN在深度CTR模型中的角色
正文明确区分了single tower和dual tower两种结构：
- single tower：特征交互层与DNN串联；优点是能够有效捕捉高阶特征交互，但低阶交互信号可能在后续DNN中消失。
- dual tower：特征交互层与DNN并联；显式交互层负责低阶交互，DNN隐式学习高阶交互，二者输出共同生成最终预测。

正文进一步评价：single tower模型如NFM、PIN具有更强建模能力和更复杂结构，但通常会遭遇bad local minima，并且严重依赖参数初始化。dual tower模型如Wide & Deep、DeepFM、DCN、DCN V2、xDeepFM、AutoInt+，其中DNN部分可视为对交互层残差信号的补充，因此训练更稳定、性能也更好。

6. 自动化架构设计（AutoML/NAS）在CTR中的应用
正文第三段主要讨论三类自动化搜索：embedding size search、feature interaction search、whole architecture search。

(1) Embedding维度搜索
一些方法做hard selection，即为每个特征只选一个embedding维度。正文提到某类方法用soft selection layer将二值搜索空间放松为连续空间，再通过预设阈值过滤不重要维度，但这个阈值在实践中难调，可能导致次优性能。PEP改进为阈值可从数据中自适应学习。与之相对，AutoEmb和AutoDim采用soft selection，对候选维度embedding按可学习权重加权求和，并通过可微搜索算法训练。AutoDim针对feature fields分配不同embedding大小，AutoEmb则为单个特征搜索不同embedding大小。

(2) 特征交互搜索
正文指出自动发现有效特征交互很有价值。AutoFIS枚举全部特征交互，用一组architecture parameters表示各交互的重要性，并借助梯度下降与GRDA得到稀疏解，使不重要交互被自动过滤。但正文也明确指出它将交互函数限制为inner product。受PIN启发，SIF和AutoFeature进一步考虑“不仅找重要交互，还要找合适的交互函数”。SIF面向matrix factorization场景，在不同数据集上自动设计交互函数；其搜索空间包含micro space（逐元素MLP）和macro space（五种线性代数运算）。AutoFeature则为每对field之间的交互使用不同架构的micro-network，通过进化算法和Naive Bayes tree在五种预定义操作中搜索。

正文还指出，AutoFIS和AutoFeature都无法建模高阶特征交互，因为它们需要预先枚举所有可能交互。为避免这种低效枚举，AutoGroup提出生成一些feature groups，使给定阶数的交互有效；每个特征初始以0.5概率被选入任一组，并通过Gumbel-Softmax从CTR监督信号中学习这些概率。BP-FIS则进一步从用户粒度识别重要特征交互，比以往方法有更细的选择粒度；它通过Bayesian variable selection构建生成模型，并用高效随机梯度变分Bayes优化。

(3) 整体架构搜索
AutoCTR从现有CTR架构中抽象出MLP、dot product和FM等代表性结构作为virtual blocks，并构建两层层级搜索空间：外层是块之间的连接关系，内层是各块的超参数细节，搜索算法采用进化算法。AMER则同时搜索两部分：一是从序列特征（用户行为）中提取序列表征的结构，搜索空间包括normalization、activation和不同层类型（卷积、循环、池化、attention）；二是自动探索非序列特征间的交互，通过逐步增加交互阶数、保留验证集表现最好的交互。

7. 对用户行为建模的结论性表述
给定片段中没有完整展开用户行为模型章节细节，但在摘要与总结中，正文明确说：在拥有丰富用户历史的大平台上，deep behavior models是重要视角；同时，attention mechanism、memory networks或retrieval-based approaches可以有效学习用户行为历史表示，从而进一步提升预测性能。至于这些方法的内部细节、适用条件、具体对比结果，给定片段中论文未明确说明。

8. 论文的整体结论
正文总结认为：
- 借助feature-interaction operators，深度模型更擅长捕捉多域类别数据中的高阶组合特征模式，从而获得更好的预测性能；
- 借助attention、memory networks、retrieval-based approaches，可以更有效表示用户行为历史并提升性能；
- 自动化架构设计方法开始进入CTR领域，用于embedding、交互和整体结构搜索。关于未来展望的完整内容，给定片段末尾不完整，因此论文未明确说明。

## 结合主题的实际运用
基于正文，这篇论文可支持的实际运用或业务含义主要包括：

1. 用于CTR estimation任务本身
正文明确指出CTR estimation是在线广告、推荐系统、网页搜索等个性化在线服务中的核心模块，因此该综述可用于梳理这些场景下点击率预测模型的选型与演进。

2. 支持多域类别型日志数据的建模
正文说明CTR数据通常来自历史日志，经特征工程后形成multi-field categorical data，并以二分类方式训练。因此该论文可用于分析这类日志表格数据上，如何从LR、FM发展到深度CTR模型。

3. 支持特征交互建模方案的比较与验证
如果业务重点是验证不同click-through rate estimation方法对特征交互的建模能力，正文提供了多类显式交互模块：product、convolution、attention、cross network、graph propagation等，并指出各自的特点与局限，例如：
- LR难以直接刻画组合特征；
- POLY2在稀疏数据下参数难估；
- Cross Network可显式控制交互阶数；
- FGCNN可生成新特征并扩展原始特征空间；
- AutoInt、InterHAt可提供一定可解释性。

4. 支持模型结构选择
正文对single tower和dual tower给出较直接的业务含义：
- 若更关注高阶交互建模能力，可关注single tower；
- 若更重视训练稳定性与综合性能，可关注dual tower，因为正文指出dual tower训练更稳定、性能更好。

5. 支持自动化模型设计
对于需要减少人工试错的CTR建模工作，正文列出了自动化搜索方向：
- embedding size search；
- feature interaction search；
- whole architecture search。
这些内容可用于支持在CTR系统中自动选择embedding大小、筛选重要交互、甚至自动生成整体架构。

6. 支持含用户历史行为的CTR场景
正文摘要和总结中明确提到，大平台若拥有丰富用户历史，可以采用deep behavior models；attention、memory networks、retrieval-based approaches可有效学习用户行为历史表示并提升预测性能。更具体的工业部署方式、线上指标收益、资源成本，论文片段未明确说明。

7. 支持可解释性交互分析
正文指出AutoInt可通过attention weights提供可解释预测，InterHAt也能解释不同特征交互的重要性。因此在需要分析“哪些特征交互更重要”的CTR验证任务中，这类模型具有直接参考价值。

除上述内容外，例如具体数据集、实验数值、A/B测试效果、部署细节、延迟与吞吐要求等，论文未明确说明。

## 证据摘录
- Click-through rate (CTR) estimation plays as a core function module in various personalized online services, including online advertising, recommender systems, and web search etc.
- The development of the models could be summarized into two aspects which are feature engineering complexity and model capacity.
- Cross Network solves this problem using a cross network to apply feature crossing at each layer explicitly. Thus the order increases at each layer and is determined by layer depth.
- As shown in Fig. 3(b), it places the feature interaction layer and DNN parallelly. The feature interaction layer is responsible for explicitly capturing low-order interactions while the high-order ones are captured implicitly by the DNN.
- AutoFIS automatically identifies and then selects important feature interactions for factorization models.

## 依据说明
“详细解读”中关于CTR任务定义、数据形式、交叉熵损失、模型发展趋势，主要由正文片段1支撑；关于显式特征交互算子（NFM、Cross Network、CIN、CCPM、FGCNN、FiGNN、AFM、AutoInt、InterHAt）以及single tower/dual tower角色划分，主要由正文片段2支撑；关于embedding搜索、特征交互搜索、整体架构搜索（AutoFIS、AutoGroup、AutoCTR、AMER等），主要由正文片段3支撑；关于用户行为历史可由attention mechanism、memory networks、retrieval-based approaches学习并提升性能，来自正文片段1摘要和正文片段3总结。凡涉及更细的实验效果、具体实现细节、未来工作完整内容、部署成本、指标收益等，给定正文未展开，因此均标注为“论文未明确说明”。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
