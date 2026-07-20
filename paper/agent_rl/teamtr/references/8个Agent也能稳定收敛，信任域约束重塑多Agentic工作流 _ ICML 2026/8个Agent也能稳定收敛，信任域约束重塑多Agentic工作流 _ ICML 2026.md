# 8个Agent也能稳定收敛，信任域约束重塑多Agentic工作流 | ICML 2026

Source: https://mp.weixin.qq.com/s/9mcdMSCSfYpY4cQj1g8bRg

![cover_image](cover_image)

# 8个Agent也能稳定收敛，信任域约束重塑多Agentic工作流 | ICML 2026

原创

让你更懂AI的
让你更懂AI的

[PaperWeekly](javascript:void(0);)

![]()

在小说阅读器读本章

去阅读

![]()

在小说阅读器中沉浸阅读

![图片](图片)

## 多 Agentic 工作流正在从推理时协作走向统一训练，TeamTR 用信任域约束给出了稳定微调方案。

多智能体 LLM 系统正在从多智能体辩论（Multi-Agent Debate）走向“智能体工作流”（Agentic Workflow）：不再只是让多个模型围绕同一个问题讨论、投票，而是让 planner、solver、critic、executor 等组件在共享上下文中连续协作，完成更长链条的任务。

问题也随之改变。过去我们更多问：推理时怎样组织多个模型？

现在还必须问：当统一训练多智能体系统时，怎样让团队稳定变好，而不是让局部更新破坏整体协作？

![](image_3.png)![]()![]()

〓 图：TeamTR 的核心直觉：从联合更新、顺序更新到 fresh occupancy 下的信任域训练。

![]()![]()

![](image_4.png)

论文标题：

TeamTR: Trust-Region Fine-Tuning for Multi-Agent LLM Coordination 

论文地址：

https://arxiv.org/abs/2605.15207

代码地址：

https://github.com/Yydc/TeamTR

![]()

![](image_5.png)![]()![]()

主要贡献

新问题：指出多 agent 工作流训练中的 compounding occupancy shift。更新一个 agent 后，后续 agent 面对的上下文分布已经改变；如果继续复用旧 rollout，偏差会沿更新顺序累积。

新理论：证明 stale-occupancy evaluation 的惩罚会随 agent 数量呈 O(n²) 增长；而使用 intermediate occupancy，在每次组件更新后重采样，可将主导惩罚降到 O(n)。

新方法：提出 TeamTR，在顺序微调中结合 fresh rollout 与 token 级 KL trust region，让每个组件更新既能带来局部收益，又不让团队分布漂移失控。

![](image_6.png)![]()![]()

研究问题：旧 rollout 会放大顺序微调中的分布错配

在多智能体 LLM 工作流中，多个 agent 共用同一段文本状态。planner 的计划、solver 的推理、critic 的反馈、executor 的执行结果都会被写回上下文，成为后续 agent 的输入。

因此，训练中的核心风险不是“能否逐个更新”，而是“更新后生成数据的分布是否还匹配当前团队”。

当第一个 agent 已经被微调，后续 agent 如果继续使用 stage-start 缓存的旧 rollout，就会在旧团队诱导的 occupancy 上优化；它看到的 prompt、历史消息和状态转移，已经不是当前团队真实会产生的分布。

前面的更新越多，后面的数据越过期，局部 surrogate objective 与实际团队表现之间的 gap 会被顺序累积。

论文将这种由共享上下文和旧轨迹复用共同造成的结构性偏差称为 ompounding occupancy shift。

![](image_7.png)![]()![]()

核心视角：消息就是会改变分布的动作

TeamTR 将共享上下文团队建模为 message-action MDP。这里的 action 不是普通动作，而是一段会进入上下文的消息。

正因为消息会改变后续状态，训练时的数据分布也会随着组件更新而改变。

顺序训练的问题在于，它为了节省采样成本，在一个 stage 内复用 stage-start rollout。

