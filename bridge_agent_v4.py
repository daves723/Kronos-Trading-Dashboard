"""
bridge_agent_v4.py -- 6-Agent multi-dimension analysis
Tencent free K-line data source
"""
import sys, json, urllib.request, numpy as np
from datetime import datetime, timedelta

INDUSTRY_MAP = {
    "中信证券":"证券","华泰证券":"证券","东方财富":"证券","国泰君安":"证券","第一创业":"证券",
    "海通证券":"证券","广发证券":"证券","申万宏源":"证券","中国银河":"证券","招商证券":"证券",
    "国信证券":"证券","光大证券":"证券","兴业证券":"证券","方正证券":"证券","长江证券":"证券",
    "东吴证券":"证券","浙商证券":"证券","天风证券":"证券","国金证券":"证券",
    "工商银行":"银行","建设银行":"银行","农业银行":"银行","中国银行":"银行","交通银行":"银行",
    "邮储银行":"银行","招商银行":"银行","浦发银行":"银行",
    "中国平安":"保险","中国人寿":"保险","中国太保":"保险",
    "同花顺":"金融科技","大智慧":"金融科技","指南针":"金融科技",
    "贵州茅台":"白酒","五粮液":"白酒",
    "宁德时代":"新能源汽车","比亚迪":"新能源汽车",
    "隆基绿能":"光伏","中芯国际":"半导体","寒武纪":"半导体",
    "药明康德":"医药","恒瑞医药":"医药",
    "科大讯飞":"AI","中际旭创":"AI","新易盛":"AI",
    "中国神华":"煤炭","紫金矿业":"有色","中国船舶":"军工",
    "长江电力":"电力","中国石油":"石油",
}

def get_kline(code, days=120):
    parts = code.replace(".SZ","").replace(".SH","").replace(".BJ","").split(".")
    num = parts[0]
    if code.endswith(".BJ"):
        mkt = "bj"
    elif code.endswith(".SZ"):
        mkt = "sz"
    else:
        mkt = "sh"
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={mkt}{num},day,,,{days},qfq"
    with urllib.request.urlopen(url, timeout=15) as resp:
        raw = resp.read()
        try: data = json.loads(raw.decode("gbk"))
        except: data = json.loads(raw.decode("utf-8"))
    key = f"{mkt}{num}"
    if key not in data.get("data",{}):
        raise ValueError(f"No data for {code}")
    rows = data["data"][key]["qfqday"]
    name = data["data"][key].get("qt",{}).get(key,["",""])[1] or code
    closes = np.array([float(r[2]) for r in rows])
    opens = np.array([float(r[1]) for r in rows])
    highs = np.array([float(r[3]) for r in rows])
    lows = np.array([float(r[4]) for r in rows])
    vols = np.array([float(r[5]) for r in rows])
    dates = [r[0] for r in rows]
    return name, closes, opens, highs, lows, vols, dates

