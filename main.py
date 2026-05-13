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
    """通用涨跌幅格式化工具"""
    if previous == 0 or pd.isna(previous): return "---"
    res = (current / previous) - 1
    return f"{'+' if res > 0 else ''}{round(res * 100, 2)}%"

def get_performance_metrics(series):
    """
    根据定义计算多维涨跌幅
    series: 价格序列 (Pandas Series)
    """
    curr = series.iloc[-1]
    
    # 1. 上一交易日 (T vs T-1)
    daily = calc_pct_str(curr, series.iloc[-2])
    
    # 2. 本月涨跌幅 (定义为最近 20 个交易日)
    m20 = calc_pct_str(curr, series.iloc[-21]) if len(series) >= 21 else "---"
    
    # 3. 年初至今 (YTD: 当年1月1日至今)
    this_year = datetime.now().year
    ytd_data = series[series.index >= pd.Timestamp(this_year, 1, 1)]
    ytd = calc_pct_str(curr, ytd_data.iloc[0]) if not ytd_data.empty else "---"
    
    # 4. 1年 (约250交易日) & 3年 (约750交易日)
    y1 = calc_pct_str(curr, series.iloc[-251]) if len(series) >= 251 else "---"
    y3 = calc_pct_str(curr, series.iloc[-751]) if len(series) >= 751 else "---"
    
    return {
        "price": round(curr, 2),
        "daily": daily,
        "m20": m20,
        "ytd": ytd,
        "y1": y1,
        "y3": y3
    }

def main():
    results = []
    print(f"[{datetime.now()}] 启动多维数据分析...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            if info['source'] == "ak_sina":
                # A股数据处理
                df = ak.stock_zh_index_daily_sina(symbol=info['symbol'])
                df.index = pd.to_datetime(df['date'])
                series = df['close'].astype(float)
            else:
                # 国际/港股数据处理
                data = yf.Ticker(info['ticker'])
                series = data.history(period="4y")['Close'].dropna()

            # 计算多维指标
            m = get_performance_metrics(series)
            
            # 计算价格分位 (基于近5年/1250交易日)
            hist_5y = series.tail(1250)
            p_val = (series.iloc[-1] - hist_5y.min()) / (hist_5y.max() - hist_5y.min())

            results.append({
                "index": info['name'],
                "price": m['price'],
                "daily": m['daily'],
                "m20": m['m20'],
                "ytd": m['ytd'],
                "y1": m['y1'],
                "y3": m['y3'],
                "percentile": f"{round(p_val * 100, 2)}%",
                "target": str(round(float(info['weight']) * 100, 1))
            })
        except Exception as e:
            print(f"!!! 无法获取 {info['name']}: {e}")

    # 输出为 JSON 供前端调用
    output = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("任务圆满完成！")

if __name__ == "__main__":
    main()
