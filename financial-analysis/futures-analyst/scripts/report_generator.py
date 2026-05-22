import json
from datetime import datetime, timedelta
import sys
import os
import re
import glob

SECTOR_ORDER = [
    "黑色系", "有色金属", "能源金属", "能源化工",
    "油脂油料", "农产品", "谷物", "软商",
    "贵金属", "航运", "煤炭板块",
]

SECTOR_EMOJI = {
    "黑色系": "🔩", "有色金属": "🟤", "能源金属": "⚡",
    "能源化工": "🛢️", "油脂油料": "🫘", "农产品": "🐷",
    "谷物": "🌾", "软商": "🧶", "贵金属": "🥇",
    "航运": "🚢", "煤炭板块": "⛏️",
}

CHAIN_MAP = {
    "黑色系": {
        "upstream": "铁矿石、焦煤、焦炭、铬矿、镍矿",
        "midstream": "炼铁、炼钢、钢材轧制、型材加工、不锈钢冶炼、线材拉拔",
        "downstream": "房地产开发、基础设施建设、汽车制造、机械制造、家电制造",
    },
    "有色金属": {
        "upstream": "铜矿、铝土矿、锌矿、铅矿、镍矿、锡矿",
        "midstream": "铜冶炼、铝冶炼、锌冶炼、铅冶炼、镍冶炼、锡冶炼",
        "downstream": "电力电网、新能源汽车、房地产建筑、电子产品、航空航天",
    },
    "能源金属": {
        "upstream": "硅石矿开采、锂矿开采、锂辉石、锂云母、盐湖提锂",
        "midstream": "工业硅冶炼、碳酸锂提炼、多晶硅提纯、锂盐生产",
        "downstream": "光伏产业、新能源汽车、锂电池、半导体、储能系统",
    },
    "能源化工": {
        "upstream": "原油开采、天然气开采、煤炭开采",
        "midstream": "石油炼化、基础化工、有机化工、煤化工、化肥生产",
        "downstream": "交通运输、房地产建材、汽车制造、农业种植、纺织化纤",
    },
    "油脂油料": {
        "upstream": "大豆种植、油菜种植、花生种植、油棕种植、进口大豆",
        "midstream": "大豆压榨、菜籽压榨、油脂精炼、棕榈油分提、饲料加工",
        "downstream": "畜禽养殖、水产养殖、食用油消费、食品加工、餐饮行业",
    },
    "农产品": {
        "upstream": "饲料生产、种猪繁育、蛋鸡养殖、果树种植",
        "midstream": "生猪养殖、蛋鸡养殖、水果种植、屠宰加工、冷链物流",
        "downstream": "猪肉消费、蛋类消费、鲜果零售、食品加工、餐饮行业",
    },
    "谷物": {
        "upstream": "种子研发、化肥农药、农业机械、谷物种植",
        "midstream": "谷物收购、仓储物流、稻谷加工、小麦加工、玉米加工",
        "downstream": "饲料加工、面粉加工、大米消费、酿酒工业、食品加工",
    },
    "软商": {
        "upstream": "棉花种植、甘蔗种植、甜菜种植",
        "midstream": "棉花加工、棉纱纺制、白糖提炼、棉纺织造",
        "downstream": "服装制造、家纺用品、糖果饮料、烘焙食品、零售批发",
    },
    "贵金属": {
        "upstream": "金矿开采、银矿开采、贵金属回收",
        "midstream": "金冶炼、银冶炼、贵金属加工、金银提纯",
        "downstream": "珠宝首饰、投资储备、电子工业、医疗器械、光伏产业",
    },
    "航运": {
        "upstream": "船舶制造、燃油供应、港口建设、集装箱制造",
        "midstream": "集装箱运输、船舶运营、港口装卸、航运代理",
        "downstream": "国际贸易、跨境电商、制造业出口、大宗商品贸易",
    },
    "煤炭板块": {
        "upstream": "煤炭开采、煤矿建设、地质勘探",
        "midstream": "煤炭洗选、焦化生产、火力发电、煤炭加工",
        "downstream": "钢铁冶炼、化工生产、电力供应、建材生产、民用供暖",
    },
}