def analyze(code):
    code = code.strip()
    if not code: print(json.dumps({"error":"no code"}, ensure_ascii=False)); return
    if "." not in code:
        if code.startswith("6") or code.startswith("5"):
            code = f"{code}.SH"
        elif code.startswith("8") or code.startswith("4"):
            code = f"{code}.BJ"
        else:
            code = f"{code}.SZ"

    try:
        name, closes, opens, highs, lows, vols, dates = get_kline(code)
    except Exception as e:
        print(json.dumps({"error":f"no data: {e}"}, ensure_ascii=False))
        return

    n, current, prev = len(closes), closes[-1], closes[-2]
    chg = (current/prev-1)*100
    industry = INDUSTRY_MAP.get(name, "")
    agents = []

    # Shared calculations
    ma5 = np.mean(closes[-5:])
    ma10 = np.mean(closes[-10:])
    ma20 = np.mean(closes[-20:])
    ma60 = np.mean(closes[-45:]) if n>=45 else ma20
    delta = np.diff(closes[-14:])
    gain = delta[delta>0].sum()
    loss_val = -delta[delta<0].sum()
    rsi = 100 - 100/(1+gain/loss_val) if loss_val>0 else 100
    avg_v20 = np.mean(vols[-21:-1])
    v_ratio20 = vols[-1]/avg_v20 if avg_v20>0 else 1
    days_up_5 = sum(1 for i in range(-5,0) if closes[i] > closes[i-1])
    days_up_10 = sum(1 for i in range(-10,0) if closes[i] > closes[i-1])

    # Agent 1: High-level Technical
    ta1 = []
    fvg_found = False
    for i in range(n-3, max(n-40,0), -1):
        if i-2>=0 and i+1<n:
            if closes[i-2] <= lows[i-1] and closes[i] > highs[i-1] and lows[i] > highs[i-1]:
                ta1.append(f"FVG上涨缺口 {dates[i]} 突破{highs[i-1]:.2f}")
                fvg_found = True; break
            if closes[i-2] >= highs[i-1] and closes[i] < lows[i-1] and highs[i] < lows[i-1]:
                ta1.append(f"FVG下跌缺口 {dates[i]} 跌破{lows[i-1]:.2f}")
                fvg_found = True; break
    if not fvg_found: ta1.append("近40日无显著FVG缺口")

    ob_found = False
    for i in range(n-2, max(n-20,0), -1):
        body = abs(closes[i]-opens[i])
        if i>=1 and body > abs(closes[i-1]-opens[i-1])*1.8:
            d = "bullish" if closes[i]>opens[i] else "bearish"
            ta1.append(f"订单块OB({d}) {dates[i]} [{min(opens[i],closes[i]):.2f}-{max(opens[i],closes[i]):.2f}]")
            ob_found = True; break
    if not ob_found: ta1.append("近20日无明确OB")

    h20, l20 = np.max(highs[-20:]), np.min(lows[-20:])
    if closes[-1] > h20: ta1.append(f"上破20日高{h20:.2f} 流动性掠夺")
    elif closes[-1] < l20: ta1.append(f"下破20日低{l20:.2f} 止损掠夺")
    else: ta1.append(f"距20日高{(closes[-1]/h20-1)*100:+.1f}% 距低{(closes[-1]/l20-1)*100:+.1f}%")

    if n>=20:
        vp = {}
        for c,v in zip(closes[-20:], vols[-20:]): vp[round(c,1)] = vp.get(round(c,1),0)+v
        poc = max(vp, key=vp.get)
        poc_dist = (current/poc-1)*100
        ta1.append(f"POC={poc:.2f} 偏离{poc_dist:+.1f}%")

    if ma5 > ma10 > ma20 > ma60: ta1.append("多头排列 MA5>MA10>MA20>MA60")
    elif ma5 < ma10 < ma20 < ma60: ta1.append("空头排列 MA5<MA10<MA20<MA60")
    else: ta1.append(f"均线交织 MA5={ma5:.1f} MA20={ma20:.1f}")

    ta1_sig = "bullish" if sum(1 for s in ta1 if "FVG上涨" in s or "上破" in s or "多头" in s)>=2 else "bearish" if sum(1 for s in ta1 if "FVG下跌" in s or "下破" in s or "空头" in s)>=2 else "neutral"
    agents.append({"name":"高阶技术(SMC+ICT+VP)","signal":ta1_sig,"confidence":min(85,50+len([s for s in ta1 if "FVG" in s or "破" in s or "排列" in s])*10),"reasons":ta1})

    # Agent 2: Basic Technical
    ta2 = [
        f"MA5={ma5:.1f} MA10={ma10:.1f} MA20={ma20:.1f} MA60={ma60:.1f}",
        f"RSI(14)={rsi:.1f} {'严重超卖' if rsi<20 else '偏弱' if rsi<35 else '严重超买' if rsi>75 else '偏强' if rsi>65 else '中性'} {'反弹概率大' if rsi<25 else ''}",
        f"MACD.DIF={(np.mean(closes[-12:])-np.mean(closes[-26:]))/current*100:.3f}",
        f"量比20={v_ratio20:.1f} {'放量' if v_ratio20>1.5 else '缩量' if v_ratio20<0.6 else '正常'}",
    ]
    std20 = np.std(closes[-20:])
    b_pos = (current-(ma20-2*std20))/(4*std20)*100 if std20>0 else 50
    ta2.append(f"Boll位置{b_pos:.0f}%")
    h30, l30 = np.max(highs[-30:]), np.min(lows[-30:])
    ta2.append(f"阻力{h30:.2f} 支撑{l30:.2f}")
    ta2_sig = "bullish" if rsi<30 and b_pos<20 else "bearish" if rsi>70 and b_pos>80 else "neutral"
    agents.append({"name":"基础技术(MA+RSI+MACD+Boll)","signal":ta2_sig,"confidence":70,"reasons":ta2})

    # Agent 3: Fund flow
    ampl = (highs[-1]-lows[-1])/closes[-2]*100
    fund = [f"量比20={v_ratio20:.1f} 振幅{ampl:.1f}%"]
    vt = np.mean([vols[i]/np.mean(vols[i-5:i]) for i in range(max(0,n-5),n)])
    if vt>1.3: fund.append("持续放量 资金流入")
    elif vt<0.7: fund.append("持续缩量 关注度降")
    else: fund.append("量能平稳")
    fund_sig = "bullish" if v_ratio20>1.5 and chg>0 else "bearish" if v_ratio20>1.5 and chg<0 else "neutral"
    agents.append({"name":"资金面(量价+换手)","signal":fund_sig,"confidence":55,"reasons":fund})

    # Agent 4: Sentiment
    streak, sd = 0, ""
    for i in range(n-1, max(n-8,0), -1):
        if closes[i] > closes[i-1]:
            if sd=="down": break
            sd, streak = "up", streak+1
        elif closes[i] < closes[i-1]:
            if sd=="up": break
            sd, streak = "down", streak+1
        else: break
    cp = (current-lows[-1])/(highs[-1]-lows[-1])*100 if highs[-1]!=lows[-1] else 50
    max60 = np.max(highs[-60:]) if n>=60 else np.max(highs)
    dd = (current/max60-1)*100
    sent = [
        f"5日阳{days_up_5}/5 ({days_up_5*20}%) 10日阳{days_up_10}/10",
        f"连续{streak}{'阳' if sd=='up' else '阴'}",
        f"收盘位{cp:.0f}% 回撤{dd:.1f}%",
    ]
    sent_sig = "bullish" if days_up_5>=3 else "bearish" if days_up_5<=1 and sd=="down" else "neutral"
    agents.append({"name":"情绪面(涨跌+回撤)","signal":sent_sig,"confidence":50+abs(days_up_5-2.5)*15,"reasons":sent})

    # Agent 5: Fundamental
    hot = ["半导体","AI","新能源汽车","光伏","军工","证券","金融科技"]
    cold = ["房地产","钢铁","煤炭"]
    if any(s in industry for s in hot):
        funda = [f"行业:{industry} 高景气"]
        funda_sig = "bullish"
    elif any(s in industry for s in cold):
        funda = [f"行业:{industry} 景气偏低"]
        funda_sig = "bearish"
    else:
        funda = [f"行业:{industry or '未识别'}"]
        funda_sig = "neutral"
    funda.append(f"现价{current:.2f} 60均价{np.mean(closes[-60:]):.2f}")
    agents.append({"name":"基本面(行业+估值)","signal":funda_sig,"confidence":50,"reasons":funda})

    # Agent 6: Verdict
    bulls = sum(1 for a in agents if a["signal"]=="bullish")
    bears = sum(1 for a in agents if a["signal"]=="bearish")
    neutrals = 5 - bulls - bears
    vd = [f"多头:{bulls} 空头:{bears} 中性:{neutrals}"]

    if rsi < 25 and days_up_5 <= 1 and bulls + neutrals >= bears:
        verdict = "bullish"
        verdict_text = f"超卖反弹信号 RSI={rsi:.0f} 连阴{streak}日 反弹概率较大"
        vd.append("策略: 左侧布局 止损设在低点下方2-3%")
    elif rsi > 75 and days_up_5 >= 4:
        verdict = "bearish"
        verdict_text = f"超买风险 RSI={rsi:.0f} {days_up_5}/5阳"
        vd.append("策略: 减仓止盈")
    elif bulls >= 4:
        verdict = "bullish"
        verdict_text = f"强烈看多 ({bulls}/5共识)"
        vd.append("策略: 逢低介入")
    elif bulls == 3:
        verdict = "bullish"
        verdict_text = f"偏多 ({bulls}/5)"
    elif bears >= 4:
        verdict = "bearish"
        verdict_text = f"强烈看空 ({bears}/5)"
    elif bears == 3:
        verdict = "bearish"
        verdict_text = f"偏空 ({bears}/5)"
    else:
        verdict = "neutral"
        verdict_text = f"信号分化 (多{bulls}/空{bears}/中{neutrals})"
    vd.append(f"风险: 波动率{np.std(closes[-20:])/np.mean(closes[-20:])*100:.1f}% 回撤{dd:.1f}%")
    agents.append({"name":"综合裁判","signal":verdict,"confidence":max(25,bulls*18),"reasons":vd})

    output = {"code":code,"name":name,"industry":industry,"price":round(current,2),"chg_pct":round(chg,2),"agents":agents,"verdict":verdict,"verdict_text":verdict_text}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else ""
    analyze(code)
