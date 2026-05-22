import json
import datetime
import sys
import os
import ssl
import re

ALLOWED_DOMAINS = [
    "futsseapi.eastmoney.com",
    "push2.eastmoney.com",
    "push2his.eastmoney.com",
]

EXCHANGE_MAP = {
    "上期所": 113,
    "大商所": 114,
    "郑商所": 115,
    "上期能源": 142,
    "中金所": 220,
    "广期所": 225
}

FUTURES_FIELDS = "dm,sc,name,p,zsjd,zde,zdf,f152,o,h,l,zjsj,vol,cje,wp,np,ccl,cclyk,zgcc"
SECTOR_MAP = {
    "黑色系": ["rb", "hc", "ss", "i", "sf", "sm", "wr"],
    "有色系": ["cu", "al", "zn", "pb", "ni", "sn", "ao", "ad", "bc"],
    "能源金属": ["si", "lc", "ps"],
    "能源化工": ["sc", "fu", "bu", "ma", "eg", "ta", "pp", "ppf", "v", "vf", "eb", "ur", "sa", "pg", "sp", "ru", "l", "lf", "op", "fb", "nr", "br", "lu", "lg", "bz", "bb"],
    "油脂油料": ["m", "rm", "y", "p", "oi", "pk", "b"],
    "农产品": ["lh", "jd", "ap", "cj"],
    "谷物": ["c", "cs", "a", "rr", "wh", "pm"],
    "软商": ["cf", "sr", "cy"],
    "贵金属": ["au", "ag"],
    "航运": ["ec"],
    "煤炭板块": ["jm", "j", "zc"],
}
MAIN_CONTRACT_SUFFIX = "m"
MACRO_SECID_MAP = {
    "美元指数": "100.UDI",
    "美元兑离岸人民币": "133.USDCNH",
    "A50期指当月连续": "104.CN00Y",
    "道琼斯": "100.DJIA",
    "期货综合指数": "159.EMFI",
    "十债当季": "220.TS0",
    "NYMEX原油": "102.CL00Y",
    "COMEX黄金": "101.GC00Y",
    "COMEX白银": "101.SI00Y",
    #"美国10年期国债收益率": "171.US10Y",
}

def _validate_url(url):
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise ValueError(f"Blocked: only HTTPS allowed, got {parsed.scheme}")
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError(f"Blocked: domain {parsed.hostname} not in allowlist")
    return url

def _http_get(url):
    _validate_url(url)
    import urllib.request
    ctx = ssl.create_default_context()
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = True
    req = urllib.request.Request(url, method="GET", headers={
        "User-Agent": "FuturesAnalyst/1.0",
        "Accept": "application/json",
        "Referer": "https://qhweb.eastmoney.com/",
    })
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        raw = resp.read().decode("utf-8")
        if raw.startswith("aaa_callback") or raw.startswith("jQuery"):
            raw = re.sub(r'^[a-zA-Z0-9_]+\(', '', raw)
            raw = re.sub(r'\);?$', '', raw)
        return json.loads(raw)


def fetch_exchange_data(market_code, page_size=2000):
    url = (
        f"https://futsseapi.eastmoney.com/list/{market_code}"
        f"?pageSize={page_size}&pageIndex=0&orderBy=zdf&sort=desc"
        f"&field={FUTURES_FIELDS}"
    )
    try:
        data = _http_get(url)
        return data.get("list", [])
    except Exception as e:
        print(f"[ERROR] fetch_exchange_data({market_code}): {e}", file=sys.stderr)
        return []


def fetch_macro_indicators():
    results = []
    for name, secid in MACRO_SECID_MAP.items():
        url = (
            f"https://push2.eastmoney.com/api/qt/stock/get"
            f"?ut=fa5fd1943c7b386f172d6893dbfba10b"
            f"&invt=2&fltt=2"
            f"&fields=f43,f44,f45,f46,f47,f48,f57,f58,f169,f170,f171"
            f"&secid={secid}"
        )
        try:
            data = _http_get(url)
            d = data.get("data", {})
            if d:
                results.append({
                    "name": name,
                    "secid": secid,
                    "latest": d.get("f43", 0),
                    "high": d.get("f44", 0),
                    "low": d.get("f45", 0),
                    "open": d.get("f46", 0),
                    "volume": d.get("f47", 0),
                    "amount": d.get("f48", 0),
                    "change_pct": d.get("f170", 0),
                    "change_amt": d.get("f169", 0),
                    "symbol": d.get("f57", ""),
                })
        except Exception as e:
            print(f"[WARN] fetch_macro({name}): {e}", file=sys.stderr)
            results.append({
                "name": name, "secid": secid,
                "latest": 0, "change_pct": 0, "change_amt": 0,
            })
    return results


