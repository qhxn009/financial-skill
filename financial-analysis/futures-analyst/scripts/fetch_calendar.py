#!/usr/bin/env python3
"""
财经日历数据获取脚本
from forex.eastmoney.com 和 sina.com 获取财经日历数据
tavily_search/tavily_extract 可直接抓取
"""
import json
import os
import re
import sys
import time
from datetime import datetime
try:
    from pyppeteer import launch
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False
def get_timestamp():
    """获取当前时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
def fetch_from_eastmoney():
    """从东方财富获取财经日历"""
    return {
        "source": "eastmoney",
        "url": "https://forex.eastmoney.com/fc.html",
        "note": "通过 tavily_extract 获取"
    }
def fetch_from_sina():
    """从新浪财经获取财经日历"""
    return {
        "source": "sina",
        "url": "http://rl.cj.sina.com.cn/",
        "note": "通过 browser_use 获取"
    }

def parse_eastmoney_data(raw_text):
    """解析东方财富数据"""
    events = []
    # 解析表格数据
    # 格式: | 序号 | 公布日 | 时间 | 国家/地区 | 事件 | ...
    lines = raw_text.split('\n')
    for line in lines:
        # 匹配时间格式如 "01:00", "15:00"
        time_match = re.search(r'(\d{1,2}:\d{2})', line)
        # 跳过表头和分隔符
        if '---' in line or '时间' in line:
            continue
        
        if time_match:
            time_str = time_match.group(1)
            # 提取国家和事件
            parts = line.split('|')
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) >= 5:
                country = parts[3] if len(parts) > 3 else ""
                event = parts[4] if len(parts) > 4 else line
                
                # 清理事件名称
                event = re.sub(r'\d{4}-\d{2}-\d{2}', '', event).strip()
                event = re.sub(r'_MAR|_Q1|_Q[1-4]', '', event).strip()
                
                if event and country:
                    events.append({
                        "time": time_str,
                        "event": f"{country} {event}",
                        "impact": "neutral"
                    })
    
    return events

def parse_sina_data(raw_text):
    """解析新浪财经数据"""
    events = []
    lines = raw_text.split('\n')
    
    current_time = ""
    for line in lines:
        line = line.strip()
        
        # 匹配时间格式
        time_match = re.match(r'(\d{1,2}:\d{2})', line)
        if time_match:
            current_time = time_match.group(1)
            continue
        
        # 匹配事件行（包含"美国"或国家名）
        if current_time and ('美国' in line or '中国' in line or '加拿大' in line):
            # 提取事件名称
            event = line
            # 清理数据
            event = re.sub(r'前值：[^\n]*', '', event)
            event = re.sub(r'预测值：[^\n]*', '', event)
            event = re.sub(r'公布值[^\n]*', '', event)
            event = event.strip()
            
            if event and len(event) > 3:
                events.append({
                    "time": current_time,
                    "event": event,
                    "impact": "neutral"
                })
    
    return events

def save_calendar(events, filename):
    """保存日历数据到 JSON 文件"""
    output_path = os.path.join(os.path.dirname(__file__), filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 财经日历已保存: {output_path}")
    return output_path

def main():
    """主函数 - 生成供 report_generator.py 使用的日历数据"""
    timestamp = get_timestamp()
    output_file = f"calendar_{timestamp}.json"
    
    print("[INFO] 财经日历数据获取脚本")
    print("[INFO] 数据源: 东方财富 forex.eastmoney.com + 新浪财经 rl.cj.sina.com.cn")
    print("[INFO] 用法: 在获取数据后，手动创建 JSON 文件或调用本脚本后手动填充数据")
    print(f"[INFO] 输出格式: {output_file}")

    sample_format = [
        {"time": "09:30", "event": "中国 工业企业利润总额", "impact": "neutral"},
        {"time": "15:00", "event": "美国 CPI数据", "impact": "neutral"}
    ]
    
    # 保存示例格式
    save_calendar(sample_format, output_file)
    
    return output_file

if __name__ == "__main__":
    main()