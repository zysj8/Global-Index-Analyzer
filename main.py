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
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "000300", "source": "ak_em"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "000905", "source": "ak_em"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "ticker": "^HSI", "source": "yf"},
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "ticker": "3033.HK", "source": "yf"}
}

def get_valuation_signal(percentile):
    """仓位管理算法"""
    p = float(percentile)
    if p < 0.2: return 100.0
    elif p < 0.5: return 70.0
    elif p < 0.8: return 40.0
    else: return 15.0 # 高位减仓至 15%

def main():
    results = []
    print(f"[{datetime.now()}] 启动分析任务...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            pct = 0.0
            method = "价格分位"
            
            if info['source'] == "ak_em":
                # A股：使用更稳健的东方财富历史数据接口
                df = ak.stock_zh_index_daily_em(symbol=f"sh{info['symbol']}")
                curr = float(df['close'].iloc[-1])
                hist = df['close'].tail(1250).astype(float)
                pct = (curr - hist.min()) / (hist.max() - hist.min())
            else:
                # 国际 & 港股：统一使用 yfinance 提高海外运行稳定性
                data = yf.Ticker(info['ticker'])
                hist = data.history(period="3y")['Close'].dropna()
                curr = float(hist.iloc[-1])
                pct = (curr - hist.min()) / (hist.max() - hist.min())

            signal = get_valuation_signal(pct)
            
            results.append({
                "index": info['name'],
                "method": method,
                "percentile": f"{round(float(pct) * 100, 2)}%",
                "target_weight": str(round(float(info['weight']) * 100, 1)), # 纯数字输出
                "suggested_pos": str(round(signal, 1)) # 纯数字输出
            })
        except Exception as e:
            print(f"数据处理失败 [{info['name']}]: {e}")
            results.append({
                "index": info['name'],
                "method": "获取失败",
                "percentile": "0%",
                "target_weight": str(round(float(info['weight']) * 100, 1)),
                "suggested_pos": "15.0"
            })

    output = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
