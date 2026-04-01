# Personalized recommendation system based on knowledge embedding and historical behavior

## 论文信息
- 标题：Personalized recommendation system based on knowledge embedding and historical behavior
- 作者：Bei Hui, Lizong Zhang, Xue Zhou, Wen Xiao, Yuhui Nian
- 年份：2021
- 会议/期刊：Applied Intelligence
- 用户搜索主题：电商点击率影响因素
- 原文链接：https://link.springer.com/article/10.1007/s10489-021-02363-w

## 中文详细解读
该论文聚焦于个性化推荐系统，核心问题是传统协同过滤（CF）在推荐场景中会因为用户-物品交互稀疏和冷启动问题而性能受限。论文指出，为了缓解这些问题，通常会引入知识图谱中的辅助信息，例如社交网络和物品属性。

在方法思路上，论文认为现有基于知识图谱的推荐算法“未能利用丰富的语义关联”，因此提出把知识图谱视为异构网络来加入辅助信息，并构建一种“行为特征与知识特征统一嵌入”的推荐系统。也就是说，论文的方法不是只看用户和物品的直接交互，而是同时结合用户历史行为与知识图谱信息来挖掘用户偏好。

从偏好建模角度看，论文明确强调其方法能够从用户历史行为中学习“短期和长期偏好”，并通过整合知识图谱“更深层识别用户偏好”。因此，这篇论文对于“点击率影响因素”主题的启发主要在于：论文把用户历史行为和知识图谱辅助信息视为影响推荐结果的重要输入因素。但需要注意，正文片段并未直接讨论“点击率”这一指标本身，也未明确说明点击率的定义、建模方式、评估指标或点击行为的因果影响机制，因此如果要把它严格解释为CTR研究，论文未明确说明。

在结果层面，论文称所提出的ReBKC在三个数据集上相比最先进方法取得了显著提升，并认为这些结果验证了：结合历史行为学习短期与长期偏好、并融合知识图谱，有助于提供“更准确且更多样”的推荐。至于这三个数据集的名称、实验设置、提升幅度、显著性检验细节，正文片段未明确说明。

综合来看，基于现有正文片段，可以确认的影响推荐效果的因素包括：1）用户-物品交互稀疏程度；2）冷启动问题；3）知识图谱中的辅助信息，如社交网络和物品属性；4）用户历史行为；5）用户短期偏好与长期偏好；6）知识图谱中的语义关联利用程度。若进一步追问模型结构细节、特征工程细节、训练方式、损失函数、与点击率的直接关系，论文未明确说明。

## 结合主题的实际运用
结合“电商点击率影响因素”这一用户研究主题，这篇论文正文片段可支持的实际运用主要是：

1. 可用于分析推荐结果受哪些信息来源影响。正文明确支持把“用户历史行为”和“知识图谱辅助信息（如社交网络、物品属性）”作为影响推荐效果的重要因素纳入分析框架。

2. 可用于构建更个性化的推荐系统。论文明确提出统一嵌入行为特征和知识特征，以挖掘用户偏好，从而提供“更准确和更多样”的推荐。这意味着在业务上可用于优化推荐排序或推荐生成任务。

3. 可用于应对交互稀疏和冷启动问题。正文明确指出该类问题是传统协同过滤的局限，而引入知识图谱辅助信息是应对方向之一，因此对新用户、新物品或低交互场景的推荐优化具有业务含义。

4. 可用于结合短期与长期偏好进行推荐。正文明确说明其结果验证了学习用户短期和长期偏好的有效性，因此业务上可以把近期行为与长期历史共同用于用户偏好建模。

5. 若从电商点击率角度理解，本论文可以作为“可能影响用户点击相关推荐表现”的因素参考，即历史行为、物品属性、社交网络、知识图谱语义关联等因素可能与推荐质量有关。但论文正文没有直接说明其应用于电商点击率预测、CTR建模、广告点击、商品曝光点击转化等具体场景，因此这些更具体的业务场景论文未明确说明。

6. 论文可支持的任务是“推荐系统/个性化推荐”，这是正文和关键词直接给出的；至于是否已在电商平台、新闻、音乐、广告等特定行业中验证，正文片段未明确说明。

## 证据摘录
- “Collaborative filtering (CF) usually suffers from limited performance in recommendation systems due to the sparsity of user–item interactions and cold start problems.”
- “To address these issues, auxiliary information from knowledge graphs, such as social networks and item properties, is typically used to boost performance.”
- “The current recommended algorithms based on knowledge graphs fail to utilize rich semantic associations.”
- “we regard knowledge graphs as heterogeneous networks to add auxiliary information, propose a recommendation system with unified embeddings of behavior and knowledge features, and mine user preferences from their historical behavior and knowledge graphs”
- “These results verify the effectiveness of learning short-term and long-term user preferences from their historical behavior and by integrating knowledge graphs to deeply identify user preferences.”

## 依据说明
“详细解读”中关于传统CF受稀疏性和冷启动限制、知识图谱可作为辅助信息、现有方法未充分利用语义关联、论文提出统一嵌入行为与知识特征、以及学习短期和长期偏好等内容，均直接由摘要中的上述引文支撑。关于‘提供更准确和更多样的推荐’由摘要中“provide more accurate and diverse recommendations”和“shows a significant improvement on three datasets”支撑。关于‘影响推荐效果的因素包括历史行为、社交网络、物品属性、语义关联、短期和长期偏好’是对摘要明示内容的归纳。

“practical_usage”中关于可用于个性化推荐、缓解稀疏与冷启动、结合历史行为与知识图谱做偏好建模，均由摘要与关键词“Collaborative filtering / Recommendation system / Knowledge graph / Historical behavior”直接支撑。关于与‘电商点击率影响因素’的关系，只能谨慎表述为对推荐表现相关因素的参考，因为正文片段并未直接出现CTR、click-through rate、点击预测、排序曝光机制等表述；这些更具体内容论文未明确说明。关于具体业务行业、数据集名称、实验指标、模型结构细节，也均为论文未明确说明。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
