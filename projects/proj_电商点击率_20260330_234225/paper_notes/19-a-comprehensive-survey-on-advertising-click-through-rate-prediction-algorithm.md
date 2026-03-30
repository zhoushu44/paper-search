# A comprehensive survey on advertising click-through rate prediction algorithm

## 论文信息
- 标题：A comprehensive survey on advertising click-through rate prediction algorithm
- 作者：J Bai, X Geng, J Deng, Z Xia, H Jiang
- 年份：2025
- 会议/期刊：cambridge.org
- 用户搜索主题：电商点击率
- 原文链接：https://www.cambridge.org/core/journals/knowledge-engineering-review/article/comprehensive-survey-on-advertising-clickthrough-rate-prediction-algorithm/C11C54F5D365D280A58CE051D9B52DE6

## 中文详细解读
这篇论文片段主要围绕广告点击率（CTR）预测中的若干深度学习建模方向展开，重点涉及注意力机制、用户兴趣建模、特征交互、图增强方法，以及数据集与评价指标。

1. 关于AFM对特征交互的改进
正文指出，NFM模型在pair-wise interaction layer中，各交叉特征的权重都为1，因此“没有考虑不同特征对结果的影响程度”。AFM（attentive factorization machines）在pair-wise interaction layer与output layer之间增加了attention net，用注意力分数a_ij来表示交互特征v_i⊙v_j对预测目标的重要性。论文还指出，若直接把注意力分数当作参数学习，则“无法估计训练数据中从未共同出现过的特征交互”的注意力，因此AFM采用多层感知机来参数化该注意力分数，且其注意力网络结构是“单全连接层加softmax输出层”。这说明AFM的核心贡献是在特征交互层面引入可学习的重要性分配，以替代统一权重。

2. 关于DIN对用户兴趣的建模方式
正文将DIN描述为在Embedding & MLP基础上加入activation unit以提升CTR的模型，并强调它“从实际应用和业务观察出发”进行改进。DIN最重要的特征之一是用户行为特征，即用户过去购买或点击过的商品特征。论文明确表示：如果用户历史商品与当前商品相关，则该商品可能符合用户偏好，因此应推荐给用户。其activation unit会对“历史商品记录”和“待推荐商品”做逐对交互，并计算相关程度。公式(15)表明，用户对候选广告A的兴趣表示，是由候选广告向量v_A与历史行为embedding序列e_1到e_H共同决定的加权和，其中权重由前馈神经网络a(e_j, v_A)输出。正文还特别指出，输入不仅包含历史行为向量与候选广告向量，还包含二者的Hadamard积，以帮助显式关联建模；同时，为保留用户兴趣强度，最终权重不做softmax归一化。这表明DIN强调候选广告与历史行为之间的细粒度相关建模，而不是仅做统一汇总。

3. 注意力机制在CTR中的总体地位
正文明确提到，近年来一些能够“自动提取用户兴趣”的深度学习模型取得成功，这些工作利用注意力机制从用户历史行为中选择感兴趣项目，以提高CTR预测器性能。并且有文献认为“大多数CTR预测模型可以看作适用于特征交互的一般注意力机制”，因此注意力机制在CTR预测模型中“发挥关键作用”。从该表述看，论文将注意力机制视为CTR预测中的重要统一建模思想之一，既可以用于特征交互，也可以用于用户兴趣提取。

4. 关于更复杂的交互与表示学习模型
正文列举了多个模型方向：
- MIAN：用于“综合提取各种细粒度特征之间的潜在关系”，例如用户画像中的性别、年龄、职业等；其包含多交互层和基于Transformer的模块，以在不同特征子空间中抽取多种用户行为表示。
- DIFM：可“根据不同输入样本自适应学习给定特征的不同表示”。
- AIM：与DIFM思路相近。
- CAN：提出Co-Action作为新的特征交互方式；当用户与物品存在关联时，Co-Action处理后的数据与原始数据一起送入深度学习模型，以提升CTR预测。
- FiBiNET：针对当前特征组合主要依赖内积或Hadamard积、忽略特征自身重要性的问题，提出动态学习特征重要性的方式，正文明确提到其使用SENET结构。关于FiBiNET后续细节，正文片段被截断，因此论文未明确说明其完整机制。

