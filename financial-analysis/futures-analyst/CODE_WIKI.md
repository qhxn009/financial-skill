# Futures Analyst — Code Wiki

> **项目名称**：futures-analyst（期货分析师收评技能）
> **版本**：builtin_skill_version 1.32
> **定位**：面向国内商品期货市场的自动化分析报告生成技能，覆盖全品种行情采集、产业链分析、资讯聚合与 HTML 报告输出。

---

## 1. 项目整体架构

```
futures-analyst/
├── SKILL.md                          # 技能定义文件（触发条件、执行流程、数据规范）
├── references/
│   ├── Exchanges.md                  # 全球交易所与央行参考链接
│   └── Ratio.md                      # 大宗商品重要比值/价差关系知识库
├── scripts/
│   ├── fetch_quotes.py               # 期货行情数据采集脚本
│   ├── fetch_calendar.py             # 财经日历数据获取脚本
│   ├── report_generator.py           # HTML 报告生成引擎
│   └── analysis.json                 # 板块分析数据示例/模板
└── assets/                           # （运行时需要）HTML 报告模板
    └── report_template.html           # 报告模板，含 {{占位符}}
```

### 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    SKILL.md (技能入口)                    │
│  定义触发条件 → 编排执行流程 → 指定数据规范               │
└───────────────────────┬─────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   ┌────────────┐ ┌──────────┐ ┌───────────────┐
   │ fetch_     │ │ fetch_   │ │ tavily_search │
   │ quotes.py  │ │calendar.py│ │ /tavily_research│
   │ (行情采集)  │ │(日历采集) │ │ (资讯搜索)     │
   └─────┬──────┘ └────┬─────┘ └──────┬────────┘
         │             │              │
         ▼             ▼              ▼
   quotes_*.json  calendar_*.json  analysis.json
         │             │              │
         └─────────────┼──────────────┘
                       ▼
              ┌─────────────────┐
              │ report_         │
              │ generator.py    │
              │ (报告生成引擎)   │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ report_template │
              │ .html           │
              │ (模板渲染)       │
              └────────┬────────┘
                       ▼
              ~/Desktop/期货分析_YYYYMMDD_版本.html
```

---

## 2. 主要模块职责

### 2.1 SKILL.md — 技能定义与编排

**职责**：作为整个技能的"大脑"，定义了完整的六步执行流程。

| 步骤 | 名称 | 说明 |
|------|------|------|
| 第一步 | 确定报告版本 | 根据 cron 时间自动判断：盘中版 / 收盘版 / 夜盘前瞻版 / 周末版 |
| 第二步 | 采集期货行情数据 | 调用 `fetch_quotes.py`，通过东方财富 API 获取实时行情 |
| 第三步 | 采集板块资讯与产业链分析 | 使用 `tavily_research` / `tavily_search` 搜索各板块新闻 |
| 第四步 | 数据校验 | 时间戳校验 + 异常值检测（涨跌幅 > ±5% 标注异常波动） |
| 第五步 | 识别日内明星品种 | 筛选涨幅/跌幅/增仓/投机度 Top 3 |
| 第六步 | 生成 HTML 报告 | 调用 `report_generator.py` 渲染模板输出 |

**关键数据规范**：附录中定义了 `analysis.json` 的完整格式规范，包含 `chain`、`news`、`positions`、`viewpoints`、`tech`、`outlook` 六大字段。

---

### 2.2 fetch_quotes.py — 行情数据采集

**职责**：从东方财富 API 采集国内商品期货全品种行情数据与宏观指标，计算重要比值，输出结构化 JSON。

#### 关键常量

| 常量 | 说明 |
|------|------|
| `ALLOWED_DOMAINS` | HTTP 请求白名单域名（安全策略） |
| `EXCHANGE_MAP` | 6 大交易所名称 → 市场代码映射 |
| `SECTOR_MAP` | 11 个板块 → 品种代码列表映射 |
| `MACRO_SECID_MAP` | 宏观指标名称 → secid 映射 |
| `FUTURES_FIELDS` | API 请求字段列表 |
| `MAIN_CONTRACT_SUFFIX` | 主力合约后缀 `"m"` |
| `SYMBOL_NAME_SECTOR` | 特殊品种名称→板块映射（解决"棕榈油/普麦"代码冲突） |

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `_validate_url` | `(url: str) -> str` | URL 安全校验：仅允许 HTTPS + 白名单域名 |
| `_http_get` | `(url: str) -> dict` | HTTP GET 请求，自动处理 JSONP 回调，强制 SSL 证书验证 |
| `fetch_exchange_data` | `(market_code: int, page_size: int) -> list` | 按交易所代码获取期货合约列表 |
| `fetch_macro_indicators` | `() -> list` | 获取美元指数、原油、黄金等宏观指标 |
| `is_main_contract` | `(dm: str) -> bool` | 判断是否为主力合约（以 `m` 结尾） |
| `_safe_float` / `_safe_int` | `(val, default) -> number` | 安全类型转换，处理 None / 空字符串 / `-` |
| `parse_futures_record` | `(item: dict) -> dict` | 解析单条期货记录，计算持仓变化与投机度 |
| `classify_by_sector` | `(futures_list: list) -> tuple[dict, list]` | 将主力合约按板块分类，返回 `(sector_data, uncategorized)` |
| `add_key_commodities_to_macro` | `(futures_list, macro_indicators) -> list` | 将螺纹钢、沪铜等关键品种添加到宏观指标 |
| `calc_ratios` | `(futures_list, macro_indicators) -> dict` | 计算跨品种比值/价差（金银比、螺矿比、猪粮比等 16 项） |
| `validate_data` | `(futures_list: list) -> list` | 异常波动检测（涨跌幅 > ±5%） |
| `find_star_products` | `(futures_list: list) -> dict` | 筛选日内明星品种 Top 3 |
| `main` | `() -> None` | 主流程：采集 → 解析 → 分类 → 计算 → 输出 JSON |

#### 数据流

```
东方财富 API (6大交易所 + 宏观指标)
    │
    ▼
