import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 1. 核心资产配置
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "ticker": "^GSPC", "source": "yf", "w": 0.32},
    "NDX": {"name": "纳斯达克100", "ticker": "^NDX", "source": "yf", "w": 0.32},
    "N225": {"name": "日经225", "ticker": "^N225", "source": "yf", "w": 0.06},
    "CSI300": {"name": "沪深300", "symbol": "sh000300", "source": "ak_sina", "w": 0.05},
    "CSI500": {"name": "中证500", "symbol": "sh000905", "source": "ak_sina", "w": 0.05},
    "HSI": {"name": "恒生指数", "ticker": "^HSI", "source": "yf", "w": 0.03}
}

def calc_pct(curr, prev):
    if prev == 0 or pd.isna(prev): return "---"
    res = (curr / prev) - 1
    return f"{'+' if res > 0 else ''}{round(res * 100, 2)}%"

def main():
    results = []
    print(f"[{datetime.now()}] 启动数据分析流程...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            if info['source'] == "ak_sina":
                # A股逻辑
                df = ak.stock_zh_index_daily_sina(symbol=info['symbol'])
                df.index = pd.to_datetime(df['date'])
                series = df['close'].sort_index().astype(float)
            else:
                # 国际/港股逻辑
                series = yf.Ticker(info['ticker']).history(period="4y")['Close'].dropna()

            curr = series.iloc[-1]
            # 统一字段名：必须与 index.html 中的 item.xxx 一一对应
            item = {
                "name": info['name'],
                "price": round(curr, 2),
                "d1": calc_pct(curr, series.iloc[-2]),
                "m20": calc_pct(curr, series.iloc[-21]) if len(series) >= 21 else "---",
                "ytd": calc_pct(curr, series[series.index >= pd.Timestamp(datetime.now().year, 1, 1)].iloc[0]),
                "y1": calc_pct(curr, series.iloc[-251]) if len(series) >= 251 else "---",
                "y3": calc_pct(curr, series.iloc[-751]) if len(series) >= 751 else "---",
                "p_val": f"{round(((curr - series.tail(1250).min()) / (series.tail(1250).max() - series.tail(1250).min())) * 100, 2)}%",
                "weight": f"{round(info['w'] * 100, 1)}%"
            }
            results.append(item)
        except Exception as e:
            print(f"!!! {info['name']} 执行异常: {e}")

    # 保存文件
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump({"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}, f, ensure_ascii=False, indent=4)
    print("数据更新成功。")

if __name__ == "__main__":
    main()
