# Deep learning for click-through rate estimation

## 论文信息
- 标题：Deep learning for click-through rate estimation
- 作者：W Zhang, J Qin, W Guo, R Tang, X He
- 年份：2021
- 会议/期刊：arxiv.org
- 用户搜索主题：电商点击率
- 原文链接：https://arxiv.org/pdf/2104.10584

## 中文详细解读
这篇论文从综述视角讨论CTR estimation中的深度学习方法，而不是提出单一新模型。正文首先把CTR estimation定位为个性化在线服务中的核心模块，适用场景包括在线广告、推荐系统、网页搜索等；在数据表示上，CTR训练数据通常被组织成表格形式，经过特征工程处理后，每条样本是multi-field categorical format，对应二分类标签（点击为1，未点击为0）。在模型训练上，论文明确把CTR estimation表述为二分类问题，并使用cross entropy loss。

论文对模型发展的核心解释有两条主线：第一条是特征工程复杂度的变化，第二条是模型容量的变化。早期CTR模型受计算能力限制，主要依赖人工设计更好的特征，同时使用较简单的模型；之后引入更复杂、尤其是深层架构，以减少人工特征工程负担；再往后，论文指出，仅靠堆叠更复杂深模型已逐渐接近性能瓶颈，因此新的方向是把复杂模型与可学习的特征工程结合起来。也就是说，这篇论文不是简单主张“模型越深越好”，而是强调“深模型 + 可学习特征工程”的结合是新的发展方向。

在从浅层到深层的演进上，论文以LR、POLY2、GBDT、FM等代表模型说明问题。LR的优点是高效率、易于快速部署，但其局限在于难以自动捕捉有判别力的组合特征。论文用“学生 + LA + Disneyland广告”这类组合模式说明，仅靠线性项难以表达高阶组合关系，因此早期方法需要人工构造cross features。POLY2给二阶组合特征分配权重，但需要O(m^2)参数，而且在稀疏数据上表现可能较差，因为很多特征对很少或从未共同出现，相关交互参数难以估计。GBDT可自动学习部分特征交互，但难以并行训练，且只能利用一小部分可能的特征交互，因此在大规模场景中应用受限。FM的重要性在于：它为每个特征分配k维embedding，通过embedding内积来灵活建模特征组合关系，从而缓解稀疏数据下交互参数难估计的问题。正文还提到FFM是FM的重要扩展，但给定片段未完整展开其机制，因此这里不能进一步解释其细节，论文未明确说明。

论文的重点之一是“显式特征交互学习模块”。正文列举了多类交互算子与对应模型。第一类是基于product operation的交互建模。NFM提出bi-interaction layer，位于embedding层与DNN之间，用来建模pairwise feature interactions；论文认为它把bi-interaction layer的线性交互与DNN的非线性交互结合起来，因此比已有深模型更容易训练。Cross Network则通过每层显式feature crossing，使交互阶数随层深增加，并由层数决定；Cross Network V2把cross vector替换为cross matrix，以提高表达能力。CIN被介绍为比Cross Network更有效、可捕捉有界阶数特征交互的模型。KPNN和PIN则分别利用kernel product和micro-net来建模特征交互。

第二类是卷积类交互建模。CCPM通过反复执行卷积、池化和非线性激活来生成任意阶特征交互，但它对field order敏感，因此只能学习相邻特征之间的部分交互。FGCNN在CCPM基础上引入recombination layer，以建模非相邻特征，并将CNN生成的新特征与原始特征结合做最终预测；论文指出，FGCNN验证了CNN生成特征可以扩充原始特征空间，并降低现有深结构的优化难度。FiGNN则把multi-field categorical data视作全连接图：field是节点，不同field之间的交互是边，再通过图传播建模特征交互。论文对FiGNN的动机解释是：已有使用简单无结构组合方式的深模型，对复杂特征交互的建模能力有限。