fetch_exchange_data / fetch_macro_indicators
    │
    ▼
parse_futures_record (逐条解析)
    │
    ▼
classify_by_sector (板块分类)
    │
    ▼
calc_ratios (比值计算) + validate_data (异常检测) + find_star_products (明星品种)
    │
    ▼
quotes_YYYYMMDD_HHMMSS.json
```

#### 输出 JSON 结构

```json
{
  "fetch_time": "2026-05-22 15:00:00",
  "domestic_futures": [...],
  "macro_indicators": [...],
  "sector_data": { "黑色系": [...], "有色金属": [...], ... },
  "uncategorized": [...],
  "ratios": { "金银比": {"value": 85.2, "meaning": "..."}, ... },
  "alerts": [...],
  "star_products": {
    "top_gain": [...], "top_loss": [...],
    "top_hold_change": [...], "top_speculation": [...]
  }
}
```

---

### 2.3 fetch_calendar.py — 财经日历采集

**职责**：获取全球经济数据发布日历，供报告"财经日历"板块使用。

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_timestamp` | `() -> str` | 获取当前时间戳字符串 |
| `fetch_from_eastmoney` | `() -> dict` | 返回东方财富财经日历数据源信息 |
| `fetch_from_sina` | `() -> dict` | 返回新浪财经数据源信息 |
| `parse_eastmoney_data` | `(raw_text: str) -> list` | 解析东方财富表格格式数据 |
| `parse_sina_data` | `(raw_text: str) -> list` | 解析新浪财经文本格式数据 |
| `save_calendar` | `(events: list, filename: str) -> str` | 保存日历数据到 JSON |
| `main` | `() -> str` | 主流程，输出示例格式 JSON |

#### 数据源

| 来源 | URL | 获取方式 |
|------|-----|---------|
| 东方财富 | `https://forex.eastmoney.com/fc.html` | tavily_extract |
| 新浪财经 | `http://rl.cj.sina.com.cn/` | browser_use |

#### 输出格式

```json
[
  {"time": "09:30", "event": "中国 工业企业利润总额", "impact": "neutral"},
  {"time": "15:00", "event": "美国 CPI数据", "impact": "neutral"}
]
```

---

