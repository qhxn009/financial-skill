这个项目中的**技能 (Skills)** 是智能体能力的核心，可以理解为封装好的**专业领域知识和方法论**。它们是用Markdown写的“说明书”，告诉智能体在特定金融任务中应遵循的**步骤、逻辑和规范**。每当任务相关时，智能体便会自动激活它们。

技能按**垂直业务领域**进行分类，以下是所有技能的全面讲解。

### 📊 1. 核心分析技能 (`financial-analysis`)
这是所有其他垂直插件的基础，提供了最通用的财务建模和图表制作能力。

| 技能 | 对应命令 | 核心功能详解 |
| :--- | :--- | :--- |
| **comps-analysis** | `/comps` | 执行可比公司分析，选取同行公司，计算并输出交易乘数（如EV/EBITDA, P/E）。 |
| **dcf-model** | `/dcf` | 构建现金流折现模型，计算WACC，并进行敏感性分析。 |
| **lbo-model** | `/lbo` | 构建杠杆收购模型，分析内部收益率(IRR)和资本回报倍数(MOIC)。 |
| **3-statement-model** | `/3-statement-model` | 将数据填充到标准的三张表（利润表、资产负债表、现金流量表）模型中，并完成勾稽。 |
| **audit-xls** | `/debug-model` | 审计Excel模型，追踪公式引用、检测硬编码数字、检查资产负债表是否平衡。 |
| **clean-data-xls** | — | 清理和标准化Excel中的表格数据，为分析做准备。 |
| **deck-refresh** | — | 一键刷新PPT中的嵌入图表和表格数据链接。 |
| **competitive-analysis** | `/competitive-analysis` | 进行竞争格局和市场竞争定位分析。 |
| **ib-check-deck** | — | 对PPT进行质量检查，查找错误和不一致。 |
| **pptx-author / xlsx-author** | — | 在无头(headless)模式（即Managed Agent模式）下，直接生成PPT和Excel文件。 |
| **ppt-template-creator** | `/ppt-template` | 从用户提供的模板中学习，创建可复用的PPT模板技能。 |
| **skill-creator** | — | 这是一个“元技能”，指导用户如何创建新的自定义技能。 |

### 🏦 2. 投资银行技能 (`investment-banking`)
专为交易执行和承揽材料设计。

| 技能 | 对应命令 | 核心功能详解 |
| :--- | :--- | :--- |
| **strip-profile** | `/one-pager` | 为pitch book创建单页公司简介，包含关键财务和业务亮点。 |
| **pitch-deck** | — | 自动将分析数据和图表填充到pitch deck模板中。 |
| **datapack-builder** | — | 从机密信息备忘录(CIM)和公开文件中提取数据，构建数据包。 |
| **cim-builder** | `/cim` | 起草机密信息备忘录，为公司出售或融资做准备。 |
| **teaser** | `/teaser` | 撰写匿名的单页项目简介(Teaser)，用于初步市场试探。 |
| **buyer-list** | `/buyer-list` | 梳理潜在的战略买家与财务投资者长名单(Long List)。 |
| **merger-model** | `/merger-model` | 构建并购模型，进行增厚/稀释(EPS Accretion/Dilution)分析。 |
| **process-letter** | `/process-letter` | 起草投标流程指引、程序信函等交易文件。 |
| **deal-tracker** | `/deal-tracker` | 追踪进行中的交易、关键里程碑和待办事项。 |

### 📈 3. 证券研究技能 (`equity-research`)
覆盖从信息追踪到报告发布的完整研究流程。

| 技能 | 对应命令 | 核心功能详解 |
| :--- | :--- | :--- |
| **earnings-analysis** | `/earnings` | 在财报发布后，生成包含模型更新和点评的季度更新报告。 |
| **earnings-preview** | `/earnings-preview` | 在财报发布前，生成情景分析和关键指标预测。 |
| **initiating-coverage** | `/initiate` | 撰写机构级别的首次覆盖(Initiation)深度报告。 |
| **model-update** | `/model-update` | 当有新的财务数据或指引时，自动更新已有的财务模型。 |
| **morning-note** | `/morning-note` | 生成晨会笔记和交易想法，总结隔夜市场动态。 |
| **sector-overview** | `/sector` | 撰写行业概览和主题研究报告。 |
| **thesis-tracker** | `/thesis` | 维护并系统性地追踪和更新投资逻辑(Investment Thesis)。 |
| **catalyst-calendar** | `/catalysts` | 追踪覆盖公司未来的股价催化剂事件。 |
| **idea-generation** | `/screen` | 根据给定标准进行股票筛选，产生投资想法(Idea Generation)。 |

### 💼 4. 私募股权技能 (`private-equity`)
从项目搜寻、尽职调查到投后管理的全链条。

| 技能 | 对应命令 | 核心功能详解 |
| :--- | :--- | :--- |
| **deal-sourcing** | `/source` | 发现潜在标的公司，核验CRM，起草给创始人的接洽信。 |
| **deal-screening** | `/screen-deal` | 对收到的商业计划书或Teaser进行快速初审，给出通过/否决的初步判断。 |
| **dd-checklist** | `/dd-checklist` | 生成按工作流分列的尽职调查清单。 |
| **dd-meeting-prep** | `/dd-prep` | 为管理层访谈和专家电话会准备问题清单。 |
| **unit-economics** | `/unit-economics` | 分析单位经济模型，如ARR/季度，LTV/CAC，净留存率等。 |
| **returns-analysis** | `/returns` | 生成IRR和MOIC的敏感性分析表格。 |
| **ic-memo** | `/ic-memo` | 起草投资委员会备忘录，是决定投资与否的关键文件。 |
| **portfolio-monitoring** | `/portfolio` | 追踪被投公司的关键绩效指标(KPI)和预算偏差。 |
| **value-creation-plan** | `/value-creation` | 制定交割后的百日计划(100-Day Plan)和EBITDA提升路径。 |
| **ai-readiness** | `/ai-readiness` | 评估被投公司在AI应用方面的准备度和潜力。 |

### 💰 5. 财富管理技能 (`wealth-management`)
面向客户顾问，提升客户服务和报告效率。

| 技能 | 对应命令 | 核心功能详解 |
| :--- | :--- | :--- |
| **client-review** | `/client-review` | 生成客户会面准备材料，包括组合表现和沟通要点。 |
| **financial-plan** | `/financial-plan` | 进行退休、教育、遗产及现金流等多目标财务规划。 |
| **portfolio-rebalance** | `/rebalance` | 分析资产配置漂移，并生成税务敏感的组合再平衡建议。 |
| **client-report** | `/client-report` | 生成面向客户的组合表现报告。 |
| **investment-proposal** | `/proposal` | 为潜在客户撰写投资建议书。 |
| **tax-loss-harvesting** | `/tlh` | 识别税损收割(Tax-Loss Harvesting)机会，并预警虚假交易(Wash Sale)。 |

### ⚙️ 总结
这些技能将金融领域的隐性知识**结构化为可复用的方法论**。它们共同的特点是**高度可定制**——你可以直接修改对应的Markdown文件，来调整分析方法、术语或输出格式，使其完全契合你所在机构的标准工作流程。