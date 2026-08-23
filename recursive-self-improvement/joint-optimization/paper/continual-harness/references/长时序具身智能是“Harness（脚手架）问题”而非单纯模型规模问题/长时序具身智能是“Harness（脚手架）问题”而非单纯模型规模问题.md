# 长时序具身智能是“Harness（脚手架）问题”而非单纯模型规模问题

Source: https://mp.weixin.qq.com/s/JI2bXhV6GCJiYHs8des2Zw

![cover_image](cover_image)

# 长时序具身智能是“Harness（脚手架）问题”而非单纯模型规模问题

原创

凡花花的小窝
凡花花的小窝

[宫灵瑞](javascript:void(0);)

![]()

在小说阅读器读本章

去阅读

![]()

在小说阅读器中沉浸阅读

https://x.com/sethkarten/status/2054579536612966480

**Seth Karten（Princeton CS PhD，前CMU Waymo研究员）长帖详细总结** —— 长时序具身智能是“Harness（脚手架）问题”而非单纯模型规模问题

这篇帖子核心观点是：当前具身代理（embodied agents）在长时序任务中的瓶颈主要在于**动态Harness（脚手架）的迭代 refinement，而非基础模型本身的能力上限。通过Pokémon游戏实验，作者展示了从人工辅助到模型自主迭代Harness的演进路径，并正式提出Continual Harness**框架，实现在线自适应与模型-Harness协同学习，具有重要范式意义。

### 背景与核心洞见

作者指出，**Claude Code** 和 **OpenHands** 等编码代理已通过强大的 scaffolding（prompt、skills、memory、sub-agents）取得成功，而具身代理仍缺乏等价机制。Gemini原始模型仅通过截图+按键接口玩Pokémon Red时，几乎无法走出第一个镇。这凸显了Harness的重要性。

**Gemini Plays Pokémon (GPP)** 项目（Joel Zhang主导）是里程碑：首次让AI完成**Pokémon Blue、Yellow Legacy（hard mode）** 和 **Crystal** 且无一败绩。其关键在于**迭代Harness开发**：游戏轨迹暴露失败模式 → Harness新增sub-agents和skills → 重新游戏。早期依赖人工编辑，后期模型通过**meta-tools**（define\_agent、run\_code、notepad edits）自主完成大部分编辑，甚至自命名策略（如“Operation Zombie Phoenix”）和构建显式真值表解决谜题。

### Continual Harness框架

论文《**Continual Harness: Online Adaptation for Self-Improving Foundation Agents**》（arxiv: https://arxiv.org/abs/2605.09998）将此循环形式化并端到端自动化。

**系统架构与流程**：

* **接口**

  ：仅提供frame、可见区域ASCII地图、按钮输入。**无任何人工知识、领域脚手架或预制skills**。
* **Refiner子代理**

  ：每F步读取最近轨迹窗口，通过CRUD操作修改prompt、sub-agents、skills和memory。
* **持续运行**

  ：无需reset，失败在单长episode内累积并持续可见，refinement质量随episode长度复合提升。
* **与Prompt Optimization的区别**

  ：后者适用于短episode、可廉价reset场景；Continual Harness针对**长时序、部分可观测、reset昂贵或不可用的真实部署场景**。

**关键实验结果**：

* 在**Gemini 3 Pro**上，Continual Harness严格Pareto优于最小化baseline。
* **Gemini 3 Flash**

  ：高方差增益。
* **Gemini 3 Flash-Lite**

  ：所有变体均劣于baseline。自精炼是**高阶技能**，需模型具备读取轨迹、识别失败、提出有效编辑的能力，低于阈值则循环无法自举。

### 模型-Harness协同学习探索

作者进一步将Harness refinement扩展到训练阶段：

* 使用开源**Gemma-4**在实时refining Harness中运行。
* 每256步用过程奖励模型（process reward model）对滑动窗口打分。
* 低奖励窗口由**Gemini 3.1 Pro**作为教师重标注，进行SFT更新得到新权重。
* **Reset-free训练循环**

  ：第k次迭代结束的模拟器状态直接作为第k+1次起点。
* 结果：随着训练经验和refinement积累，开源模型持续突破游戏里程碑。

作者强调：未来代理能力提升将由**两条学习者共享单一流轨迹**定义——快速的Harness编辑器（in-place）和慢速的权重更新器（weights），二者相互感知并协同进化，而非孤立扩大上下文窗口或孤立增强基础模型。

### 总结洞见

**最大价值**在于将代理研究焦点从“更大模型”转向“模型与动态Harness的持续协同进化”。**迭代Harness refinement** 能弥合与手工专家系统的差距，且在长时序具身任务中是负载承载能力（load-bearing capability）。当前静态benchmark无法捕捉这一区分，未来需设计能测量自精炼能力的长时序、reset-scarce基准。

对读者的启发：构建实用长时序具身代理时，应优先投入**可在线迭代、模型可控的Harness设计**，并探索模型-Harness联合优化范式。这不仅是技术路径，更是代理系统从“静态工具”向“自进化生命体”转变的关键哲学转变。GPP和Continual Harness为此提供了极具说服力的实证案例（详见演示：https://sethkarten.ai/continual-harness）。

预览时标签不可点

![]()

微信扫一扫  
关注该公众号

继续滑动看下一个

轻触阅读原文

![](image_2.png)

宫灵瑞

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

![作者头像](image_2.png)

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