### 2.4 report_generator.py — HTML 报告生成引擎

**职责**：读取行情数据 JSON + 分析数据 JSON + 财经日历 JSON，基于 HTML 模板渲染最终报告。

#### 关键常量

| 常量 | 说明 |
|------|------|
| `SECTOR_ORDER` | 板块渲染顺序（11 个板块） |
| `SECTOR_EMOJI` | 板块对应 emoji 图标 |
| `CHAIN_MAP` | 各板块产业链上/中/下游描述（静态数据） |

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `format_number` | `(val, decimal=2) -> str` | 通用数字格式化 |
| `format_volume` | `(val) -> str` | 成交量格式化（亿/万单位） |
| `format_turnover` | `(val) -> str` | 成交额格式化 |
| `change_class` | `(val) -> str` | 返回涨跌 CSS 类名（`up`/`down`/`flat`） |
| `change_prefix` | `(val) -> str` | 正数前缀 `+` |
| `determine_sentiment` | `(futures_list) -> tuple` | 判断市场整体情绪（偏多/偏空/震荡/分化） |
| `build_macro_cards` | `(macro_indicators) -> str` | 生成宏观指标卡片 HTML |
| `build_ratio_items` | `(ratios) -> str` | 生成比值分析项 HTML |
| `build_sector_nav_links` | `() -> str` | 生成板块导航链接 |
| `build_sector_table` | `(futures_list) -> str` | 生成板块行情表格 HTML |
| `build_sector_stats` | `(futures_list) -> str` | 生成板块涨跌统计 HTML |
| `build_chain_analysis` | `(sector_name, analysis_data) -> str` | 生成产业链分析 HTML |
| `build_news_list` | `(news_items) -> str` | 生成资讯列表 HTML |
| `build_position_table` | `(position_data) -> str` | 生成机构持仓表格 HTML |
| `build_viewpoint_section` | `(viewpoints) -> str` | 生成机构观点卡片 HTML |
| `build_tech_section` | `(tech_data) -> str` | 生成技术形态分析 HTML |
| `build_outlook_section` | `(outlook_data) -> str` | 生成后市展望 HTML |
| `build_sector_section` | `(sector_name, futures_list, sector_analysis) -> str` | 组装完整板块区域 HTML |
| `build_star_card` | `(item, detail) -> str` | 生成明星品种卡片 HTML |
| `build_calendar_items` | `(calendar_data) -> str` | 生成财经日历表格 HTML |
| `generate_report` | `(quotes_data, analysis_data, calendar_data, version) -> str` | 核心函数：模板渲染 + 文件输出 |
| `find_latest_quotes` | `() -> str` | 自动查找最新的行情 JSON 文件 |
| `main` | `() -> None` | CLI 入口，解析参数并执行报告生成 |

#### CLI 参数

```bash
python scripts/report_generator.py \
  --quotes scripts/quotes_YYYYMMDD_HHMMSS.json \  # 行情数据（必须）
  --analysis analysis.json \                        # 分析数据（可选）
  --calendar calendar.json \                        # 财经日历（可选）
  --version "收盘版"                                 # 报告版本
```

#### 模板占位符

| 占位符 | 替换内容 |
|--------|---------|
| `{{REPORT_DATE}}` | 报告日期 |
| `{{REPORT_VERSION}}` | 版本标识 |
| `{{GENERATE_TIME}}` | 生成时间戳 |
| `{{SECTOR_NAV_LINKS}}` | 板块导航链接 |
| `{{SENTIMENT_CLASS}}` | 情绪 CSS 类名 |
| `{{SENTIMENT_TEXT}}` | 情绪文字 |
| `{{MACRO_CARDS}}` | 宏观指标卡片 |
| `{{RATIO_ITEMS}}` | 比值分析项 |
| `{{SECTOR_SECTIONS}}` | 各板块完整 HTML |
| `{{STAR_GAIN_CARDS}}` | 涨幅榜明星卡片 |
| `{{STAR_LOSS_CARDS}}` | 跌幅榜明星卡片 |
| `{{STAR_HOLD_CARDS}}` | 增仓榜明星卡片 |
| `{{STAR_SPEC_CARDS}}` | 投机度榜明星卡片 |
| `{{CALENDAR_ITEMS}}` | 财经日历表格 |