def format_number(val, decimal=2):
    if val is None or val == 0:
        return "0"
    if isinstance(val, float):
        return f"{val:.{decimal}f}"
    return str(val)


def format_volume(val):
    if val is None or val == 0:
        return "0"
    if val >= 1e8:
        return f"{val/1e8:.2f}亿"
    if val >= 1e4:
        return f"{val/1e4:.2f}万"
    return str(int(val))


def format_turnover(val):
    if val is None or val == 0:
        return "0"
    if val >= 1e8:
        return f"{val/1e8:.2f}亿"
    if val >= 1e4:
        return f"{val/1e4:.2f}万"
    return str(int(val))


def change_class(val):
    if val > 0:
        return "up"
    if val < 0:
        return "down"
    return "flat"


def change_prefix(val):
    if val > 0:
        return "+"
    return ""


def determine_sentiment(futures_list):
    if not futures_list:
        return "sentiment-oscillate", "震荡", "暂无足够数据判断市场情绪"
    main = [f for f in futures_list if f.get("is_main", False)]
    if not main:
        return "sentiment-oscillate", "震荡", "暂无足够数据判断市场情绪"
    up = sum(1 for f in main if f.get("change_pct", 0) > 0)
    down = sum(1 for f in main if f.get("change_pct", 0) < 0)
    flat = len(main) - up - down
    total = len(main)
    ratio = (up - down) / total if total > 0 else 0
    if ratio > 0.3:
        cls, txt = "sentiment-bull", "偏多"
    elif ratio < -0.3:
        cls, txt = "sentiment-bear", "偏空"
    elif abs(ratio) <= 0.1:
        cls, txt = "sentiment-oscillate", "震荡"
    else:
        cls, txt = "sentiment-mixed", "分化"
    overview = f"今日主力合约中，上涨 {up} 只，下跌 {down} 只，持平 {flat} 只，市场整体{txt}。"
    return cls, txt, overview


def build_macro_cards(macro_indicators):
    cards = []
    for item in macro_indicators:
        name = item.get("name", "")
        latest = item.get("latest", 0)
        change_pct = item.get("change_pct", 0)
        change_amt = item.get("change_amt", 0)
        cls = change_class(change_pct)
        prefix = change_prefix(change_pct)
        direction = ""
        if name in ("美元指数",):
            direction = "美元走强→商品承压" if change_pct > 0 else "美元走弱→商品获支撑"
        elif name in ("美元兑离岸人民币",):
            direction = "人民币贬值→内盘偏强" if change_pct > 0 else "人民币升值→内盘偏弱"
        elif "原油" in name:
            direction = "能化成本支撑" if change_pct > 0 else "能化成本下移"
        elif "黄金" in name or "白银" in name:
            direction = "避险情绪升温" if change_pct > 0 else "避险情绪降温"
        elif "沪深" in name or "上证" in name or "道琼斯" in name or "恒生" in name or "A50" in name:
            direction = "风险偏好提升" if change_pct > 0 else "风险偏好下降"
        elif "期货综合指数" in name or "商品指数" in name:
            direction = "增长与通胀预期升温→风险偏好上升" if change_pct > 0 else "需求担忧加剧→避险偏好上升"
        elif "国债期货" in name or "五债当季" or "五债当季"or "一债当季"or "三十债当季"in name:
            direction = "避险升温" if change_pct > 0 else "避险降温"
        elif "铜" in name:
            direction = "经济预期向好" if change_pct > 0 else "经济预期转弱"
        elif "螺纹钢" in name:
            direction = "风险偏好上升" if change_pct > 0 else "避险偏好上升"

        cards.append(
            f'<div class="macro-card">'
            f'<div class="label">{name}</div>'
            f'<div class="value">{format_number(latest)}</div>'
            f'<div class="change {cls}">{prefix}{format_number(change_pct)}%</div>'
            f'<div class="direction">{direction}</div>'
            f'</div>'
        )
    return "\n".join(cards)


