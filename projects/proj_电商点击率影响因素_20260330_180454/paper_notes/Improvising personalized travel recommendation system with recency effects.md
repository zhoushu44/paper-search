# Improvising personalized travel recommendation system with recency effects

## 论文信息
- 标题：Improvising personalized travel recommendation system with recency effects
- 作者：Paromita Nitu, Joseph Coelho, Praveen Madiraju
- 年份：2021
- 会议/期刊：Big Data Mining and Analytics
- 用户搜索主题：电商点击率影响因素
- 原文链接：https://ieeexplore.ieee.org/ielx7/8254253/9430128/09430131.pdf

## 中文详细解读
该论文片段主要讨论的是“个性化旅行推荐系统”如何通过加入“时间敏感的近期性（recency）”来改进推荐效果，而不是直接研究电商点击率。若从“推荐系统影响用户响应”的角度理解，这篇论文可提供的核心启发是：用户兴趣会随时间变化，因此推荐模型若能更重视用户近期行为，可能比只看长期历史更贴近用户当下偏好。

具体来看，正文明确提出：用户对旅行目的地的倾向“会随着时间改变”，因此作者不只分析用户自己的 Twitter 数据，还分析其 friends 和 followers 的数据，并且是“及时地（in a timely fashion）”去理解最近的旅行兴趣。也就是说，论文把“近期兴趣”视为个性化推荐中的一个关键因素。

在方法层面，论文先用机器学习分类器识别与旅行相关的 tweets，再用这些 travel tweets 生成个性化旅行推荐。与既有模型相比，这篇论文的主要改进不是简单增加特征，而是把时间敏感的 recency weight 融入模型。正文说明，他们将社交媒体内容划分为不同时间块（time blocks），并对“更当代、更近期”的活动赋予更高权重；而对于社交媒体活跃度较低、信息量不足的时间块，则给予更低权重。这说明该模型不是把所有历史内容等权看待，而是显式地区分“新近信息”和“较旧信息”的价值。

在权重构造上，论文不仅考虑时间，还考虑信息来源与情感。来源上，用户本人、朋友、粉丝三者的重要性不同，因此分别赋权。正文给出的近似归一化结果是：用户权重 U=4，朋友权重 F=3.25，粉丝权重 L=2.75，说明模型中用户自己的内容最重要，其次是朋友，再次是粉丝。情感上，正向、 中性、负向情感也采用不同系数，分别是 1.0、0.65、0.35。最终，各类兴趣分数按照时间权重、来源权重、情感权重综合计算并排序，得到用户偏好的类别列表。

从推荐输出形式看，论文不是直接预测单个地点得分，而是先形成“类别偏好分数”，再按类别分数比例抽取推荐结果。例如给定示例中，park、museum、restaurant、historical building 四类分数分别为 0.44、0.22、0.19、0.15，因此系统给出 15 个推荐时，会按比例分配为 6 个 park、4 个 museum、3 个 restaurant、2 个 historical building。由此可见，该系统首先做的是“用户兴趣结构”的刻画，然后再映射到具体 POI。

关于与既有推荐系统的关系，正文指出该模型同时包含 collaborative filtering 和 content-based filtering 的特征：一方面挖掘朋友和粉丝的 tweets 来识别相似兴趣，具有协同过滤色彩；另一方面又从 tweet 文本和元数据抽取地点类别相关信息，体现内容过滤特征。此外，正文还提到推荐系统在电商中非常流行，但该论文本身的应用领域是旅游/POI 推荐，不是电商商品推荐。

关于效果，正文明确声称：所提模型优于已有的个性化 POI 推荐模型，总体准确率为 75.23%。评价方式采用双盲短问卷，对随机选取的 Twitter 用户进行线上和线下调查。对于“没有或很少活动”的用户，论文将其视为冷启动群体，并说明模型会“基于趋势”来推荐旅行地点。但这个“趋势”如何定义、计算，正文片段未明确说明。

如果将其放到“影响用户点击/选择的推荐因素”这一更宽泛问题下，这篇论文真正被正文明确支持的因素有三类：第一，近期性，即近期行为比久远行为更重要；第二，社交关系信息，即朋友和粉丝的偏好被纳入；第三，情感倾向，即正向、中性、负向内容贡献不同。至于这些因素如何具体影响电商点击率、转化率、曝光效率等指标，论文未明确说明。

## 结合主题的实际运用
基于正文，这篇论文可支持的实际运用或业务含义主要有：

1. 可用于个性化旅行推荐场景
正文明确说明系统目标是根据用户、其朋友、其粉丝的社交媒体活动，生成个性化的 place of interest 推荐，适用于旅游/出行平台中的 POI 推荐任务。

2. 可用于“近期兴趣优先”的推荐排序改进
论文表明用户兴趣会变化，因此推荐模型可以把用户内容按时间块组织，并对近期内容赋予更高权重，以更贴合用户当前兴趣。这适合用于需要体现“近期偏好”的推荐任务。

3. 可用于结合社交关系信号的推荐建模
正文明确将用户本人、朋友、粉丝三类内容同时纳入，而且赋予不同权重。因此，该论文支持在推荐中综合使用社交关系相关行为数据，而不是只依赖用户本人历史。

4. 可用于结合情感倾向的类别偏好计算
论文把正向、中性、负向情感分别赋予不同权重，再汇总到各兴趣类别得分，适合用于“先识别类别兴趣、再分发具体推荐项”的任务。

5. 可用于冷启动用户的趋势型推荐
正文提到对于活动极少的用户，模型会基于趋势推荐旅行地点，因此可支持低行为数据用户的推荐场景。但“趋势”的具体构造方法，论文片段未明确说明。

6. 对“电商点击率影响因素”的可借鉴含义
若仅严格依据正文，可借鉴的是：推荐结果可能受“近期行为权重、社交关联信息、文本情感信息”影响，从而提升推荐准确性。正文还指出推荐系统在电商中广泛应用。但论文没有直接研究点击率，也没有报告 CTR、CVR、停留时长等电商指标，因此不能据此直接得出电商点击率结论，论文未明确说明。

## 证据摘录
- “the user’s inclination towards travel destinations is subject to change over time.”
- “our proposed model takes into account a user’s most recent interest by incorporating time-sensitive recency weight into the model.”
- “To emphasize user’s recent interest, we have imparted social media contents into time blocks represented by suffix i, and more weights have been assigned to contemporary activities.”
- “U, F, and L are normalized... and approximated at U=4, F=3.25, and L=2.75. The scores for positive sentiment have a weight of 1.0, for neutral sentiment, 0.65; and for negative sentiment, 0.35.”
- “Our proposed model has outperformed the existing personalized place of interest recommendation model, and the overall accuracy is 75.23%.”

## 依据说明
“详细解读”中关于用户兴趣随时间变化、模型引入近期性权重、按时间块加权、综合用户/朋友/粉丝与情感分数、最终得到类别排序，以及总体准确率 75.23%，均由正文片段1和片段3直接支撑。关于系统兼具协同过滤与内容过滤特征，来自片段2对模型构成的说明。关于冷启动用户基于趋势推荐，来自片段3的评估描述。关于‘趋势如何计算’、‘对电商点击率的直接影响’、‘CTR/CVR等商业指标表现’，正文未明确说明。因此“practical_usage”里凡涉及电商点击率的部分，只能表述为可借鉴的推荐建模含义，而不能声称论文已直接验证。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