def is_main_contract(dm):
    return dm.endswith(MAIN_CONTRACT_SUFFIX) or dm.endswith("m")


def _safe_float(val, default=0):
    if val is None or val == '' or val == '-':
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    if val is None or val == '' or val == '-':
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def parse_futures_record(item):
    dm = item.get("dm", "")
    name = item.get("name", "")
    p = _safe_float(item.get("p", 0))
    zdf = _safe_float(item.get("zdf", 0))
    vol = _safe_int(item.get("vol", 0))
    ccl = _safe_int(item.get("ccl", 0))
    cje = _safe_float(item.get("cje", 0))
    f152 = _safe_float(item.get("f152", 0))
    zjsj = _safe_float(item.get("zjsj", 0))
    zde = _safe_float(item.get("zde", 0))
    np_val = _safe_int(item.get("np", 0))
    wp_val = _safe_int(item.get("wp", 0))
    cclyk = _safe_int(item.get("cclyk", 0))
    zgcc = _safe_int(item.get("zgcc", 0))

    hold_change = cclyk if cclyk else (np_val - wp_val if np_val and wp_val else 0)
    speculation = 0
    if vol and ccl:
        speculation = round(vol / ccl, 2) if ccl > 0 else 0

    return {
        "symbol": dm,
        "name": name,
        "latest": p,
        "change_pct": zdf,
        "change_amt": zde,
        "volume": vol,
        "open_interest": ccl,
        "hold_change": hold_change,
        "speculation": float(speculation),
        "turnover": cje,
        "prev_settle": zjsj,
        "is_main": is_main_contract(dm),
    }


SYMBOL_NAME_SECTOR = {
    "pm": {"棕榈油": "油脂油料", "普麦": "谷物"},
}


def classify_by_sector(futures_list):
    sector_data = {sector: [] for sector in SECTOR_MAP}
    uncategorized = []
    all_codes = set()
    for codes in SECTOR_MAP.values():
        all_codes.update(codes)

    for item in futures_list:
        if not item.get("is_main", False):
            continue
        dm = item.get("symbol", "").lower()
        name = item.get("name", "")
        matched = False

        base = dm
        if base.endswith("m") and base not in all_codes:
            base = base[:-1]

        if base in SYMBOL_NAME_SECTOR:
            for keyword, sector in SYMBOL_NAME_SECTOR[base].items():
                if keyword in name:
                    sector_data[sector].append(item)
                    matched = True
                    break
            if matched:
                continue

        for sector, codes in SECTOR_MAP.items():
            for code in codes:
                if base == code:
                    sector_data[sector].append(item)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            uncategorized.append(item)

    return sector_data, uncategorized


def add_key_commodities_to_macro(futures_list, macro_indicators):
    """Add key commodity futures (螺纹钢, 沪铜, etc) to macro indicators from domestic futures data."""
    # Map display name -> main contract symbol
    key_symbols = {
        "螺纹钢": "rbm",   # 螺纹钢主力连续
        "沪铜": "cus",     # 沪铜主力连续
    }
    
    # Build lookup from symbol to futures data (normalized to lowercase)
    futures_by_symbol = {}
    for f in futures_list:
        sym = f.get("symbol", "").lower()
        futures_by_symbol[sym] = f
    
    # Add to macro indicators
    for name, sym in key_symbols.items():
        if sym in futures_by_symbol:
            f = futures_by_symbol[sym]
            change_pct = f.get("change_pct", 0)
            macro_indicators.append({
                "name": name,
                "secid": f"futures.{sym}",
                "latest": f.get("latest", 0),
                "high": f.get("high", 0) if f.get("high") else f.get("latest", 0),
                "low": f.get("low", 0) if f.get("low") else f.get("latest", 0),
                "open": f.get("open", 0),
                "volume": f.get("volume", 0),
                "amount": f.get("turnover", 0),
                "change_pct": change_pct,
                "change_amt": f.get("change_amt", 0),
                "symbol": sym,
            })
            print(f"[INFO] Added to macro: {name} @ {f.get('latest')} ({change_pct}%)")
    
    return macro_indicators