def build_ratio_items(ratios):
    items = []
    for name, ratio_data in ratios.items():
        # Handle both old format (plain value) and new format (dict with value+meaning)
        if isinstance(ratio_data, dict):
            value = ratio_data.get("value", ratio_data)
            meaning = ratio_data.get("meaning", "")
        else:
            value = ratio_data
            meaning = ""
        
        if meaning:
            items.append(
                f'<div class="ratio-item">'
                f'<div class="label">{name}</div>'
                f'<div class="value">{value}</div>'
                f'<div class="meaning">{meaning}</div>'
                f'</div>'
            )
        else:
            items.append(
                f'<div class="ratio-item">'
                f'<div class="label">{name}</div>'
                f'<div class="value">{value}</div>'
                f'</div>'
            )
    return "\n".join(items)


def build_sector_nav_links():
    links = []
    for sector in SECTOR_ORDER:
        anchor = f"sector-{sector}"
        links.append(f'<a href="#{anchor}">{sector}</a>')
    return "\n".join(links)


def build_sector_table(futures_list):
    if not futures_list:
        return '<p style="color:#999">暂无数据</p>'
    rows = []
    for item in futures_list:
        name = item.get("name", "")
        latest = item.get("latest", 0)
        change_pct = item.get("change_pct", 0)
        change_amt = item.get("change_amt", 0)
        vol = item.get("volume", 0)
        ccl = item.get("open_interest", 0)
        hold_change = item.get("hold_change", 0)
        spec = item.get("speculation", 0)
        turnover = item.get("turnover", 0)
        cls = change_class(change_pct)
        prefix = change_prefix(change_pct)
        alert = ""
        if abs(change_pct) > 5:
            alert = '<span class="alert-badge">⚠️ 异常波动</span>'
        hold_cls = change_class(hold_change)
        hold_prefix = change_prefix(hold_change)
        rows.append(
            f'<tr>'
            f'<td>{name}{alert}</td>'
            f'<td>{format_number(latest)}</td>'
            f'<td class="{cls}">{prefix}{format_number(change_pct)}%</td>'
            f'<td class="{cls}">{prefix}{format_number(change_amt)}</td>'
            f'<td>{format_volume(vol)}</td>'
            f'<td>{format_volume(ccl)}</td>'
            f'<td class="{hold_cls}">{hold_prefix}{format_volume(hold_change)}</td>'
            f'<td>{format_number(spec)}</td>'
            f'<td>{format_turnover(turnover)}</td>'
            f'</tr>'
        )
    return (
        f'<table><thead><tr>'
        f'<th>品种</th><th>最新价</th><th>涨跌幅</th><th>涨跌额</th>'
        f'<th>成交量</th><th>持仓量</th><th>日增仓</th><th>投机度</th>'
        f'<th>成交额</th>'
        f'</tr></thead><tbody>'
        + "".join(rows) + "</tbody></table>"
    )


def build_sector_stats(futures_list):
    up = sum(1 for f in futures_list if f.get("change_pct", 0) > 0)
    down = sum(1 for f in futures_list if f.get("change_pct", 0) < 0)
    flat = len(futures_list) - up - down
    return (
        f'<div class="sector-stats">'
        f'<span class="stat-up">上涨 {up}</span>'
        f'<span class="stat-down">下跌 {down}</span>'
        f'<span class="stat-flat">持平 {flat}</span>'
        f'</div>'
    )


