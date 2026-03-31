# A comprehensive survey on advertising click-through rate prediction algorithm

## 论文信息
- 标题：A comprehensive survey on advertising click-through rate prediction algorithm
- 作者：J Bai, X Geng, J Deng, Z Xia, H Jiang
- 年份：2025
- 会议/期刊：cambridge.org
- 用户搜索主题：电商点击率影响因素
- 原文链接：https://www.cambridge.org/core/journals/knowledge-engineering-review/article/comprehensive-survey-on-advertising-clickthrough-rate-prediction-algorithm/C11C54F5D365D280A58CE051D9B52DE6

## 中文详细解读
论文片段主要围绕广告点击率预测中的若干关键影响因素建模方式展开，核心可归纳为以下几类：

1. 不同特征交互的重要性不同，且这种差异会影响CTR预测结果。
正文指出，NFM模型在pair-wise interaction层中“所有交叉特征的权重都为1”，即没有区分不同交叉特征对结果的影响程度；AFM则通过在pair-wise interaction层与输出层之间加入attention net，学习不同交叉特征对预测目标的重要性，其中a_ij表示交互特征的重要程度。根据这一表述，论文明确支持这样的理解：在电商点击率问题中，特征之间不是“只要发生交互就同等重要”，而是“不同交互项对点击预测的贡献不同”。

2. 用户历史行为与当前候选广告/商品之间的相关性，是CTR提升的重要建模对象。
正文在DIN部分明确说明：用户行为特征，也就是用户过去购买或点击过的商品特征，是该模型最重要的特征之一；如果用户历史商品与当前商品相关，则该商品可能更符合用户偏好，因此应推荐给该用户。DIN通过activation unit，对“历史商品记录”与“待推荐商品”逐一做pairwise interaction并计算相关程度，再将这些相关性权重用于用户兴趣表示。由此可见，论文把“历史行为—当前商品相关性”作为点击率预测中的关键因素之一。

3. 用户兴趣不是静态汇总，而是与当前候选广告相关的动态表达。
DIN中的用户兴趣表示v_U(A)由候选广告向量v_A和用户历史行为嵌入序列共同决定，并通过加权求和生成；其中权重a(e_j, v_A)由前馈神经网络产生。这意味着论文强调的不是简单地把用户历史行为平均汇总，而是根据“当前候选广告”重新激活不同历史行为的重要性。正文还特别指出，为保留用户兴趣强度，attention score直接作为最终权重，不做softmax归一化。

4. 注意力机制在CTR预测中具有关键作用，尤其适合处理特征交互与兴趣选择问题。
正文直接提到：一些深度学习模型已经能够从用户行为中自动提取用户兴趣，并成功使用attention mechanism从历史行为中选择用户感兴趣的item，以提高CTR预测性能；同时，文献还发现“大多数CTR预测模型都可以视为适用于特征交互的一般注意力机制”，因此“attention mechanism plays a key role in CTR prediction models”。据此，论文片段将注意力机制定位为CTR预测中的核心方法之一。

5. 细粒度属性关系也是影响CTR预测的重要对象。
正文提到MIAN用于综合提取各种细粒度特征之间的潜在关系，例如用户画像中的gender、age和occupation；该模型包含多交互层进行细粒度特征交互学习，并使用基于Transformer的模块在不同特征子空间中提取多种用户行为表示。由此可见，论文认为用户画像中的细粒度属性及其相互关系，也是CTR预测中的重要影响因素。

6. 特征本身的重要性不能被忽略，仅靠内积或Hadamard积构造交叉特征存在局限。
正文引用FiBiNET相关内容时指出，当前通过特征组合进行CTR预测的工作，主要使用特征向量的inner product或Hadamard product计算交叉特征，但这种方法忽视了特征本身的重要性，因此进一步提出了动态学习特征重要性的做法。基于此，论文支持这样的解释：不仅“特征如何交互”重要，“单个特征本身有多重要”也会影响点击率建模效果。