5. 关于图学习与稀疏问题
正文指出，近年来CTR预测中两个常见技术方向是“特征交互建模”和“用户兴趣挖掘”，但这两类方法分别面临两个关键挑战：
(1) 特征稀疏：很多特征出现频率低，而特征交互模型又依赖特征共现；
(2) 行为稀疏：用户兴趣挖掘需要足够丰富的行为数据，但很多用户行为序列很短。
为解决这些问题，论文介绍了DG-ENN。该模型通过用户（物品）属性图和协同图来缓解特征稀疏与行为稀疏，并通过divide-and-conquer和受curriculum learning启发的organized learning策略来优化embedding。这里可以看出，论文认为图结构增强是一种针对CTR稀疏性问题的重要解决思路。

6. 关于意图与属性依赖建模
正文介绍HIEN时指出，传统方法常把物品属性视为ID特征，从而忽略结构信息与属性之间的依赖；此外，在从用户-商品交互中挖掘兴趣时，现有模型忽略了具有不同属性的用户意图和商品意图。HIEN通过构建属性图，并基于自底向上的树聚合来考虑属性依赖，再结合层次注意力机制捕获不同属性下的用户与商品意图。这说明论文片段进一步把CTR建模从简单行为相关性推进到“属性依赖+层次意图”的粒度。

7. 关于多兴趣和降噪
正文还提到Deminet显式建模多重用户兴趣，并通过multi-dependency-aware heterogeneous attention和self-supervised interest learning减少行为序列中的噪声信号。这表明在用户行为序列较复杂或有噪声时，论文所综述的方法强调通过更细粒度的注意力与自监督方式改善兴趣表达。

8. 关于数据集使用情况
正文在数据集部分明确指出，现有广告CTR预测研究中常用的数据集包括Criteo、Avazu和Amazon，这三者是“最常用的公共数据集”。专有数据集则来自广告平台、社交媒体平台和电商网站，例如Alibaba Cloud、Tencent、Facebook、Alibaba、Taobao等。论文同时指出，公共数据集比专有数据集更常用，可能原因是“更容易获取”。但正文片段没有给出各数据集的字段结构、规模差异或适用任务细分，因此这些内容论文未明确说明。

9. 关于模型评价指标
正文指出，CTR预测模型常用的评价指标中，AUC和Logloss最常见。
- AUC：表示随机选取一个正样本，其排序高于随机选取负样本的概率；是ROC曲线下面积；“只考虑预测实例的顺序”，因此“对类别不平衡问题不敏感”；上界为1，越大越好。
- Logloss：衡量每个样本预测分数与真实标签之间的距离；下界为0，越小越好；正文还给出了带L2正则项的公式，其中包含真实标签y_i、预测值ŷ_i、样本总数N、正则权重λ和参数集Θ。
- RelaImpr：正文指出其作用是“根据离线性能估计在线性能的相对提升”，并用于与baseline比较；同时也称RI-AUC。但该指标完整公式在片段中被截断，因此具体表达式论文未明确说明。

10. 关于论文整体性质
从题目与各段内容看，这是一篇综述性论文，目的之一是比较不同CTR预测算法的优缺点。正文提到Table 7总结了基于浅层交互模型、DNN、CNN、RNN和GNN的CTR预测算法的优缺点，并称这有助于研究者选择合适方法。但由于表格内容未出现在片段中，各类模型的具体优缺点论文片段未明确说明。

## 结合主题的实际运用
基于正文，这篇论文对“电商点击率”主题可支持的实际运用主要体现在以下几个方面：

1. 支持电商广告/商品推荐中的CTR建模思路选择
正文明确提到DIN利用用户过去点击或购买过的商品特征，与当前候选商品做相关性计算，以判断该商品是否符合用户口味。这可直接支持电商场景下的点击率预测与广告/商品排序任务，即使用用户历史行为与候选商品之间的相关性来建模点击概率。

2. 支持基于用户历史行为的个性化推荐
正文说明DIN的activation unit会对用户历史商品与当前候选商品逐对交互，并输出权重，再形成用户对当前广告的兴趣表示。这说明论文可支持一种实际用法：在电商场景中，根据用户历史浏览、点击、购买记录，对当前候选商品进行个性化打分，以改进CTR预测。