def build_chain_analysis(sector_name, analysis_data=None):
    chain = CHAIN_MAP.get(sector_name, {})
    upstream = chain.get("upstream", "数据暂缺")
    midstream = chain.get("midstream", "数据暂缺")
    downstream = chain.get("downstream", "数据暂缺")

    upstream_analysis = "数据暂缺"
    midstream_analysis = "数据暂缺"
    downstream_analysis = "数据暂缺"
    logic_chain = "数据暂缺"

    if analysis_data:
        upstream_analysis = analysis_data.get("upstream_analysis", "数据暂缺")
        midstream_analysis = analysis_data.get("midstream_analysis", "数据暂缺")
        downstream_analysis = analysis_data.get("downstream_analysis", "数据暂缺")
        logic_chain = analysis_data.get("logic_chain", "数据暂缺")

    return (
        f'<div class="card-title">产业链分析</div>'
        f'<div style="margin-bottom:12px"><strong>上游原料端：</strong>{upstream}</div>'
        f'<div style="margin-bottom:8px;padding-left:16px;color:#444">{upstream_analysis}</div>'
        f'<div style="margin-bottom:12px"><strong>中游生产端：</strong>{midstream}</div>'
        f'<div style="margin-bottom:8px;padding-left:16px;color:#444">{midstream_analysis}</div>'
        f'<div style="margin-bottom:12px"><strong>下游需求端：</strong>{downstream}</div>'
        f'<div style="margin-bottom:8px;padding-left:16px;color:#444">{downstream_analysis}</div>'
        f'<div style="margin-bottom:8px"><strong>逻辑链传导：</strong></div>'
        f'<div style="padding-left:16px;color:#444">{logic_chain}</div>'
    )


def build_news_list(news_items):
    if not news_items:
        return '<p style="color:#999">暂无资讯数据</p>'
    items = []
    for news in news_items:
        title = news.get("title", "")
        source = news.get("source", "")
        impact = news.get("impact", "neutral")
        interpretation = news.get("interpretation", "")
        impact_cls = {
            "up": "impact-up", "down": "impact-down", "neutral": "impact-neutral"
        }.get(impact, "impact-neutral")
        impact_label = {"up": "利多", "down": "利空", "neutral": "中性"}.get(impact, "中性")
        items.append(
            f'<div class="news-item">'
            f'<div class="news-title">{title}</div>'
            f'<div class="news-meta">来源：{source} '
            f'<span class="news-impact {impact_cls}">{impact_label}</span></div>'
            f'<div style="margin-top:4px;color:#444;font-size:13px">{interpretation}</div>'
            f'</div>'
        )
    return "\n".join(items)


def build_position_table(position_data):
    if not position_data:
        return '<p style="color:#999">暂无持仓数据</p>'
    rows = []
    for pos in position_data:
        seat = pos.get("seat", "")
        long_chg = pos.get("long_change", 0)
        short_chg = pos.get("short_change", 0)
        net_chg = pos.get("net_change", 0)
        long_cls = change_class(long_chg)
        short_cls = change_class(short_chg)
        net_cls = change_class(net_chg)
        rows.append(
            f'<tr>'
            f'<td>{seat}</td>'
            f'<td class="{long_cls}">{change_prefix(long_chg)}{format_number(long_chg)}</td>'
            f'<td class="{short_cls}">{change_prefix(short_chg)}{format_number(short_chg)}</td>'
            f'<td class="{net_cls}">{change_prefix(net_chg)}{format_number(net_chg)}</td>'
            f'</tr>'
        )
    return (
        f'<table><thead><tr>'
        f'<th>席位</th><th>多单变化</th><th>空单变化</th><th>净持仓变化</th>'
        f'</tr></thead><tbody>'
        + "".join(rows) + "</tbody></table>"
    )


def build_viewpoint_section(viewpoints):
    if not viewpoints:
        return '<p style="color:#999">暂无机构观点</p>'
    cards = []
    for vp in viewpoints:
        vtype = vp.get("type", "neutral")
        content = vp.get("content", "")
        vp_cls = {"bull": "viewpoint-bull", "bear": "viewpoint-bear", "neutral": "viewpoint-neutral"}.get(vtype, "viewpoint-neutral")
        vp_label = {"bull": "多头观点", "bear": "空头观点", "neutral": "中性观点"}.get(vtype, "中性观点")
        cards.append(
            f'<div class="viewpoint-card {vp_cls}">'
            f'<div class="viewpoint-label">{vp_label}</div>'
            f'<div>{content}</div>'
            f'</div>'
        )
    return f'<div class="viewpoint-grid">{"".join(cards)}</div>'