7. 图结构信息、属性依赖和多关系路径被用于进一步挖掘用户意图与商品意图。
正文在图模型相关部分提到：传统方法把item attributes当作ID特征，从而忽略结构信息与属性之间的依赖；HIEN则基于构造的attribute graph，利用自底向上的tree aggregation考虑属性依赖，并通过hierarchical attention mechanism同时捕捉用户和商品在不同属性上的意图。这里反映出论文所强调的另一类影响因素：不仅有“用户做过什么”，还有“属性之间如何关联”“用户/商品意图在不同属性维度上如何表达”。

8. CTR预测面临两类关键稀疏性挑战：特征稀疏与行为稀疏。
正文明确指出，近年来CTR预测中的两个主要技术方向是feature interaction modeling和user interest mining，但它们分别遭遇关键挑战：一是很多特征出现频率低，导致feature sparsity，且特征交互模型严重依赖特征共现；二是user interest mining需要丰富行为数据才能刻画多样兴趣，但许多用户行为序列很短，导致behavior sparsity。由此可见，论文把“稀疏性问题”视为影响CTR预测效果的核心障碍之一。

9. 为缓解稀疏问题，论文片段强调了属性图、协同图、多兴趣建模等增强方式。
DG-ENN中构建了user/item attribute graph和collaborative graph，用于缓解特征稀疏和行为稀疏问题；Deminet则显式建模multiple user interests，并通过multi-dependency-aware heterogeneous attention和self-supervised interest learning减少行为序列中的噪声信号。这些内容表明：点击率预测的影响因素不仅在于原始特征和行为本身，还在于能否利用图结构、协同关系、多兴趣和降噪机制更充分地表达用户与商品。

10. 在模型评价层面，论文片段强调AUC和Logloss是最常用指标。
正文写到，现有研究提出了多种评价指标，其中最常用的是AUC和Logloss。AUC衡量随机选取的正样本是否比负样本排名更高，对类别不平衡不敏感；Logloss衡量预测值与真实标签之间的距离，越小越好。这部分不是点击率影响因素本身，但说明论文在讨论CTR任务时，如何判断上述建模因素是否真正提升了效果。

11. 数据层面，论文片段表明Criteo、Avazu、Amazon是常用公开数据集，而私有数据常来自广告平台、社交媒体和电商网站。
这说明论文所讨论的方法被用于广告平台、电商站点等CTR预测场景，但关于各数据集具体包含哪些电商点击率影响变量，正文片段未明确说明。

总体而言，仅基于给定正文，论文将电商点击率影响因素主要落实为：不同特征交互的重要性、用户历史行为与当前商品的相关性、用户动态兴趣表达、细粒度属性关系、特征本身的重要性、属性依赖与用户/商品意图，以及特征稀疏和行为稀疏等问题。至于哪些具体业务字段在电商中最重要、各因素的量化贡献大小、不同模型在电商数据上的绝对优劣，论文片段未明确说明。

## 结合主题的实际运用
基于正文，该论文对“电商点击率影响因素”主题可支持的实际运用或业务含义主要包括：

1. 可用于指导电商CTR模型把“用户历史点击/购买商品”作为关键输入。
正文明确指出，DIN最重要的特征之一是用户行为特征，即用户过去购买或点击过的商品特征；如果历史商品与当前商品相关，则更可能符合用户口味。因此，在电商场景中，可以将用户历史行为序列与当前候选商品之间的相关性作为建模重点。

2. 可用于支持“按候选商品动态激活用户兴趣”的推荐/广告排序方式。
根据DIN公式与描述，用户兴趣表示是相对于当前候选广告A动态生成的，而非固定用户向量。这意味着在电商点击率估计任务中，可以针对每个候选商品分别计算用户兴趣权重，以改进排序或曝光决策。

3. 可用于支持引入注意力机制，对不同特征交互赋予不同权重。
AFM说明交叉特征的影响程度不同；DIN说明历史行为与候选商品的相关性权重不同；文中还明确指出attention mechanism在CTR prediction中起关键作用。因此，电商CTR建模可采用注意力机制来识别更重要的用户-商品、属性-属性或行为-商品关系。

4. 可用于支持挖掘用户画像中的细粒度属性关系。
正文提到MIAN可提取gender、age、occupation等细粒度特征的潜在关系。对应到电商点击率任务，可将用户画像中的细粒度属性交互纳入建模。至于电商中具体应采用哪些字段，正文未明确说明。