#### 输出规则

| 版本 | 文件名 | 输出路径 |
|------|--------|---------|
| 盘中版 | `期货分析_YYYYMMDD_盘中.html` | `~/Desktop/` |
| 收盘版 | `期货分析_YYYYMMDD_收盘.html` | `~/Desktop/` |
| 夜盘前瞻版 | `期货分析_YYYYMMDD_夜盘.html` | `~/Desktop/` |
| 周末版 | `期货分析_YYYYMMDD_周末.html` | `~/Desktop/` |

> 若桌面目录不可写，降级输出到项目根目录。可通过环境变量 `REPORT_OUTPUT_DIR` 自定义输出路径。

---

### 2.5 references/ — 参考知识库

#### Exchanges.md

全球主要交易所与央行官方链接索引，涵盖：
- **交易所**（22 家）：SSE、SZSE、HKEX、CFFEX、DCE、ZCE、SHFE、NYSE、NASDAQ、CME、CBOE、ICE、LSE、Euronext、Deutsche Börse、TSE、SGX、ASX、TSX、BSE、NSE
- **央行**（20 家）：Fed、ECB、BoE、BoJ、PBOC、SNB、BoC、RBA、RBNZ、BOK、MAS、RBI、BCB、Banxico、SARB、CBR、HKMA、BIS、IMF

#### Ratio.md

国内大宗商品期货重要比值/价差关系知识库，按产业链分类：

| 产业链 | 比值/价差 |
|--------|----------|
| 黑色产业链 | 螺矿比、螺焦比、钢厂利润、卷螺差 |
| 农产品-油脂 | 豆棕价差、菜豆价差、菜棕价差 |
| 农产品-饲料 | 豆粕/玉米比、豆菜粕价差 |
| 能源化工 | 油煤比、甲醇/尿素比、PP/甲醇比 |
| 贵金属与宏观 | 金银比、铜金比、金油比 |

---

### 2.6 analysis.json — 板块分析数据模板

**职责**：定义 AI Agent 通过 tavily_search 采集后整理的板块分析数据格式，供 `report_generator.py` 读取。

#### 数据结构

```json
{
  "板块名": {
    "chain": {
      "upstream_analysis": "上游原料端分析文本",
      "midstream_analysis": "中游生产端分析文本",
      "downstream_analysis": "下游需求端分析文本",
      "logic_chain": "产业链逻辑传导链"
    },
    "news": [
      {"title": "", "source": "", "impact": "up|down|neutral", "interpretation": ""}
    ],
    "positions": [
      {"seat": "", "long_change": 0, "short_change": 0, "net_change": 0}
    ],
    "viewpoints": [
      {"type": "bull|bear|neutral", "content": ""}
    ],
    "tech": {
      "品种支撑": "价格区间",
      "品种压力": "价格区间",
      "趋势判断": "多头/空头/震荡"
    },
    "outlook": {
      "trend": "短期走势预判",
      "drivers": "核心驱动因素",
      "risk": "风险提示"
    }
  }
}
```

---

## 3. 依赖关系

### 3.1 外部 API 依赖

| API | 域名 | 用途 | 白名单 |
|-----|------|------|--------|
| 期货行情列表 | `futsseapi.eastmoney.com` | 6 大交易所行情数据 | ✅ |
| 宏观指标推送 | `push2.eastmoney.com` | 美元指数、原油、黄金等 | ✅ |
| 历史数据推送 | `push2his.eastmoney.com` | 历史行情数据 | ✅ |
| 财经日历 | `forex.eastmoney.com` | 全球经济数据发布 | ❌（tavily_extract） |
| 财经日历 | `rl.cj.sina.com.cn` | 新浪财经日历 | ❌（browser_use） |

### 3.2 Python 标准库依赖