def build_tech_section(tech_data):
    if not tech_data:
        return '<p style="color:#999">暂无技术分析数据</p>'
    items = []
    for key, val in tech_data.items():
        items.append(
            f'<div class="tech-item">'
            f'<div class="label">{key}</div>'
            f'<div class="value">{val}</div>'
            f'</div>'
        )
    return f'<div class="tech-info">{"".join(items)}</div>'


def build_outlook_section(outlook_data):
    if not outlook_data:
        return '<p style="color:#999">暂无后市展望</p>'
    trend = outlook_data.get("trend", "数据暂缺")
    drivers = outlook_data.get("drivers", "数据暂缺")
    risk = outlook_data.get("risk", "数据暂缺")
    return (
        f'<div style="margin-bottom:8px"><strong>短期走势：</strong>{trend}</div>'
        f'<div style="margin-bottom:8px"><strong>核心驱动：</strong>{drivers}</div>'
        f'<div><strong>风险提示：</strong>{risk}</div>'
    )


def build_sector_section(sector_name, futures_list, sector_analysis=None):
    anchor = f"sector-{sector_name}"
    emoji = SECTOR_EMOJI.get(sector_name, "")
    table_html = build_sector_table(futures_list)
    stats_html = build_sector_stats(futures_list)

    analysis = sector_analysis or {}
    # 兼容两种数据结构：嵌套在 "chain" 下，或直接在板块对象下
    chain_data = analysis.get("chain") or analysis
    chain_html = build_chain_analysis(sector_name, chain_data if chain_data else None)
    news_html = build_news_list(analysis.get("news", []))
    position_html = build_position_table(analysis.get("positions", []))
    viewpoint_html = build_viewpoint_section(analysis.get("viewpoints", []))
    tech_html = build_tech_section(analysis.get("tech", {}))
    outlook_html = build_outlook_section(analysis.get("outlook", {}))
    
    # 数据校验：如果产业链分析数据不完整，输出警告
    if chain_data and chain_data.get("upstream_analysis") == "数据暂缺":
        print(f"[WARN] 板块 '{sector_name}' 缺少产业链分析数据（upstream_analysis）")
    
    # 检查各板块数据完整性
    has_chain = bool(chain_data and chain_data.get("upstream_analysis") != "数据暂缺")
    has_news = bool(analysis.get("news"))
    has_positions = bool(analysis.get("positions"))
    has_viewpoints = bool(analysis.get("viewpoints"))
    has_tech = bool(analysis.get("tech"))
    has_outlook = bool(analysis.get("outlook"))
    
    missing = []
    if not has_chain: missing.append("产业链分析")
    if not has_news: missing.append("重要资讯")
    if not has_positions: missing.append("机构持仓")
    if not has_viewpoints: missing.append("机构观点")
    if not has_tech: missing.append("技术形态")
    if not has_outlook: missing.append("后市展望")
    
    if missing:
        print(f"[WARN] 板块 '{sector_name}' 缺少: {', '.join(missing)}")

    return (
        f'<div class="card" id="{anchor}">'
        f'<div class="card-title">{emoji}{sector_name} '
        f'<span class="toggle-btn">收起 ▲</span></div>'
        f'<div class="collapsible-content">'
        f'{stats_html}'
        f'{table_html}'
        f'</div>'
        f'</div>'
        f'<div class="card">'
        f'<div class="card-title">{emoji}{sector_name} - 产业链分析 '
        f'<span class="toggle-btn">收起 ▲</span></div>'
        f'<div class="collapsible-content">'
        f'{chain_html}'
        f'</div>'
        f'</div>'
        f'<div class="card">'
        f'<div class="card-title">{emoji}{sector_name} - 重要资讯 '
        f'<span class="toggle-btn">收起 ▲</span></div>'
        f'<div class="collapsible-content">'
        f'{news_html}'
        f'</div>'
        f'</div>'
        f'<div class="card">'
        f'<div class="card-title">{emoji}{sector_name} - 机构持仓 '
        f'<span class="toggle-btn">收起 ▲</span></div>'
        f'<div class="collapsible-content">'
        f'{position_html}'
        f'{viewpoint_html}'
        f'</div>'
        f'</div>'
        f'<div class="card">'
        f'<div class="card-title">{emoji}{sector_name} - 技术形态 & 后市展望 '
        f'<span class="toggle-btn">收起 ▲</span></div>'
        f'<div class="collapsible-content">'
        f'{tech_html}'
        f'{outlook_html}'
        f'</div>'
        f'</div>'
    )


