import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 核心资产配置
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300", "source": "ak_sina"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905", "source": "ak_sina"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "ticker": "^HSI", "source": "yf"}
}

def calc_pct_str(current, previous):
    if previous == 0 or pd.isna(previous): return "---"
    res = (current / previous) - 1
    return f"{'+' if res > 0 else ''}{round(res * 100, 2)}%"

def get_performance_metrics(series):
    curr = series.iloc[-1]
    daily = calc_pct_str(curr, series.iloc[-2])
    m20 = calc_pct_str(curr, series.iloc[-21]) if len(series) >= 21 else "---"
    
    this_year = datetime.now().year
    ytd_data = series[series.index >= pd.Timestamp(this_year, 1, 1)]
    ytd = calc_pct_str(curr, ytd_data.iloc[0]) if not ytd_data.empty else "---"
    
    y1 = calc_pct_str(curr, series.iloc[-251]) if len(series) >= 251 else "---"
    y3 = calc_pct_str(curr, series.iloc[-751]) if len(series) >= 751 else "---"
    
    return {"price": round(curr, 2), "daily": daily, "m20": m20, "ytd": ytd, "y1": y1, "y3": y3}

def main():
    results = []
    for key, info in INDEX_CONFIG.items():
        try:
            if info['source'] == "ak_sina":
                df = ak.stock_zh_index_daily_sina(symbol=info['symbol'])
                df.index = pd.to_datetime(df['date'])
                series = df['close'].sort_index().astype(float) # 强制排序
            else:
                data = yf.Ticker(info['ticker'])
                series = data.history(period="4y")['Close'].dropna()

            m = get_performance_metrics(series)
            hist_5y = series.tail(1250)
            p_val = (series.iloc[-1] - hist_5y.min()) / (hist_5y.max() - hist_5y.min())

            results.append({
                "name": info['name'], # 统一键名
                "price": m['price'],
                "daily": m['daily'],
                "m20": m['m20'],
                "ytd": m['ytd'],
                "y1": m['y1'],
                "y3": m['y3'],
                "percentile": f"{round(p_val * 100, 2)}%",
                "target_weight": str(round(float(info['weight']) * 100, 1)) # 使用更明确的键名
            })
        except Exception as e:
            print(f"Error {info['name']}: {e}")

    output = {"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