| 模块 | 使用位置 |
|------|---------|
| `json` | 全部脚本 |
| `datetime` | fetch_quotes.py, report_generator.py, fetch_calendar.py |
| `sys` | fetch_quotes.py, report_generator.py |
| `os` | 全部脚本 |
| `ssl` | fetch_quotes.py（HTTPS 证书验证） |
| `re` | fetch_quotes.py（JSONP 解析）, fetch_calendar.py, report_generator.py |
| `urllib.parse` | fetch_quotes.py（URL 校验） |
| `urllib.request` | fetch_quotes.py（HTTP 请求） |
| `glob` | report_generator.py（文件查找） |

### 3.3 可选依赖

| 模块 | 用途 | 使用位置 |
|------|------|---------|
| `pyppeteer` | 浏览器自动化（财经日历） | fetch_calendar.py（可选，`BROWSER_AVAILABLE` 标志） |

### 3.4 外部工具依赖

| 工具 | 用途 |
|------|------|
| `tavily_research` | 深度搜索板块资讯与产业链分析（优先使用） |
| `tavily_search` | 单次搜索模式（tavily_research 配额耗尽时降级使用） |

---

## 4. 板块与品种覆盖范围

项目覆盖 **11 个板块**，涉及 **70+ 个期货品种**：

| 板块 | 品种代码 | 数量 |
|------|---------|------|
| 黑色系 | RB, HC, ss, I, SF, SM, wr | 7 |
| 有色金属 | CU, AL, ZN, PB, NI, SN, ao, ad, bc | 9 |
| 能源金属 | si, lc, ps | 3 |
| 能源化工 | SC, FU, BU, MA, EG, TA, PP, ppf, V, vf, EB, UR, SA, PG, SP, RU, L, lf, op, fb, NR, br, LU, LG, BZ, bb | 26 |
| 油脂油料 | M, RM, y, p, OI, PK, b | 7 |
| 农产品 | LH, JD, AP, CJ | 4 |
| 谷物 | c, cs, a, rr, WH, PM | 6 |
| 软商 | CF, SR, CY | 3 |
| 贵金属 | AU, AG | 2 |
| 航运 | EC | 1 |
| 煤炭板块 | JM, J, ZC | 3 |

---

## 5. 比值/价差计算体系

`calc_ratios` 函数计算 **16 项** 跨品种比值/价差，按产业链分组：

### 黑色产业链

| 名称 | 公式 | 参考区间 |
|------|------|---------|
| 钢厂利润 | 螺纹 - 1.6×铁矿 - 0.5×焦炭 | 均值回归 |
| 螺矿比 | 螺纹 / 铁矿 | 4-6 |
| 螺焦比 | 螺纹 / 焦炭 | 1.8-2.2 |
| 卷螺差 | 螺纹 - 热卷 | -200~+300 元/吨 |

### 贵金属与宏观

| 名称 | 公式 | 参考区间 |
|------|------|---------|
| 金银比 | COMEX黄金 / COMEX白银 | 55-65，>80 白银低估 |
| 金油比 | COMEX黄金 / NYMEX原油 | 极端值对应市场拐点 |
| 铜金比 | 沪铜 / COMEX黄金 | 上升预示经济复苏 |

### 油脂类

| 名称 | 公式 | 参考区间 |
|------|------|---------|
| 豆棕价差 | 豆油 - 棕榈油 | 500~1500 元/吨 |
| 菜豆价差 | 菜油 - 豆油 | 300-800 元/吨 |
| 菜棕价差 | 菜油 - 棕榈油 | 800-2000 元/吨 |

### 饲料类

| 名称 | 公式 |
|------|------|
| 豆粕/玉米比 | 豆粕 / 玉米 |
| 豆菜粕价差 | 豆粕 - 菜粕 |

### 能源化工

| 名称 | 公式 |
|------|------|
| 油煤比 | 原油 / 动力煤 |
| 甲醇/尿素比 | 甲醇 / 尿素 |
| PP/甲醇比 | 聚丙烯 / 甲醇 |

### 生猪产业链

| 名称 | 公式 |
|------|------|
| 猪粮比 | 生猪 / 玉米 |

---

## 6. 安全机制

### 6.1 网络请求安全