def calc_ratios(futures_list, macro_indicators):
    prices = {}
    for item in futures_list:
        if not item.get("is_main", False):
            continue
        name = item.get("name", "").replace("主连", "")
        dm = item.get("symbol", "").replace("m", "").upper()
        prices[name] = item.get("latest", 0)
        prices[dm] = item.get("latest", 0)

    for item in macro_indicators:
        mname = item.get("name", "")
        prices[mname] = item.get("latest", 0)

    ratios = {}

    gold = prices.get("COMEX黄金", 0)
    silver = prices.get("COMEX白银", 0)
    crude = prices.get("NYMEX原油", 0)
    rb = prices.get("螺纹钢", 0) or prices.get("RB", 0)
    i = prices.get("铁矿石", 0) or prices.get("I", 0)
    hc = prices.get("热卷", 0) or prices.get("HC", 0)
    j = prices.get("焦炭", 0) or prices.get("J", 0)
    lh = prices.get("生猪", 0) or prices.get("LH", 0)
    c = prices.get("玉米", 0) or prices.get("C", 0)
    y = prices.get("豆油", 0) or prices.get("Y", 0)
    p = prices.get("棕榈油", 0) or prices.get("P", 0)
    oi = prices.get("菜籽油", 0) or prices.get("OI", 0)
    m = prices.get("豆粕", 0) or prices.get("M", 0)
    rm = prices.get("菜籽粕", 0) or prices.get("RM", 0)
    zc = prices.get("动力煤", 0) or prices.get("ZC", 0)
    ma = prices.get("甲醇", 0) or prices.get("MA", 0)
    ur = prices.get("尿素", 0) or prices.get("UR", 0)
    pp = prices.get("聚丙烯", 0) or prices.get("PP", 0)
    cu = prices.get("沪铜", 0) or prices.get("CU", 0)

    # === 黑色产业链 ===
    if rb and i and j:
        # 模拟吨钢毛利 = 螺纹 - 1.6×铁矿 - 0.5×焦炭
        steel_profit = round(rb - 1.6 * i - 0.5 * j, 2)
        ratios["钢厂利润"] = {"value": steel_profit, "meaning": "模拟吨钢毛利，核心套利指标，利润极端值时反向操作均值回归"}
    if rb and i:
        ratios["螺矿比"] = {"value": round(rb / i, 2), "meaning": "反映钢厂原料成本压力，比值越低利润越薄，历史均值约4-6，低位做多"}
    if rb and j:
        ratios["螺焦比"] = {"value": round(rb / j, 2), "meaning": "衡量焦炭成本占比，辅助判断炼钢利润，合理区间1.8-2.2"}
    if rb and hc:
        ratios["卷螺差"] = {"value": round(rb - hc, 2), "meaning": "反映板材与长材需求强弱对比，正常区间-200~+300元/吨"}

    # === 贵金属与宏观比值 ===
    if gold and silver:
        ratios["金银比"] = {"value": round(gold / silver, 2), "meaning": "贵金属内部相对估值，避险情绪指标，历史均值55-65，>80提示白银低估"}
    if gold and crude:
        ratios["金油比"] = {"value": round(gold / crude, 2), "meaning": "衡量通胀预期与风险偏好，极端值常对应市场拐点"}
    if cu and gold:
        ratios["铜金比"] = {"value": round(cu / gold, 2), "meaning": "全球经济体温计，比值上升预示经济复苏"}

    # === 油脂类 ===
    if y and p:
        ratios["豆棕价差"] = {"value": round(y - p, 2), "meaning": "替代油脂的相对价值，常态500~1500元/吨，2024年曾现倒挂"}
    if oi and y:
        ratios["菜豆价差"] = {"value": round(oi - y, 2), "meaning": "反映菜油溢价能力及供需格局，菜油通常溢价300-800元/吨"}
    if oi and p:
        ratios["菜棕价差"] = {"value": round(oi - p, 2), "meaning": "综合判断三大油脂相对强弱，常态800-2000元/吨"}

    # === 饲料类 ===
    if m and c:
        ratios["豆粕/玉米比"] = {"value": round(m / c, 2), "meaning": "衡量饲料配方中蛋白与能量原料的相对成本"}
    if m and rm:
        ratios["豆菜粕价差"] = {"value": round(m - rm, 2), "meaning": "反映蛋白原料替代关系，水产/畜禽饲料配方调整依据"}

    # === 能源化工 ===
    if crude and zc:
        ratios["油煤比"] = {"value": round(crude / zc, 2), "meaning": "能源结构替代性指标，影响煤化工/油化工竞争力"}
    if ma and ur:
        ratios["甲醇/尿素比"] = {"value": round(ma / ur, 2), "meaning": "两者同为煤化工下游，反映氮肥与化工需求强弱"}
    if pp and ma:
        ratios["PP/甲醇比"] = {"value": round(pp / ma, 2), "meaning": "甲醇制烯烃(MTO)工艺利润参考，比值过低抑制开工"}

    # === 生猪产业链 ===
    if lh and c:
        ratios["猪粮比"] = {"value": round(lh / c, 2), "meaning": "猪粮比高于5.5养殖亏损，低于5.5仍有利润"}

    return ratios

    return ratios