TeamTR 则要求每次更新一个 agent 后，用当前“部分更新后”的团队重新生成 rollout，让下一个 agent 在新分布上训练。

![](image_8.png)![]()![]()

从 O(n²) 到 O(n)：TeamTR 的理论直觉

论文的关键理论对比非常直接：

* 复用旧 rollout：stale-occupancy penalty 随 agent 数量近似 O(n²) 增长；
* 更新后重采样：intermediate-occupancy evaluation 将主导惩罚降到 O(n)；
* 加入 token 级 KL 信任域：每次组件更新的分布漂移被显式限制，因此可以得到 per-update 和 per-stage 的改进下界。

这让 TeamTR 不只是一个训练技巧，而是一个可监控的多 agent 微调框架。

![](image_9.png)![]()![]()

方法：TeamTR 如何训练多 LLM 团队？

TeamTR 采用 stage-wise trust-region fine-tuning。每个 stage 中，系统按顺序更新 agent：

1. 使用当前部分更新后的团队采样 fresh rollout；

2. 为当前 agent 构造 surrogate objective；

3. 用 KL penalty 或 early stopping 限制 token 级更新幅度；

4. 更新后刷新轨迹，再进入下一个 agent。

直观地说，TeamTR 允许每个 agent 变强，但不允许它一步跨得太远；同时，每个后续 agent 都必须在“新团队产生的新数据”上继续训练。

![](image_10.png)![]()![]()

实验结果：稳定性、监控与扩展性

整体性能：TeamTR 在多类任务上稳定提升

实验覆盖数学推理、逻辑推理、主动推理和规划任务。整体上，TeamTR 相比单 agent 微调和多 agent baseline 平均提升 7.1%。

更关键的是，提升主要来自稳定地控制分布漂移，而不是单纯增加训练步数或 rollout 数量。

在 AIME24 上，3×Qwen3-8B 团队从朴素顺序训练的 71.1% 提升到 88.1%，stale gap 从 0.31 降到 0.08。

在更大的异构团队 8B+14B+32B 中，TeamTR 也将 AIME24 从 77.8% 提升到 92.5%。

![](image_11.png)![]()![]()

〓 图：团队规模、模型规模与消融实验。

训练动态也支持这一点：PPO、GRPO、DAPO 形式的顺序 baseline 会出现中途回退，而 TeamTR 在匹配 rollout budget 下更稳定地提升。

![](image_12.png)![]()![]()

〓 图：匹配 rollout budget 下的训练动态。

消融与监控：fresh rollout 和 trust region 缺一不可

消融实验显示，TeamTR 的两个组件都重要。只做 KL penalty 但不刷新 rollout，仍然会留下 stale drift；只降低重采样频率，也会明显落后；完全去掉 trust region 时，训练最不稳定，协调分数也最弱。

TeamTR 的 token 级 KL 监控还能给出训练过程中的稳定性信号。在 AIME25 上，TeamTR 的 out-of-region 更新比例为 2%，而 DAPO、GRPO、PPO 分别为 21% / 44% / 60%。

这说明 trust region 不只是约束，也能成为训练是否仍在安全区域内的诊断工具。

![](image_13.png)![]()![]()

〓 图：token 级 KL 信任域监控与 certificate tracking。

扩展与替换：团队越大，越需要控制分布漂移

团队扩到 8 个 agent 时，TeamTR 达到 87.9%，而朴素顺序训练降到 58.7%。

这说明更多 agent 并不会自动带来更强协作；如果不控制中间分布，团队越大，过期 rollout 的影响越明显。

论文还测试了组件替换：将 Qwen2.5-Instruct 团队中的 1.5B agent 替换为 Qwen3-8B。

直接替换会造成明显性能冲击；TeamTR 的 Stage-0 alignment 则能缓解 swap shock，并在 AIME24 和 ARBench-DC 上分别带来 +27% / +24% 的提升。

![](image_14.png)![]()![]()

〓 图：组件替换中的 Stage-0 alignment。

![](image_15.png)![]()![]()

总结