第三类是注意力机制交互建模。AFM在FM上加入attention network，使不同特征交互对预测的贡献可不同：它对每个pairwise interacted vector计算attention score，经过softmax归一化后加权用于最终预测。FiBiNET扩展SENET以学习特征重要性，再用bilinear function学习特征交互。AutoInt利用multi-head self-attention和残差连接显式建模不同阶的特征交互，并可通过attention weights提供可解释预测。InterHAt结合transformer网络与多层attentional aggregation layer进行特征交互学习，正文指出它训练效率高、性能可比，并能解释不同特征交互的重要性。

论文还讨论了DNN在深度CTR模型中的角色，并把架构分为single tower和dual tower。single tower是把特征交互层与深网络串联，优点是可以有效捕捉高阶交互，但低阶交互信号可能在后续DNN中消失。dual tower则让特征交互层与DNN并联：前者显式捕捉低阶交互，后者隐式捕捉高阶交互，最后联合输出。论文评价是，single tower如NFM、PIN建模能力更强、结构更复杂，但通常容易陷入bad local minima并且高度依赖参数初始化；dual tower如Wide & Deep、DeepFM、DCN、DCN V2、xDeepFM、AutoInt+，其DNN部分可视为对交互层残差信号的补充，因此训练更稳定且性能更好。

在自动化架构设计方面，正文片段重点覆盖了embedding size search、feature interaction search和whole architecture search。对于embedding大小搜索，论文提到一类方法通过hard selection在搜索空间中选择embedding维度，但预设阈值难调，可能导致次优性能；PEP则可以从数据中自适应学习阈值来剪枝embedding参数。相对地，AutoEmb和AutoDim采用soft selection，对候选维度的embedding按可学习权重求和，并通过可微搜索算法训练；其中AutoDim按field分配不同embedding size，AutoEmb按individual feature搜索不同embedding size。

对于feature interaction search，论文认为自动设计有效特征交互具有较高价值。AutoFIS会枚举所有特征交互，并用一组架构参数表示各交互的重要性，再通过梯度下降和稀疏优化自动过滤不重要交互；但它把交互函数限制为inner product。受到PIN中micro-network可能更有效的启发，SIF和AutoFeature进一步关注“哪些交互重要”之外，“用什么交互函数合适”也很关键。SIF为矩阵分解自动搜索交互函数；AutoFeature为每对field设计微网络，并搜索其架构。论文同时指出，AutoFIS和AutoFeature都不能建模高阶特征交互，因为它们需要先枚举所有可能交互。为避免低效枚举，AutoGroup提出自动生成一些feature groups，使给定阶数的交互有效，并通过Gumbel-Softmax从CTR监督信号中学习每个特征被选入各组的概率。BP-FIS则进一步做到面向不同用户识别重要特征交互，提供比以往方法更细粒度的交互选择。

在whole architecture search上，AutoCTR把代表性的CTR结构抽象为virtual blocks，并设计两层分层搜索空间：外层搜索block之间的连接，内层搜索不同block的详细超参数；搜索算法使用evolutionary algorithm，并做了效率优化。AMER则同时搜索序列特征上的行为建模结构和非序列特征之间的交互：前者的搜索空间包括normalization、activation以及卷积/循环/池化/注意力等层选择；后者通过逐步增加交互阶数来搜索有效交互。正文明确指出，AMER一方面针对user behaviors的序列表示提取架构进行搜索，另一方面自动探索非序列特征交互。

论文总结部分给出的总体结论是：借助feature-interaction operators，深模型更能捕捉multi-field categorical data中的高阶组合特征模式，从而带来更好的预测性能；借助attention mechanism、memory networks或retrieval-based approaches，可以更有效地学习用户行为历史表示，进一步提升预测性能。不过，在当前提供的片段中，关于memory networks、retrieval-based approaches以及完整的用户行为模型细节没有展开，因此其具体机制、适用条件与实验结论，论文未明确说明。

## 结合主题的实际运用
围绕“电商点击率”主题，这篇论文可支持的实际运用主要体现在以下几个方面：

1. 可作为电商CTR建模方案选型依据。正文明确指出CTR estimation是个性化在线服务中的核心模块，且适用于item recommendation in e-commerce。因此在电商推荐或广告点击率预测中，可以根据业务需求在LR、FM、NFM、DCN、xDeepFM、AutoInt等不同类型模型之间做架构选择。

