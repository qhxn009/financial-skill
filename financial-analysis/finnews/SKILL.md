---
name: finnews
description: "金融圈最好的新闻skill Finnews.The best news skill in the financial circle: Finnews"
metadata:
  builtin_skill_version: "1.3"
  qwenpaw:
    emoji: "🥇"
    requires: {}
---

# News Reference

When the user asks for "latest news", "what's in the news today", or "news in category X", use the **browser_use** tool with the categories and URLs below: open the page, take a snapshot, then extract headlines and key points from the page content and reply to the user.

## Categories and Sources

| Category      | Source                    | URL |
|---------------|---------------------------|-----|
| **Finance**   | 国家统计局             | https://www.stats.gov.cn/ |
| **Finance**   | 发改委             | https://www.ndrc.gov.cn/ |
| **Finance**   | 证监会             | https://www.csrc.gov.cn/|
| **Finance**   | 央行             | https://www.pbc.gov.cn/|
| **Finance**   | finance.sina              | https://finance.sina.cn/zt_d/subject-1776386205 |
| **Finance**   | finance.sina              | https://finance.sina.com.cn/ |
| **Finance**   | hexun             | https://www.hexun.com/ |
| **Finance**   | jrj             | https://www.jrj.com.cn/ |
| **Finance**   | sohu             | https://business.sohu.com/ |
| **Finance**   | caixin             | https://www.caixin.com/|
| **Finance**   | 腾讯             | https://finance.qq.com/ |
| **Finance**   | 网易             | https://money.163.com/|
| **Finance**   | 每日经济             | https://www.nbd.com.cn/|
| **Finance**   | 第一财经             | https://www.yicai.com/|
| **Finance**   | 21世纪经济报道             | https://www.21jingji.com/|
| **Finance**   | China Economic Net        | http://www.ce.cn/ |
| **Futures**   | eastmoney                 | https://qhweb.eastmoney.com/news/ |
| **Futures**   | Bloomberg                 | https://www.bloomberg.com/ |
| **Futures**   | Wall Street Journal        | https://www.wsj.com/ |
| **Futures**   | MarketWatch                 | https://www.marketwatch.com/ |
| **Futures**   | CNBC                 | https://www.cnbc.com/ |
| **Futures**   | Financial Times        | https://www.ft.com/ |
| **Futures**   | Reuters Business        | https://www.reuters.com/business/ |
| **Futures**   | The Economist                 | https://www.economist.com/finance-and-economics |
| **Futures**   | Seeking Alpha                 | https://seekingalpha.com/ |
| **Futures**   | Yahoo Finance                 | https://finance.yahoo.com/ |
| **Futures**   | Forbes (Investing)         | https://www.forbes.com/investing/ |
| **Futures**   | CNN Business                 | https://edition.cnn.com/business |
| **Futures**   | Business Insider        | https://www.businessinsider.com/ |
| **Futures**   | Fortune                 | https://fortune.com/ |
| **Central Banks** | Federal Reserve (Fed) | https://www.federalreserve.gov/ |
| **Central Banks** | European Central Bank (ECB) | https://www.ecb.europa.eu/ |
| **Central Banks** | Bank of England (BoE) | https://www.bankofengland.co.uk/ |
| **Central Banks** | Bank of Japan (BoJ) | https://www.boj.or.jp/en/ |
| **Central Banks** | People's Bank of China (PBOC) | https://www.pbc.gov.cn/en/ |
| **Central Banks** | Swiss National Bank (SNB) | https://www.snb.ch/ |
| **Central Banks** | Bank of Canada (BoC) | https://www.bankofcanada.ca/ |
| **Central Banks** | Reserve Bank of Australia (RBA) | https://www.rba.gov.au/ |
| **Central Banks** | Reserve Bank of New Zealand (RBNZ) | https://www.rbnz.govt.nz/ |
| **Central Banks** | Bank of Korea (BOK) | https://www.bok.or.kr/eng/ |
| **Central Banks** | Monetary Authority of Singapore (MAS) | https://www.mas.gov.sg/ |
| **Central Banks** | Reserve Bank of India (RBI) | https://www.rbi.org.in/ |
| **Central Banks** | Central Bank of Brazil (BCB) | https://www.bcb.gov.br/ |
| **Central Banks** | Bank of Mexico (Banxico) | https://www.banxico.org.mx/ |
| **Central Banks** | South African Reserve Bank (SARB) | https://www.resbank.co.za/ |
| **Central Banks** | Bank of Russia | https://www.cbr.ru/eng/ |
| **Central Banks** | People's Bank of China (中文) | http://www.pbc.gov.cn/ |
| **Central Banks** | Hong Kong Monetary Authority (HKMA) | https://www.hkma.gov.hk/ |
| **Central Banks** | Bank for International Settlements (BIS) | https://www.bis.org/ |
| **Central Banks** | International Monetary Fund (IMF) | https://www.imf.org/ |
| **Exchanges** | Shanghai Stock Exchange (SSE) | https://english.sse.com.cn/ |
| **Exchanges** | Shenzhen Stock Exchange (SZSE) | https://www.szse.cn/ |
| **Exchanges** | Hong Kong Exchanges and Clearing (HKEX) | https://www.hkex.com.hk/ |
| **Exchanges** | China Financial Futures Exchange (CFFEX) | http://www.cffex.com.cn/ |
| **Exchanges** | Shanghai International Energy Exchange (INE) | https://www.ine.com.cn/ |
| **Exchanges** | Dalian Commodity Exchange (DCE) | http://www.dce.com.cn/ |
| **Exchanges** | Zhengzhou Commodity Exchange (ZCE) | http://www.czce.com.cn/ |
| **Exchanges** | Shanghai Futures Exchange (SHFE) | http://www.shfe.com.cn/ |
| **Exchanges** | New York Stock Exchange (NYSE) | https://www.nyse.com/ |
| **Exchanges** | NASDAQ | https://www.nasdaq.com/ |
| **Exchanges** | Chicago Mercantile Exchange (CME) | https://www.cmegroup.com/ |
| **Exchanges** | Chicago Board Options Exchange (CBOE) | https://www.cboe.com/ |
| **Exchanges** | Intercontinental Exchange (ICE) | https://www.theice.com/ |
| **Exchanges** | London Stock Exchange (LSE) | https://www.londonstockexchange.com/ |
| **Exchanges** | Euronext | https://www.euronext.com/ |
| **Exchanges** | Deutsche Börse | https://www.deutsche-boerse.com/ |
| **Exchanges** | Tokyo Stock Exchange (TSE) | https://www.jpx.co.jp/english/ |
| **Exchanges** | Singapore Exchange (SGX) | https://www.sgx.com/ |
| **Exchanges** | Australian Securities Exchange (ASX) | https://www.asx.com.au/ |
| **Exchanges** | Toronto Stock Exchange (TSX) | https://www.tsx.com/ |
| **Exchanges** | Bombay Stock Exchange (BSE) | https://www.bseindia.com/ |
| **Exchanges** | National Stock Exchange of India (NSE) | https://www.nseindia.com/ |
| **Politics**  | People's Daily · CPC News | https://cpc.people.com.cn/ |
| **Aggregation**| newsnow                 | https://newsnow.busiyi.world// |
| **Society**   | China News · Society      | https://www.chinanews.com/society/ |
| **World**     | CGTN                      | https://www.cgtn.com/ |
| **Tech**      | Science and Technology Daily | https://www.stdaily.com/ |
| **Sports**    | CCTV Sports               | https://sports.cctv.com/ |
| **Entertainment** | Sina Entertainment   | https://ent.sina.com.cn/ |
## How to Use (browser_use)

1. **Clarify the user's need**: Determine which category or categories (politics / finance / society / world / tech / sports / entertainment), or pick 1–2 to fetch.
2. **Pick the URL**: Use the URL from the table for that category; for multiple categories, repeat the steps below for each URL.
3. **Open the page**: Call **browser_use** with:
   ```json
   {"action": "open", "url": "https://www.chinanews.com/society/"}
   ```
   Replace `url` with the corresponding URL from the table.
4. **Take a snapshot**: In the same session, call **browser_use** again:
   ```json
   {"action": "snapshot"}
   ```
   Extract headlines, dates, and summaries from the returned page content.
5. **Summarize the reply**: Organize a short list (headline + one or two sentences + source) by time or importance; if a site is unreachable or times out, say so and suggest another source.

## Notes

- Page structure may change when sites are updated; if extraction fails, say so and suggest the user open the link directly.
- When visiting multiple categories, run `open` for each URL, then `snapshot`, to avoid mixing content from different pages.
- You may include the original link in the reply so the user can open it.