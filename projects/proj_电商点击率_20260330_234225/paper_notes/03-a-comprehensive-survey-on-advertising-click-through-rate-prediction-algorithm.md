# A comprehensive survey on advertising click-through rate prediction algorithm

## 论文信息
- 标题：A comprehensive survey on advertising click-through rate prediction algorithm
- 作者：J Bai, X Geng, J Deng, Z Xia, H Jiang
- 年份：2025
- 会议/期刊：cambridge.org
- 用户搜索主题：电商点击率
- 原文链接：https://www.cambridge.org/core/journals/knowledge-engineering-review/article/comprehensive-survey-on-advertising-clickthrough-rate-prediction-algorithm/C11C54F5D365D280A58CE051D9B52DE6

## 中文详细解读
该论文片段展示的是一篇关于广告点击率预测算法的综述性总结，重点围绕“特征交互建模”“用户兴趣建模”“图增强方法”“数据集与评估指标”几个方面展开。

1. 关于注意力机制在CTR预测中的作用
正文指出，AFM是在NFM基础上的改进。NFM在pair-wise interaction layer中，对交叉特征的权重都设为1，没有考虑不同特征对结果影响程度不同；AFM则在pair-wise interaction layer和output layer之间加入attention net，为不同交互特征学习不同的重要性权重。正文明确给出：a_ij表示交互特征v_i⊙v_j的attention score，用来表示该交互特征对预测目标的重要性。论文还指出，若直接把attention score当参数学习，则对于训练数据中从未共同出现过的特征交互，注意力分数无法估计，因此AFM使用多层感知机对attention score进行参数化，且其注意力网络结构是“单全连接层+softmax输出层”。

2. 关于DIN对用户兴趣的建模方式
正文认为DIN是在基础模型（Embedding & MLP）上加入activation unit来学习用户兴趣分布，以提升CTR。DIN的重要特征之一是用户行为特征，即用户过去购买或点击过的商品特征。论文给出的逻辑是：如果用户历史商品与当前商品相关，则当前广告可能更符合用户偏好，因此可推荐该广告。DIN的activation unit会对“历史商品序列中的每一条记录”和“当前待推荐商品”做两两交互，并计算相关度；其输出是相关性权重。用户兴趣表示为历史行为embedding的加权和，权重由历史行为商品与当前广告之间的相关性决定。正文特别强调：为了保留用户兴趣强度，DIN中attention score直接作为最终权重系数，不做softmax归一化。此外，正文还说明该前馈神经网络的输入不仅包括历史行为向量与候选广告向量，还包括它们的Hadamard product，这有助于显式关联建模。

3. 关于注意力机制在CTR模型中的整体地位
正文明确说，近年来一些能自动从用户行为中提取用户兴趣的深度学习模型取得了很大成功，这些工作中通常使用注意力机制从历史行为中筛选用户感兴趣的项目，从而提高CTR预测器性能。还引用文献指出，大多数CTR预测模型都可以看作一种适用于特征交互的一般注意力机制，因此注意力机制在CTR预测模型中起关键作用。

4. 关于更复杂的特征交互与兴趣提取模型
正文列举了多个代表性模型：
- MIAN：用于综合提取多种细粒度特征之间的潜在关系，例如用户画像中的性别、年龄、职业。模型包括多交互层用于细粒度特征交互学习，以及基于Transformer的模块，用于在不同特征子空间中抽取用户行为的多种表示。
- DIFM：可根据不同输入样本，自适应学习给定特征的不同表示。
- AIM：正文只说“有相似思想”，未进一步展开，论文未明确说明其详细机制。
- CIN：其特征交互方法与Deep&Cross中的cross network相似，每次特征交互都使用输入变量；不同于FM仅做变量的两两交互，CIN将所有变量融合成矩阵进行特征交互。
- CAN中的Co-Action：被描述为一种新的特征交互方式；当用户与物品之间存在关联时，将Co-Action处理后的数据与原始数据同时输入深度学习模型，以提高CTR预测。
- FiBiNET：针对现有方法主要用内积或Hadamard product计算交叉特征、但忽略特征自身重要性的问题，提出利用SENET结构动态学习特征重要性，并结合双线性交互。由于正文片段截断，FiBiNET后续细节论文片段未完整说明。

