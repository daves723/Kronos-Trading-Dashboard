"""
bridge_chart.py -- 4-segment Kronos prediction (10/20/60/120 day) + K-line data
"""
import sys, json, urllib.request, os, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")

def get_tencent_kline(code, days=600):
    parts = code.replace(".SZ","").replace(".SH","").replace(".BJ","").split(".")
    num = parts[0]
    mkt = "bj" if code.endswith(".BJ") else ("sz" if code.endswith(".SZ") else "sh")
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={mkt}{num},day,,,{days},qfq"
    with urllib.request.urlopen(url, timeout=15) as resp:
        raw = resp.read()
        try: data = json.loads(raw.decode("gbk"))
        except: data = json.loads(raw.decode("utf-8"))
    key = f"{mkt}{num}"
    rows = data["data"][key]["qfqday"]
    name = data["data"][key]["qt"][key][1] or code
    candles = []
    for r in rows:
        candles.append([r[0], round(float(r[1]),2), round(float(r[2]),2),
                       round(float(r[4]),2), round(float(r[3]),2), round(float(r[5]),0), 0])
    return candles, name

def kronos_predict_segments(df_all, pred_lens):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kronos_local"))
        from kronos.model.kronos import Kronos, KronosTokenizer, KronosPredictor
        
        weights = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kronos_weights")
        tok_dir = os.path.join(weights, "models--NeoQuasar--Kronos-Tokenizer-base", "snapshots")
        md_dir = os.path.join(weights, "models--NeoQuasar--Kronos-small", "snapshots")
        
        tok_path = md_path = None
        for d in os.listdir(tok_dir):
            p = os.path.join(tok_dir, d)
            if os.path.isdir(p) and os.path.exists(os.path.join(p,"model.safetensors")): tok_path = p; break
        for d in os.listdir(md_dir):
            p = os.path.join(md_dir, d)
            if os.path.isdir(p) and os.path.exists(os.path.join(p,"model.safetensors")): md_path = p; break
        if not tok_path or not md_path: return None
        
        tok = KronosTokenizer.from_pretrained(tok_path, map_location="cpu")
        model = Kronos.from_pretrained(md_path, map_location="cpu")
        pred = KronosPredictor(model, tok, device="cpu", max_context=512, use_amp=False)
        
        results = {}
        for pl in pred_lens:
            n_hist = min(200, len(df_all))
            hist = df_all.iloc[-n_hist:].copy()
            y_ts = pd.date_range(start=hist.index[-1] + pd.Timedelta(days=1), periods=pl, freq="B")
            result = pred.predict(hist, hist.index, y_ts, pred_len=pl, T=0.9, sample_count=2, verbose=False)
            predictions, pred_dates, upper, lower = [], [], [], []
            for idx, row in result.iterrows():
                predictions.append(round(float(row["close"]), 2))
                pred_dates.append(idx.strftime("%Y%m%d"))
                upper.append(round(float(row["high"]), 2))
                lower.append(round(float(row["low"]), 2))
            results[str(pl)] = {"predictions": predictions, "dates": pred_dates, "upper": upper, "lower": lower}
        return results
    except: return None

def trend_fallback(closes, pred_lens):
    from datetime import datetime, timedelta
    ma5 = np.mean(closes[-5:])
    ma20 = np.mean(closes[-20:])
    td = 1 if ma5 > ma20 else -1
    ts = abs(ma5/ma20-1)*100
    vol = np.std(closes[-20:])/np.mean(closes[-20:])*100
    lc = closes[-1]
    results = {}
    for pl in pred_lens:
        np.random.seed(42)
        preds, dates, up, lo = [], [], [], []
        dt = datetime.now()
        for i in range(1, pl+1):
            drift = td * ts / 100 * lc / 20
            noise = np.random.normal(0, vol/100*lc/2)
            preds.append(round(lc + drift*i + noise, 2))
            while True:
                dt += timedelta(days=1)
                if dt.weekday() < 5: break
            dates.append(dt.strftime("%Y%m%d"))
            band = vol/100*lc*np.sqrt(i+1)
            up.append(round(lc+drift*i+band, 2))
            lo.append(round(lc+drift*i-band, 2))
        results[str(pl)] = {"predictions":preds,"dates":dates,"upper":up,"lower":lo}
    return results

def get_chart(code):
    code = code.strip()
    if not code: print(json.dumps({"error":"no code"}, ensure_ascii=False)); return
    if "." not in code:
        if code.startswith("6") or code.startswith("5"): code = f"{code}.SH"
        elif code.startswith("8") or code.startswith("4"): code = f"{code}.BJ"
        else: code = f"{code}.SZ"
    try:
        candles, name = get_tencent_kline(code, days=600)
    except Exception as e:
        print(json.dumps({"error":f"data: {e}"}, ensure_ascii=False)); return
    if len(candles) < 80:
        print(json.dumps({"error":"need >= 80 candles"}, ensure_ascii=False)); return

    closes = [c[2] for c in candles]
    df = pd.DataFrame([[c[0],c[1],c[3],c[4],c[2],c[5]] for c in candles],
                      columns=["date","open","high","low","close","volume"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    pred_lens = [10, 20, 60, 120]
    segments = kronos_predict_segments(df, pred_lens)
    if segments is None:
        segments = trend_fallback(closes, pred_lens)
        model_name = "趋势外推(Kronos加载失败)"
    else:
        model_name = "Kronos-small"

    volatility = np.std(closes[-20:])/np.mean(closes[-20:])*100
    ma5 = np.mean(closes[-5:])
    ma20 = np.mean(closes[-20:])
    td = 1 if ma5 > ma20 else -1
    ts = abs(ma5/ma20-1)*100

    output = {
        "code":code,"name":name,"price":round(closes[-1],2),
        "candles":candles[-120:],"segments":segments,
        "trend":"up" if td>0 else "down",
        "trend_strength":round(ts,2),"volatility":round(volatility,2),
        "model":model_name
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else ""
    get_chart(code)