3. 支持在特征交互中引入差异化权重
正文表明AFM能够学习不同交叉特征对预测结果的不同影响程度，而不是像NFM那样统一设为1。这可用于电商CTR系统中对特征交互进行加权建模，例如更关注对点击更重要的交互特征。至于具体应如何部署到某种业务系统，论文未明确说明。

4. 支持从历史行为中筛选兴趣项目
正文指出，近年来若干CTR模型通过注意力机制从用户历史行为中选择用户感兴趣的项目，以提升CTR预测性能。这对于电商点击率任务的业务含义是：当用户历史行为很多时，可以通过注意力机制突出与当前候选商品更相关的历史行为，提高预测效果。

5. 支持处理电商CTR中的稀疏问题
正文明确指出CTR任务面临特征稀疏和行为稀疏两大问题，而DG-ENN通过用户/物品属性图与协同图来缓解这两类问题。对于电商场景，这意味着该论文可支持在用户行为较短、商品属性稀疏或交互稀少时，考虑图增强embedding来提升CTR预测。至于具体电商平台实施条件、图构建细节和工程成本，论文片段未明确说明。

6. 支持多兴趣与噪声抑制场景
正文提到Deminet显式建模多重用户兴趣，并通过异构注意力和自监督兴趣学习减少行为序列噪声。因此在电商用户兴趣复杂、行为信号噪声较大的场景中，这类方法可用于提升CTR预测鲁棒性。具体适用人群划分、线上实验收益幅度，论文未明确说明。

7. 支持模型评估方案制定
正文明确指出AUC和Logloss是CTR预测最常用的评价指标，因此在电商CTR建模实践中，可使用AUC和Logloss对模型进行离线评估；RelaImpr可用于估计相对改进。但RelaImpr的具体计算方式在片段中不完整，论文未明确说明。

8. 支持数据集选择上的研究参考
正文指出Criteo、Avazu、Amazon是最常用的公共数据集，专有数据还包括来自广告平台、社交平台和电商网站的数据。对于电商CTR研究，这意味着可优先参考这些公共数据集进行模型验证。不过具体到哪一个最适合“电商点击率”这一用户主题，正文未明确说明。

## 证据摘录
- In the pair-wise interaction layer, the weights of the cross features of the NFM model are all 1... while AFM can learn the different influence degrees of different cross features on the results.
- one of the most important features of the DIN is user behavior features, that is, the product features that the user has purchased or clicked on in the past... The activation unit structure makes a pairwise interaction between each record in the historical commodity and the commodity to be recommended, and calculates the correlation degree.
- In recent years, some deep learning models that can automatically extract user interests from user behavior have achieved great success... the attention mechanism is used to select items of interest to users from historical behaviors to improve the performance of CTR predictors.
- these approaches encounter key challenges: (1) Feature sparsity... and (2) user interest mining requires extensive behavioral data... many users have short behavior sequences... Guo et al. proposed the dual graph enhanced embedding module... A user (item) attribute graph and a collaborative graph are proposed in DG-ENN to alleviate the feature sparsity and behavior sparsity problems.
- Among these, the most commonly used evaluation indicators are AUC and Logloss.

## 依据说明
“详细解读”中关于AFM、DIN、注意力机制关键作用、DG-ENN解决稀疏问题、HIEN/Deminet等内容，主要由正文片段2和片段3支撑；关于数据集与评价指标，主要由正文片段3支撑；关于论文为综述并比较不同算法优缺点，由片段3中‘Table 7 offers a comprehensive summary...’支撑。‘实际运用’中关于电商场景下利用历史点击/购买行为建模候选商品CTR，直接由DIN相关描述支撑；关于用AUC、Logloss做评估，由片段3支撑；关于图方法缓解稀疏问题，也由片段3支撑。凡涉及具体工程部署方式、收益幅度、表7具体优缺点明细、FiBiNET完整机制、RelaImpr完整公式、数据集字段与规模差异等，正文片段均未完整给出，因此这些部分均应视为‘论文未明确说明’。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