def build_star_card(item, detail=None):
    name = item.get("name", "")
    latest = item.get("latest", 0)
    change_pct = item.get("change_pct", 0)
    change_amt = item.get("change_amt", 0)
    vol = item.get("volume", 0)
    ccl = item.get("open_interest", 0)
    hold_change = item.get("hold_change", 0)
    spec = item.get("speculation", 0)
    cls = change_class(change_pct)
    prefix = change_prefix(change_pct)

    detail_text = detail or "数据暂缺"

    return (
        f'<div class="star-card">'
        f'<h4>{name} <span class="{cls}">{prefix}{format_number(change_pct)}%</span></h4>'
        f'<div class="detail">'
        f'最新价：{format_number(latest)} | 涨跌额：{prefix}{format_number(change_amt)} | '
        f'成交量：{format_volume(vol)} | 持仓量：{format_volume(ccl)} | '
        f'日增仓：{change_prefix(hold_change)}{format_volume(hold_change)} | '
        f'投机度：{format_number(spec)}'
        f'</div>'
        f'<div class="detail" style="margin-top:8px">{detail_text}</div>'
        f'</div>'
    )


def build_calendar_items(calendar_data):
    if not calendar_data:
        return '<p style="color:#999">暂无财经日历数据</p>'
    
    # 表头
    html = '''<div class="card-content">
<table class="calendar-table">
<thead><tr>
<th>时间</th>
<th>事件</th>
<th>前值</th>
<th>预测</th>
<th>公布值</th>
<th>趋势</th>
<th>重要</th>
</tr></thead>
<tbody>'''
    
    for cal in calendar_data:
        time = cal.get("time", "")
        event = cal.get("event", "")
        impact = cal.get("impact", "low")
        actual = cal.get("actual", "--")
        forecast = cal.get("forecast", "--")
        previous = cal.get("previous", "--")
        trend = cal.get("trend", "")
        
        # 趋势样式
        if trend == "上升":
            trend_html = '<span class="calendar-trend-up">↑</span>'
        elif trend == "下降":
            trend_html = '<span class="calendar-trend-down">↓</span>'
        else:
            trend_html = '<span style="color:#ccc">-</span>'
        
        # 重要性样式
        impact_cls = {"high": "calendar-impact-high", "medium": "calendar-impact-medium", "low": "calendar-impact-low"}.get(impact, "calendar-impact-low")
        impact_label = {"high": "高", "medium": "中", "low": "低"}.get(impact, "低")
        
        html += f'''<tr>
<td>{time}</td>
<td style="text-align:left;font-weight:500">{event}</td>
<td class="calendar-value calendar-previous">{previous}</td>
<td class="calendar-value calendar-forecast">{forecast}</td>
<td class="calendar-value calendar-actual">{actual}</td>
<td style="text-align:center">{trend_html}</td>
<td class="{impact_cls}">{impact_label}</td>
</tr>'''
    
    html += '</tbody></table></div>'
    return html