2. 可用于指导电商多字段离散特征建模。论文明确把CTR数据组织成multi-field categorical data，例如用户、城市、职业、商品、类目、品牌等字段，因此适合支持电商场景下基于用户侧、商品侧、上下文字段共同建模的CTR预测任务。

3. 可用于提升对特征组合关系的利用。论文反复强调高阶combining features / feature interactions对点击预测的重要性，因此在电商点击率任务中，可重点考虑显式特征交互模块，以更好刻画用户属性、商品属性、类目、品牌等字段之间的组合模式。

4. 可用于大规模平台下的模型设计思路。正文指出LR易于快速部署，GBDT在大规模场景受限，dual tower模型训练更稳定且性能更好，因此对于电商大规模CTR系统，论文可支持“从简单浅层模型过渡到更稳定的双塔深度交互模型”的设计思路。

5. 可用于自动化结构搜索与特征交互搜索。若电商CTR系统需要减少人工调参与人工交互设计，论文介绍的AutoFIS、AutoGroup、AutoCTR、AMER、AutoEmb、AutoDim、PEP等方法，可作为自动搜索embedding维度、交互方式与整体架构的参考方向。

6. 可用于含用户历史行为的点击率建模。摘要和总结明确提到，对拥有丰富用户历史的大平台，深度行为模型是重要视角；总结也指出attention mechanism、memory networks、retrieval-based approaches能更有效学习用户行为历史表示并提升预测性能。因此对于电商中的用户历史点击/浏览/行为序列建模，这篇论文可提供方向性支持。但关于具体行为模型如何构造、输入输出如何定义、在电商场景如何部署，当前片段未明确说明。

7. 若需要可解释性，论文中的注意力交互模型可提供支持。正文指出AutoInt可通过attention weights提供可解释预测，InterHAt可解释不同特征交互的重要性，因此在电商CTR中，若业务希望理解“哪些字段交互影响点击”，这些模型有潜在实用价值。

除此之外，例如具体线上A/B收益、具体电商指标提升幅度、训练资源消耗、延迟约束、冷启动策略、样本构建细节等，论文未明确说明。

## 证据摘录
- Click-through rate (CTR) estimation plays as a core function module in various personalized online services, including online advertising, recommender systems, and web search etc.
- For CTR estimation tasks, the dataset is commonly represented as a table... each instance is in a multi-field categorical format while the corresponding label is binary (1 for click and 0 for non-click).
- The development of the models could be summarized into two aspects which are feature engineering complexity and model capacity... Combining both complex models and learnable feature engineering is the new development direction.
- Single tower models... could effectively capture the high-order feature interactions but the signals of low-order feature interactions may vanish... dual tower networks are proposed... which yields stable training and the improved performance.
- With feature-interaction operators, deep models are more capable of capturing high-order combining feature patterns in the multi-field categorical data and yield better prediction performance. With attention mechanism, memory networks or retrieval-based approaches, the representation of a user behavior history can be effectively learned, which further improves the prediction performance.

## 依据说明
对论文定位、CTR任务定义、数据形式和损失函数的解读，主要由正文片段1中关于‘core function module’、表格数据表示、multi-field categorical format以及binary classification / cross entropy loss的描述支撑。关于‘从浅层到深层’的发展逻辑、人工特征工程与模型容量的双主线、以及‘复杂模型+可学习特征工程’是新方向，来自正文片段1中对模型发展趋势图和相应文字说明。关于显式特征交互学习、卷积/注意力/图结构等模型类别，以及single tower与dual tower的差异、稳定性与性能判断，来自正文片段2。关于自动化搜索，包括embedding size search、feature interaction search、whole architecture search，以及AutoFIS、AutoGroup、AutoCTR、AMER等方法的作用，来自正文片段3。关于用户行为历史可被attention mechanism、memory networks或retrieval-based approaches有效学习并提升预测性能，来自正文片段3的总结段和摘要中的‘deep behavior models are discussed’。凡涉及这些方法的具体实验效果数值、线上部署策略、在电商场景中的实现细节、完整行为建模机制等，当前片段均未展开，因此相关部分均标注为‘论文未明确说明’。

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