TeamTR 的信息很清楚：训练多智能体 LLM 工作流，不是把每个 agent 单独变强就够了。

由于所有组件共享上下文，一个组件更新会改变后续组件面对的数据分布；如果继续使用旧 rollout，局部收益可能变成全局错配。

TeamTR 用“更新后重采样 + token 级信任域”把这个问题变成可控训练过程。它解释了为什么朴素顺序微调会退化，也给出了一个可监控、可扩展、支持组件替换的多 LLM 团队训练框架。

过去的多智能体 LLM 研究更多关注推理时如何组织角色和通信；TeamTR 强调的是训练时的关键问题：团队的分布要跟着团队一起更新。

**更多阅读**

[![](image_16.png)](https://mp.weixin.qq.com/s?__biz=MzIwMTc4ODE0Mw==&mid=2247719474&idx=2&sn=be225fb932a6dfac03b021ea389476c5&scene=21#wechat_redirect)

[![](image_17.png)](https://mp.weixin.qq.com/s?__biz=MzIwMTc4ODE0Mw==&mid=2247719474&idx=1&sn=aa5a0f9eb40a223969f250fbe52e1554&scene=21#wechat_redirect)

[![](image_18.png)](https://mp.weixin.qq.com/s?__biz=MzIwMTc4ODE0Mw==&mid=2247720381&idx=1&sn=712d2d82762b292e00b5543505ef7e67&scene=21#wechat_redirect)

![](image_19.gif)![]()![]()

**#投 稿 通 道#**

**让你的文字被更多人看到**

如何才能让更多的优质内容以更短路径到达读者群体，缩短读者寻找优质内容的成本呢？**答案就是：你不认识的人。**

总有一些你不认识的人，知道你想知道的东西。PaperWeekly 或许可以成为一座桥梁，促使不同背景、不同方向的学者和学术灵感相互碰撞，迸发出更多的可能性。 

PaperWeekly 鼓励高校实验室或个人，在我们的平台上分享各类优质内容，可以是**最新论文解读**，也可以是**学术热点剖析**、**科研心得**或**竞赛经验讲解**等。我们的目的只有一个，让知识真正流动起来。

📝 **稿件基本要求：**

• 文章确系个人**原创作品**，未曾在公开渠道发表，如为其他平台已发表或待发表的文章，请明确标注 

• 稿件建议以 **markdown** 格式撰写，文中配图以附件形式发送，要求图片清晰，无版权问题

• PaperWeekly 尊重原作者署名权，并将为每篇被采纳的原创首发稿件，提供**业内具有竞争力稿酬**，具体依据文章阅读量和文章质量阶梯制结算

📬 **投稿通道：**

• 投稿邮箱：hr@paperweekly.site 

• 来稿请备注即时联系方式（微信），以便我们在稿件选用的第一时间联系作者

• 您也可以直接添加小编微信（**pwbot02**）快速投稿，备注：姓名-投稿

![](image_20.png)![]()![]()

**△长按添加PaperWeekly小编**

🔍

现在，在**「知乎」**也能找到我们了

进入知乎首页搜索**「PaperWeekly」**

点击**「关注」**订阅我们的专栏吧

·

![](image_21.jpg)![]()![]()

预览时标签不可点

![]()

微信扫一扫  
关注该公众号

继续滑动看下一个

轻触阅读原文

![](image_22.png)

PaperWeekly

向上滑动看下一个

[知道了](javascript:;)



![]()
微信扫一扫  
使用小程序

[取消](javascript:void(0);)
[允许](javascript:void(0);)

[取消](javascript:void(0);)
[允许](javascript:void(0);)

[取消](javascript:void(0);)
[允许](javascript:void(0);)

×
分析

![跳转二维码]()

![作者头像](image_22.png)

微信扫一扫可打开此内容，  
使用完整服务

：
，
，
，
，
，
，
，
，
，
，
，
，
。
 
视频
小程序
赞
，轻点两下取消赞
在看
，轻点两下取消在看
分享
留言
收藏
听过