5. 可用于支持同时关注“特征本身的重要性”和“特征交互的重要性”。
FiBiNET相关表述指出，仅通过inner product或Hadamard product计算交叉特征会忽视特征自身重要性。因此，电商CTR任务中，不仅可以建模商品、用户、上下文之间的交互，还可以评估各特征自身的重要程度。具体业务字段或实现细节，正文未明确说明。

6. 可用于支持解决电商场景中的特征稀疏和短行为序列问题。
正文明确提出CTR预测存在feature sparsity和behavior sparsity两类挑战，并介绍DG-ENN通过用户/商品属性图和协同图缓解这两个问题。因此，对于电商中低频特征多、很多用户历史行为短的问题，可考虑图增强嵌入方式。具体在电商平台如何部署，正文未明确说明。

7. 可用于支持多兴趣建模与行为降噪。
Deminet被描述为显式建模multiple user interests，并通过heterogeneous attention和self-supervised interest learning减少行为序列噪声。这说明在电商CTR任务中，可以将用户兴趣视为多元而非单一，并尝试降低无关历史行为对点击预测的干扰。

8. 可用于支持模型评估时重点使用AUC和Logloss。
正文明确指出AUC和Logloss是最常用的评价指标，因此在电商点击率估计实验中，可以优先用这两个指标比较不同影响因素建模方式是否有效。

9. 可用于支持在公开数据集和平台私有数据上开展CTR实验。
正文说明Criteo、Avazu、Amazon是常见公开数据集，私有数据来自广告平台、社交媒体和电商网站。因此，对于电商点击率研究，该论文可支持“在公开数据集或平台自有数据上验证模型”的任务方向。但各数据集与电商业务的对应细节，正文未明确说明。

10. 关于业务层面的更具体落地，如预算分配、广告创意优化、渠道投放策略、价格因素影响等，论文未明确说明。

## 证据摘录
- “In the pair-wise interaction layer, the weights of the cross features of the NFM model are all 1... while AFM can learn the different influence degrees of different cross features on the results.”
- “one of the most important features of the DIN is user behavior features, that is, the product features that the user has purchased or clicked on in the past. If many of the user’s historical products are related to the current product, then the product may be in line with the user’s taste”
- “The activation unit structure makes a pairwise interaction between each record in the historical commodity and the commodity to be recommended, and calculates the correlation degree.”
- “Literature (Cheng & Xue, 2021) found that most CTR prediction models can be regarded as a general attention mechanism suitable for feature interaction, so attention mechanism plays a key role in CTR prediction models.”
- “these approaches encounter key challenges: (1) Feature sparsity... and (2) user interest mining requires extensive behavioral data... but many users have short behavior sequences, leading to sparse behavior data.”

## 依据说明
“详细解读”中关于不同特征交互影响不同，主要由AFM段落支撑；关于历史行为与当前商品相关性、动态用户兴趣表达、activation unit、是否做softmax，由DIN公式（15）及其文字说明支撑；关于注意力机制在CTR中的关键作用，由“most CTR prediction models...”和“attention mechanism plays a key role...”直接支撑；关于细粒度属性关系，由MIAN对gender、age、occupation等细粒度特征关系的描述支撑；关于特征本身重要性不能忽视，由FiBiNET相关表述支撑；关于属性依赖、用户/商品意图和图结构，由HIEN、DSGL相关内容支撑；关于特征稀疏和行为稀疏两大挑战及DG-ENN缓解方式，由正文片段3直接支撑；关于多兴趣和行为降噪，由Deminet描述支撑；关于AUC、Logloss和常用数据集，由5.2与5.3节内容支撑。‘实际运用’部分中，能够支持的应用仅限于正文明确提到的CTR预测、推荐/广告排序、历史行为建模、注意力加权、细粒度特征交互、图增强缓解稀疏、多兴趣建模以及AUC/Logloss评估。凡涉及更具体的电商字段选择、线上部署方案、预算/创意/价格/渠道策略等，论文未明确说明。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