5. 关于图方法解决CTR中的稀疏问题
正文指出，近年来CTR预测中两个普遍技术是特征交互建模和用户兴趣挖掘，但它们分别面临关键挑战：
- 特征稀疏：许多特征出现频率很低，而特征交互模型高度依赖特征共现；
- 行为稀疏：用户兴趣挖掘需要大量行为数据，但很多用户行为序列较短，导致行为数据稀疏。
为解决这两个问题，DG-ENN提出了dual graph enhanced embedding module，并可兼容多种CTR预测模型。该方法引入用户（物品）属性图和协同图，分别用于缓解特征稀疏和行为稀疏问题。为高效学习这些图，正文提到其embedding通过两种设计良好的学习策略优化：divide-and-conquer与受curriculum learning启发的organized learning。

6. 关于意图与属性依赖建模
正文指出传统方法将物品属性视为ID特征，忽略了结构信息与属性之间的依赖；在从用户-商品交互中挖掘兴趣时，也忽略了不同属性下的用户意图和商品意图。HIEN针对这一问题提出：在构建的属性图上基于自底向上的树聚合来考虑属性依赖，并用层次注意力机制同时捕捉不同属性下的用户意图与商品意图。其核心是用图和树结构表示属性与商品（用户）的关系，并通过聚合探索属性依赖，再与注意力机制结合以揭示不同属性层次下的意图。

7. 关于Deminet
正文说Deminet显式建模CTR任务中的多重用户兴趣。为减少行为序列中的噪声信号，使用了multi-dependency-aware heterogeneous attention和self-supervised interest learning。正文未进一步展开其结构细节。

8. 关于算法优缺点的综述结论
正文在Discussion部分明确指出，不同广告CTR预测算法各有独特优势与挑战，并称Table 7对浅层交互模型、DNN、CNN、RNN、GNN类CTR算法的优缺点做了综合总结。但由于表格内容未给出，具体到每类模型的详细优缺点，论文片段未明确说明。

9. 关于数据集
正文指出现有广告CTR预测研究常用多种数据集，其中最常见的公开数据集是Criteo、Avazu和Amazon。私有数据集则来自广告平台、社交媒体平台和电商网站，例如Alibaba Cloud、Tencent、Facebook、Alibaba、Taobao。正文还指出，公开数据集比私有数据集使用更广，原因“可能”是更易获取。除此之外，各数据集的具体字段、规模、预处理方式，论文片段未明确说明。

10. 关于评估指标
正文明确指出，CTR预测模型最常用的评估指标是AUC和Logloss。
- AUC：表示随机抽取一个正样本比随机抽取一个负样本排名更高的概率，即ROC曲线下面积；它只考虑预测实例排序，对类别不平衡问题不敏感；上界为1，越大越好。
- Logloss：衡量每个样本预测分数与真实标签之间的距离；下界为0，越小越好。正文给出了带L2正则项的Logloss公式，其中y_i和ŷ_i分别是真实标签与预测值，N是训练样本总数，λ是L2正则权重，Θ是模型参数集合。
- RelaImpr：正文说其用于在离线性能基础上估计在线性能的相对提升，并用于与baseline模型比较，也称RI-AUC；还指出随机猜测的AUC为0.5。但由于公式后半部分被截断，具体表达式论文片段未完整说明。

总体上，从该综述片段可见，论文认为CTR预测的发展重点在于：通过注意力机制增强特征交互表达、通过行为序列建模更精确提取用户兴趣、通过图结构缓解特征与行为稀疏问题，并通过AUC与Logloss等指标进行评估。不过若要进一步比较具体模型的实验表现、精度排名、工业部署效果等，当前片段未明确说明。

## 结合主题的实际运用
基于正文片段，这篇论文对“电商点击率”主题可支持的实际运用主要体现在以下几个方面：