- **域名白名单**：`_validate_url` 函数强制校验请求域名必须在 `ALLOWED_DOMAINS` 列表中
- **HTTPS 强制**：仅允许 HTTPS 协议，拒绝 HTTP
- **SSL 证书验证**：`ssl.CERT_REQUIRED` + `check_hostname=True`
- **User-Agent 标识**：所有请求携带 `FuturesAnalyst/1.0` UA

### 6.2 数据安全

- **安全类型转换**：`_safe_float` / `_safe_int` 防止异常数据导致崩溃
- **数据缺失标记**：比值计算中数据不可用时标记为"数据暂缺"，不编造数据
- **异常波动标注**：涨跌幅超 ±5% 自动标注"⚠️ 异常波动"

---

## 7. 项目运行方式

### 7.1 完整执行流程

```bash
# 步骤 1：采集期货行情数据
python scripts/fetch_quotes.py
# 输出：scripts/quotes_YYYYMMDD_HHMMSS.json

# 步骤 2：采集财经日历（可选）
python scripts/fetch_calendar.py
# 输出：scripts/calendar_YYYYMMDD_HHMMSS.json

# 步骤 3：AI Agent 通过 tavily_search 采集板块资讯
# 整理为 analysis.json 格式（手动或自动）

# 步骤 4：生成 HTML 报告
python scripts/report_generator.py \
  --quotes scripts/quotes_YYYYMMDD_HHMMSS.json \
  --analysis scripts/analysis.json \
  --calendar scripts/calendar_YYYYMMDD_HHMMSS.json \
  --version "收盘版"
# 输出：~/Desktop/期货分析_YYYYMMDD_收盘.html
```

### 7.2 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OUTPUT_DIR` | `scripts/` 目录 | 行情 JSON 输出目录 |
| `REPORT_OUTPUT_DIR` | `~/Desktop/` | HTML 报告输出目录 |

### 7.3 报告版本自动判断

| 时间段 | 版本 |
|--------|------|
| 交易日 09:00 - 15:00 | 盘中版 |
| 交易日 15:00 - 19:00 | 收盘版 |
| 交易日 19:00 - 次日 20:50 | 夜盘前瞻版 |
| 周六 | 当周总结版 |
| 周日 | 下周展望版 |

---

## 8. HTML 报告结构

生成的报告包含以下完整结构：

```
1. 封面信息（标题、日期、版本、时间戳）
2. 市场情绪（整体情绪 + 8 个宏观指标卡片）
3. 重要比值分析（16 项比值/价差）
4. 各板块分析（11 个板块，每个含 6 个子模块）
   ├── 4.1 行情总览（表格 + 涨跌统计）
   ├── 4.2 产业链分析（上/中/下游 + 逻辑链）
   ├── 4.3 重要资讯影响
   ├── 4.4 机构持仓追踪（席位表 + 观点卡片）
   ├── 4.5 技术形态
   └── 4.6 后市展望
5. 日内明星品种（4 个维度 Top 3 深度解读）
6. 财经日历
7. 免责声明
```

---

## 9. 代码质量注意事项

### 9.1 已知问题

1. **`calc_ratios` 函数重复定义**：[fetch_quotes.py](file:///Users/wangcheng/Desktop/financial-skill/financial-analysis/futures-analyst/scripts/fetch_quotes.py) 中 `calc_ratios` 被定义了两次（第 272 行和第 360 行），Python 会使用后定义的版本覆盖前者。第一个定义（第 272-356 行）包含多余的 `return ratios` 和死代码。

2. **死代码**：`calc_ratios` 函数内部第 491-540 行存在第三段重复的比值计算逻辑，位于 `return ratios` 之后，永远不会执行。

3. **`assets/` 目录缺失**：`report_generator.py` 引用 `assets/report_template.html`，但该目录和文件在当前项目中不存在，运行时会报错退出。

4. **`fetch_calendar.py` 功能不完整**：该脚本仅输出示例格式 JSON，实际数据获取依赖外部工具（tavily_extract / browser_use），脚本本身不直接发起网络请求。

5. **`determine_sentiment` 条件判断**：`report_generator.py` 第 167 行 `"五债当季" or "五债当季" or "一债当季" or "三十债当季" in name` 存在逻辑错误，前三个字符串在布尔上下文中始终为 True。