# === 新版比值计算函数 ===
def calc_ratios(futures_list, macro_indicators):
    # Build prices lookup - from is_main contracts AND from "主连" contracts
    prices = {}
    for item in futures_list:
        latest = item.get("latest", 0)
        if not latest:
            continue
        
        name = item.get("name", "")
        
        # For main contracts (is_main=True)
        if item.get("is_main", False):
            clean_name = name.replace("主连", "").replace("次主连", "")
            dm = item.get("symbol", "").replace("m", "").replace("s", "").upper()
            prices[clean_name] = latest
            prices[dm] = latest
        
        # Also include contracts with "主连" in name (may not be is_main)
        if "主连" in name:
            prices[name] = latest
            # Store with simplified name too
            clean_name = name.replace("主连", "")
            prices[clean_name] = latest
    
    # Add macro indicator prices
    for item in macro_indicators:
        mname = item.get("name", "")
        prices[mname] = item.get("latest", 0)

    # Extract key prices - use multiple fallback lookups
    gold = prices.get("COMEX黄金") or prices.get("黄金") or prices.get("沪金主连") or 0
    silver = prices.get("COMEX白银") or prices.get("白银") or prices.get("沪银主连") or 0
    crude = prices.get("NYMEX原油") or prices.get("原油") or prices.get("原油主连") or 0
    
    # 黑色系
    rb = prices.get("螺纹钢") or prices.get("RB") or prices.get("螺纹钢主连") or 0
    i = prices.get("铁矿石") or prices.get("I") or prices.get("铁矿石主连") or 0
    hc = prices.get("热卷") or prices.get("HC") or prices.get("热卷主连") or 0
    j = prices.get("焦炭") or prices.get("J") or prices.get("焦炭主连") or 0
    
    # 农产品
    lh = prices.get("生猪") or prices.get("LH") or prices.get("生猪主连") or 0
    c = prices.get("玉米") or prices.get("C") or prices.get("玉米主连") or 0
    m = prices.get("豆粕") or prices.get("M") or prices.get("豆粕主连") or 0
    y = prices.get("豆油") or prices.get("Y") or prices.get("豆油主连") or 0
    p = prices.get("棕榈油") or prices.get("P") or prices.get("棕榈油主连") or 0
    oi = prices.get("菜籽油") or prices.get("菜油") or prices.get("OI") or prices.get("菜油主连") or 0
    rm = prices.get("菜籽粕") or prices.get("菜粕") or prices.get("RM") or prices.get("菜粕主连") or 0
    
    # 有色
    cu = prices.get("沪铜") or prices.get("CU") or prices.get("沪铜主连") or 0
    
    # 化工
    ma = prices.get("甲醇") or prices.get("MA") or prices.get("甲醇主连") or 0
    ur = prices.get("尿素") or prices.get("UR") or prices.get("尿素主连") or 0
    pp = prices.get("聚丙烯") or prices.get("PP") or prices.get("聚丙烯主连") or 0
    zc = prices.get("动力煤") or prices.get("ZC") or prices.get("动力煤主连") or 0

    # 黑色产业链
    ratios = {}
    if rb and i and j:
        steel_profit = round(rb - 1.6 * i - 0.5 * j, 2)
        ratios["钢厂利润"] = {"value": steel_profit, "meaning": "模拟吨钢毛利，核心套利指标，利润极端值���反向操作均值回归"}
    if rb and i:
        ratios["螺矿比"] = {"value": round(rb / i, 2), "meaning": "反映钢厂原料成本压力，比值越低利润越薄，历史均值约4-6，低位做多"}
    if rb and j:
        ratios["螺焦比"] = {"value": round(rb / j, 2), "meaning": "衡量焦炭成本占比，辅助判断炼钢利润，合理区间1.8-2.2"}
    if rb and hc:
        ratios["卷螺差"] = {"value": round(rb - hc, 2), "meaning": "反映板材与长材需求强弱对比，正常区间-200~+300元/吨"}
    else:
        ratios["卷螺差"] = {"value": "数据暂缺", "meaning": "需热卷主连数据"}

    # 贵金属
    if gold and silver:
        ratios["金银比"] = {"value": round(gold / silver, 2), "meaning": "贵金属内部相对估值，避险情绪指标，历史均值55-65，>80提示白银低估"}
    else:
        ratios["金银比"] = {"value": "数据暂缺", "meaning": "需黄金白银数据"}
    if gold and crude:
        ratios["金油比"] = {"value": round(gold / crude, 2), "meaning": "衡量通胀预期与风险偏好，极端值常对应市场拐点"}
    else:
        ratios["金油比"] = {"value": "数据暂缺", "meaning": "需黄金原油数据"}
    if cu and gold:
        ratios["铜金比"] = {"value": round(cu / gold, 2), "meaning": "全球经济体温计，比值上升预示经济复苏"}
    else:
        ratios["铜金比"] = {"value": "数据暂缺", "meaning": "需沪铜数据"}

    # 油脂类
    if y and p:
        ratios["豆棕价差"] = {"value": round(y - p, 2), "meaning": "替代油脂的相对价值，常态500~1500元/吨"}
    else:
        ratios["豆棕价差"] = {"value": "数据暂缺", "meaning": "需豆油棕榈油主连数据"}
    
    if oi and y:
        ratios["菜豆价差"] = {"value": round(oi - y, 2), "meaning": "反映菜油溢价能力及供需格局，菜油通常溢价300-800元/吨"}
    else:
        ratios["菜豆价差"] = {"value": "数据暂缺", "meaning": "需菜油数据"}
    
    if oi and p:
        ratios["菜棕价差"] = {"value": round(oi - p, 2), "meaning": "综合判断三大油脂相对强弱，常态800-2000元/吨"}
    else:
        ratios["菜棕价差"] = {"value": "数据暂缺", "meaning": "需菜油数据"}
    # 饲料类
    if m and c:
        ratios["豆粕/玉米比"] = {"value": round(m / c, 2), "meaning": "衡量饲料配方中蛋白与能量原料的相对成本"}
    else:
        ratios["豆粕/玉米比"] = {"value": "数据暂缺", "meaning": "需豆粕玉米数据"}
    if m and rm:
        ratios["豆菜粕价差"] = {"value": round(m - rm, 2), "meaning": "反映蛋白原料替代关系，水产/畜禽饲料配方调整依据"}
    else:
        ratios["豆菜粕价差"] = {"value": "数据暂缺", "meaning": "需菜粕数据"}
    # 能源化工
    if crude and zc:
        ratios["油煤比"] = {"value": round(crude / zc, 2), "meaning": "能源结构替代性指标，影响煤化工/油化工竞争力"}
    elif crude:
        ratios["油煤比"] = {"value": "数据暂缺", "meaning": "需动力煤数据"}
    else:
        ratios["油煤比"] = {"value": "数据暂缺", "meaning": "需动力煤数据"}
    if ma and ur:
        ratios["甲醇/尿素比"] = {"value": round(ma / ur, 2), "meaning": "两者同为煤化工下游，反映氮肥与化工需求强弱"}
    else:
        ratios["甲醇/尿素比"] = {"value": "数据暂缺", "meaning": "需甲醇尿素数据"}
    if pp and ma:
        ratios["PP/甲醇比"] = {"value": round(pp / ma, 2), "meaning": "甲醇制烯烃(MTO)工艺利润参考，比值过低抑制开工"}
    elif pp:
        ratios["PP/甲醇比"] = {"value": "数据暂缺", "meaning": "需甲醇数据"}
    # 生猪产业链
    if lh and c:
        ratios["猪粮比"] = {"value": round(lh / c, 2), "meaning": "猪粮比高于5.5养殖亏损，低于5.5仍有利润"}
    else:
        ratios["猪粮比"] = {"value": "数据暂缺", "meaning": "需生猪玉米数据"}
    return ratios
    # 黑色产业链
    ratios = {}
    if rb and i and j:
        steel_profit = round(rb - 1.6 * i - 0.5 * j, 2)
        ratios["钢厂利润"] = {"value": steel_profit, "meaning": "模拟吨钢毛利，核心套利指标，利润极端值时反向操作均值回归"}
    if rb and i:
        ratios["螺矿比"] = {"value": round(rb / i, 2), "meaning": "反映钢厂原料成本压力，比值越低利润越薄，历史均值约4-6，低位做多"}
    if rb and j:
        ratios["螺焦比"] = {"value": round(rb / j, 2), "meaning": "衡量焦炭成本占比，辅助判断炼钢利润，合理区间1.8-2.2"}
    if rb and hc:
        ratios["卷螺差"] = {"value": round(rb - hc, 2), "meaning": "反映板材与长材需求强弱对比，正常区间-200~+300元/吨"}
    else:
        ratios["卷螺差"] = {"value": "数据暂缺", "meaning": "需热卷主连数据"}
    # 贵金属
    if gold and silver:
        ratios["金银比"] = {"value": round(gold / silver, 2), "meaning": "贵金属内部相对估值，避险情绪指标，历史均值55-65，>80提示白银低估"}
    else:
        ratios["金银比"] = {"value": "数据暂缺", "meaning": "需黄金白银数据"}
    if gold and crude:
        ratios["金油比"] = {"value": round(gold / crude, 2), "meaning": "衡量通胀预期与风险偏好，极端值常对应市场拐点"}
    else:
        ratios["金油比"] = {"value": "数据暂缺", "meaning": "需黄金原油数据"}
    if cu and gold:
        ratios["铜金比"] = {"value": round(cu / gold, 2), "meaning": "全球经济体温计，比值上升预示经济复苏"}
    else:
        ratios["铜金比"] = {"value": "数据暂缺", "meaning": "需沪铜数据"}
    # 油脂类
    if y and p:
        ratios["豆棕价差"] = {"value": round(y - p, 2), "meaning": "替代油脂的相对价值，常态500~1500元/吨，2024年曾现倒挂"}
    else:
        ratios["豆棕价差"] = {"value": "数据暂缺", "meaning": "需豆油棕榈油主连数据"}
    # 菜油、菜籽粕国内暂无期货，暂时标记为数据暂缺
    ratios["菜豆价差"] = {"value": "数据暂缺", "meaning": "国内暂无菜籽油期货"}
    ratios["菜棕价差"] = {"value": "数据暂缺", "meaning": "国内暂无菜籽油期货"}
    # 饲料类
    if m and c:
        ratios["豆粕/玉米比"] = {"value": round(m / c, 2), "meaning": "衡量饲料配方中蛋白与能量原料的相对成本"}
    else:
        ratios["豆粕/玉米比"] = {"value": "数据暂缺", "meaning": "需豆粕玉米主连数据"}
    ratios["豆菜粕价差"] = {"value": "数据暂缺", "meaning": "国内暂无菜籽粕期货"}
    # 能源化工 - 动力煤、甲醇、尿素国内暂无期货
    ratios["油煤比"] = {"value": "数据暂缺", "meaning": "国内暂无动力煤期货(ZC)"}
    ratios["甲醇/尿素比"] = {"value": "数据暂缺", "meaning": "国内暂无甲醇/尿素期货"}
    ratios["PP/甲醇比"] = {"value": "数据暂缺", "meaning": "国内暂无甲醇期货(MA)"}
    # 生猪产业链
    if lh and c:
        ratios["猪粮比"] = {"value": round(lh / c, 2), "meaning": "猪粮比高于5.5养殖亏损，低于5.5仍有利润"}
    else:
        ratios["猪粮比"] = {"value": "数据暂缺", "meaning": "需生猪玉米主连数据"}
    return ratios