1. 可用于电商广告/商品推荐中的CTR建模方案选型
正文明确讨论了AFM、DIN、MIAN、DIFM、CAN、FiBiNET、DG-ENN、Deminet、HIEN等模型及其侧重点，因此可用于在电商点击率估计任务中，按问题类型进行方法选择：
- 如果业务重点是区分不同交叉特征的重要性，可参考AFM；
- 如果业务重点是利用用户历史点击/购买行为与当前候选商品之间的相关性来建模兴趣，可参考DIN；
- 如果业务中存在用户画像等细粒度特征关系建模需求，可参考MIAN；
- 如果业务面临特征稀疏、短行为序列导致的行为稀疏，可参考DG-ENN；
- 如果需要显式建模多重兴趣并减少行为噪声，可参考Deminet；
- 如果希望考虑属性依赖与不同属性下的用户/商品意图，可参考HIEN。

2. 可支持电商场景中的用户兴趣建模
正文明确说DIN将用户过去购买或点击的商品作为关键行为特征，并根据这些历史商品与当前候选广告之间的相关性加权生成用户兴趣表达。这意味着在电商点击率任务中，可将用户历史点击或购买序列作为重要输入，构建“当前候选商品相关的动态兴趣表示”。

3. 可支持对历史行为较短、数据稀疏用户的建模改进
正文指出CTR中的两个关键难点是特征稀疏和行为稀疏，尤其很多用户行为序列较短。DG-ENN通过用户/物品属性图与协同图缓解这两个问题，因此对于电商CTR中“新用户或低活跃用户行为少”的情况，论文提供了可参考的解决方向。

4. 可支持电商CTR模型评估体系的建立
正文明确指出AUC和Logloss是最常用的评价指标。因此在电商点击率估计实验或模型对比中，可以依据论文采用AUC与Logloss作为核心离线评估指标。RelaImpr被用于估计相对提升，但公式细节在片段中不完整，因此若要直接实施其计算，论文片段未明确说明完整方法。

5. 可支持数据集选型与基准实验设计
正文说明Criteo、Avazu、Amazon是常见公开数据集，且公开数据集更常用。因此如果是开展电商点击率算法研究或离线验证，该论文片段可支持优先考虑这些公开数据集作为对比基准。至于Amazon数据集在该文中是否专门对应电商点击场景，正文只列为常用公开数据集，未进一步细分其具体任务设置。

6. 可支持“注意力机制是CTR关键模块”的业务判断
正文直接指出注意力机制在CTR预测模型中起关键作用，且多个模型都通过注意力从历史行为中选择与当前目标更相关的项目。因此在电商CTR系统中，若目标是提高对用户即时兴趣或细粒度特征关系的刻画能力，论文支持优先关注带注意力机制的CTR模型。

7. 工业部署、线上实验收益、训练成本、推理延迟
这些内容在片段中没有展开。若问这些模型在电商业务中的部署门槛、实时性、线上提升幅度、资源消耗，论文未明确说明。

## 证据摘录
- In the pair-wise interaction layer, the weights of the cross features of the NFM model are all 1... while AFM can learn the different influence degrees of different cross features on the results.
- one of the most important features of the DIN is user behavior features, that is, the product features that the user has purchased or clicked on in the past.
- The activation unit structure makes a pairwise interaction between each record in the historical commodity and the commodity to be recommended, and calculates the correlation degree.
- two prevalent techniques for CTR prediction are feature interaction modeling and user interest mining... these approaches encounter key challenges: (1) Feature sparsity... and (2) user interest mining requires extensive behavioral data... many users have short behavior sequences
- Among these, the most commonly used evaluation indicators are AUC and Logloss.

## 依据说明
对AFM、DIN、注意力机制关键作用、DG-ENN缓解稀疏问题、HIEN/Deminet/MIAN等模型方向的解读，主要由正文片段2和片段3支撑；其中AFM与DIN的机制、DIN不做softmax归一化、注意力用于筛选历史兴趣项目，均直接来自片段2。对CTR中“特征稀疏、行为稀疏”及DG-ENN用双图缓解问题的说明，来自片段3。对常用数据集Criteo、Avazu、Amazon以及公开数据集更常用的总结，来自片段3的Datasets部分。对AUC、Logloss、RelaImpr等评估指标的说明，来自片段3的Model evaluation indicators部分。关于算法优缺点的总体判断，只能依据片段3中“Different ad click-through rate prediction algorithms exhibit unique advantages and challenges”这一概括；但表7具体内容未展示，因此各类模型详细优缺点论文未明确说明。关于工业部署效果、线上收益、资源开销、具体实验结果对比等，正文片段未明确说明。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