def generate_report(quotes_data, analysis_data=None, calendar_data=None, version="收盘版"):
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "report_template.html"
    )

    if not os.path.exists(template_path):
        print(f"[ERROR] 模板文件不存在: {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    analysis = analysis_data or {}
    calendar = calendar_data or []

    now = datetime.now()
    report_date = now.strftime("%Y年%m月%d日")
    generate_time = now.strftime("%Y-%m-%d %H:%M:%S")

    futures_list = quotes_data.get("domestic_futures", [])
    macro_indicators = quotes_data.get("macro_indicators", [])
    sector_data = quotes_data.get("sector_data", {})
    ratios = quotes_data.get("ratios", {})
    stars = quotes_data.get("star_products", {})

    sentiment_cls, sentiment_txt, _ = determine_sentiment(futures_list)

    macro_cards = build_macro_cards(macro_indicators)
    ratio_items = build_ratio_items(ratios)
    sector_nav_links = build_sector_nav_links()

    sector_sections = []
    for sector in SECTOR_ORDER:
        sector_futures = sector_data.get(sector, [])
        # 兼容多种数据格式：
        # 1. analysis["黑色系"]["chain"]["upstream_analysis"] (嵌套格式)
        # 2. analysis["黑色系"]["upstream_analysis"] (平铺格式)
        # 3. analysis["chain"]["黑色系"]["upstream_analysis"] (顶层chain格式)
        sector_analysis = analysis.get(sector, {})
        # 如果板块数据中没有 chain，但顶层有 chain.xxx，则合并
        if not sector_analysis.get("chain") and analysis.get("chain", {}).get(sector):
            top_chain = analysis["chain"][sector]
            sector_analysis = {**sector_analysis, "chain": top_chain}
        sector_sections.append(build_sector_section(sector, sector_futures, sector_analysis))

    star_gain_cards = ""
    for item in stars.get("top_gain", []):
        detail = analysis.get("star_details", {}).get(item.get("symbol", ""), "")
        star_gain_cards += build_star_card(item, detail)

    star_loss_cards = ""
    for item in stars.get("top_loss", []):
        detail = analysis.get("star_details", {}).get(item.get("symbol", ""), "")
        star_loss_cards += build_star_card(item, detail)

    star_hold_cards = ""
    for item in stars.get("top_hold_change", []):
        detail = analysis.get("star_details", {}).get(item.get("symbol", ""), "")
        star_hold_cards += build_star_card(item, detail)

    star_spec_cards = ""
    for item in stars.get("top_speculation", []):
        detail = analysis.get("star_details", {}).get(item.get("symbol", ""), "")
        star_spec_cards += build_star_card(item, detail)

    calendar_items = build_calendar_items(calendar)

    replacements = {
        "{{REPORT_DATE}}": report_date,
        "{{REPORT_VERSION}}": version,
        "{{GENERATE_TIME}}": generate_time,
        "{{SECTOR_NAV_LINKS}}": sector_nav_links,
        "{{SENTIMENT_CLASS}}": sentiment_cls,
        "{{SENTIMENT_TEXT}}": sentiment_txt,
        "{{MACRO_CARDS}}": macro_cards,
        "{{RATIO_ITEMS}}": ratio_items,
        "{{SECTOR_SECTIONS}}": "\n".join(sector_sections),
        "{{STAR_GAIN_CARDS}}": star_gain_cards,
        "{{STAR_LOSS_CARDS}}": star_loss_cards,
        "{{STAR_HOLD_CARDS}}": star_hold_cards,
        "{{STAR_SPEC_CARDS}}": star_spec_cards,
        "{{CALENDAR_ITEMS}}": calendar_items,
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    remaining = re.findall(r'\{\{[A-Z_]+\}\}', html)
    if remaining:
        print(f"[WARN] 未替换的占位符: {remaining}", file=sys.stderr)

    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    version_suffix = {"盘中版": "盘中", "收盘版": "收盘", "夜盘前瞻版": "夜盘"}.get(version, "收盘")
    filename = f"期货分析_{now.strftime('%Y%m%d')}_{version_suffix}.html"

    output_dir = os.environ.get("REPORT_OUTPUT_DIR", desktop_dir)
    if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
        output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"[WARN] 桌面目录不可写，输出至项目目录: {output_dir}", file=sys.stderr)

    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[INFO] 报告已生成: {output_path}")
    return output_path


def find_latest_quotes():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(script_dir, "quotes_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    return files[-1]


def main():
    quotes_file = None
    analysis_file = None
    calendar_file = None
    version = "收盘版"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--quotes" and i + 1 < len(args):
            quotes_file = args[i + 1]
            i += 2
        elif args[i] == "--analysis" and i + 1 < len(args):
            analysis_file = args[i + 1]
            i += 2
        elif args[i] == "--calendar" and i + 1 < len(args):
            calendar_file = args[i + 1]
            i += 2
        elif args[i] == "--version" and i + 1 < len(args):
            version = args[i + 1]
            i += 2
        else:
            i += 1

    if not quotes_file:
        quotes_file = find_latest_quotes()
        if not quotes_file:
            print("[ERROR] 未找到行情数据文件，请先运行 fetch_quotes.py", file=sys.stderr)
            sys.exit(1)

    print(f"[INFO] 读取行情数据: {quotes_file}")
    with open(quotes_file, "r", encoding="utf-8") as f:
        quotes_data = json.load(f)

    analysis_data = {}
    if analysis_file and os.path.exists(analysis_file):
        print(f"[INFO] 读取分析数据: {analysis_file}")
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)

    # 财经日历获取逻辑
    # 优先使用传入的 calendar_file，否则尝试读取最新的 calendar_*.json
    if not calendar_file:
        # 尝试查找当天最新的 calendar 文件
        today = datetime.now().strftime("%Y%m%d")
        
        # 先在当前目录找
        calendar_files = glob.glob("./calendar_*.json") + glob.glob("../scripts/calendar_*.json")
        calendar_files.sort(reverse=True)
        
        for cf in calendar_files:
            # 检查是否是今天的文件
            if f"calendar_{today}" in cf:
                calendar_file = cf
                break
            elif cf > "./calendar_latest.json":
                # 使用最新的一个
                calendar_file = cf
                break
    
    calendar_data = []
    if calendar_file and os.path.exists(calendar_file):
        print(f"[INFO] 读取日历数据: {calendar_file}")
        with open(calendar_file, "r", encoding="utf-8") as f:
            calendar_data = json.load(f)
    elif not calendar_file:
        # 如果没有找到日历文件，使用内置的默认财经日历
        print("[INFO] 未找到财经日历文件，使用内置默认数据")
        calendar_data = [
            {"time": "09:30", "event": "中国 工业企业利润总额累计同比(每月)", "impact": "neutral"},
            {"time": "09:30", "event": "中国 工业企业利润总额累计值(每月)", "impact": "neutral"},
            {"time": "15:00", "event": "西班牙 失业率(每月)", "impact": "neutral"},
            {"time": "15:00", "event": "德国 Gfk消费者信心指数(每月)", "impact": "neutral"},
            {"time": "13:00", "event": "日本 工业产出月率(每月)", "impact": "neutral"},
            {"time": "13:00", "event": "日本 零售销售(每月)", "impact": "neutral"},
            {"time": "22:30", "event": "美国 达拉斯联储制造业指数(每月)", "impact": "neutral"},
            {"time": "20:00", "event": "英国 央行利率决议(每月)", "impact": "neutral"},
            {"time": "20:30", "event": "美国 非农就业人口(每月)", "impact": "neutral"},
            {"time": "20:30", "event": "美国 失业率(每月)", "impact": "neutral"},
            {"time": "01:00", "event": "美国 API原油库存(每周)", "impact": "neutral"},
            {"time": "04:30", "event": "美国 EIA原油库存(每周)", "impact": "neutral"},
            {"time": "06:30", "event": "美国 SPDR黄金持仓(每日)", "impact": "neutral"},
            {"time": "06:30", "event": "美国 iShares白银持仓(每日)", "impact": "neutral"},
        ]

    output_path = generate_report(quotes_data, analysis_data, calendar_data, version)
    print(f"[INFO] 完成！报告路径: {output_path}")


if __name__ == "__main__":
    main()