def validate_data(futures_list):
    alerts = []
    for item in futures_list:
        change = item.get("change_pct", 0)
        if abs(change) > 5:
            alerts.append({
                "symbol": item.get("symbol", ""),
                "name": item.get("name", ""),
                "change_pct": change,
                "alert": "⚠️ 异常波动",
            })
    return alerts
def find_star_products(futures_list):
    main_only = [f for f in futures_list if f.get("is_main", False)]
    sorted_by_gain = sorted(main_only, key=lambda x: x.get("change_pct", 0), reverse=True)
    sorted_by_loss = sorted(main_only, key=lambda x: x.get("change_pct", 0))
    sorted_by_hold = sorted(main_only, key=lambda x: x.get("hold_change", 0), reverse=True)
    sorted_by_spec = sorted(main_only, key=lambda x: x.get("speculation", 0), reverse=True)
    return {
        "top_gain": sorted_by_gain[:3],
        "top_loss": sorted_by_loss[:3],
        "top_hold_change": sorted_by_hold[:3],
        "top_speculation": sorted_by_spec[:3],
    }
def main():
    print("[INFO] 正在获取期货行情数据...")
    all_raw = []
    for exchange_name, market_code in EXCHANGE_MAP.items():
        print(f"[INFO] 获取 {exchange_name} (market={market_code})...")
        items = fetch_exchange_data(market_code)
        print(f"  → 获取到 {len(items)} 条记录")
        all_raw.extend(items)
    print(f"[INFO] 共获取 {len(all_raw)} 条原始记录，正在解析...")
    all_futures = []
    for item in all_raw:
        record = parse_futures_record(item)
        all_futures.append(record)
    main_count = sum(1 for f in all_futures if f.get("is_main", False))
    print(f"[INFO] 解析完成：总合约 {len(all_futures)}，主力合约 {main_count}")
    print("[INFO] 正在获取宏观指标...")
    macro_indicators = fetch_macro_indicators()
    print(f"[INFO] 获取到 {len(macro_indicators)} 个宏观指标")
    # Add key commodity futures to macro indicators (from domestic futures data)
    macro_indicators = add_key_commodities_to_macro(all_futures, macro_indicators)
    sector_data, uncategorized = classify_by_sector(all_futures)
    ratios = calc_ratios(all_futures, macro_indicators)
    alerts = validate_data(all_futures)
    stars = find_star_products(all_futures)
    result = {
        "fetch_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "domestic_futures": all_futures,
        "macro_indicators": macro_indicators,
        "sector_data": sector_data,
        "uncategorized": uncategorized,
        "ratios": ratios,
        "alerts": alerts,
        "star_products": stars,
    }
    output_dir = os.environ.get("OUTPUT_DIR", os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(output_dir, f"quotes_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 数据已保存至: {output_file}")
    print(f"[INFO] 比值计算结果: {ratios}")
    print(f"[INFO] 异常波动品种数: {len(alerts)}")
    if uncategorized:
        print(f"[WARN] 未分类主力合约: {len(uncategorized)}")
        for item in uncategorized[:5]:
            print(f"  - {item.get('name', '')} ({item.get('symbol', '')})")
if __name__ == "__main__":
    main()