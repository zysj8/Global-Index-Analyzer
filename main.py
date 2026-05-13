import pandas as pd
import akshare as ak
import yfinance as yf
import json
from datetime import datetime

# 1. 10个指数的完整精确配置
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "ticker": "^GSPC", "source": "yf", "weight": 0.32},
    "NDX": {"name": "纳斯达克100", "ticker": "^NDX", "source": "yf", "weight": 0.32},
    "N225": {"name": "日经225", "ticker": "^N225", "source": "yf", "weight": 0.06},
    "FTSE": {"name": "英国富时100", "ticker": "^FTSE", "source": "yf", "weight": 0.06},
    "FCHI": {"name": "法国CAC40", "ticker": "^FCHI", "source": "yf", "weight": 0.04},
    "DAX": {"name": "德国DAX", "ticker": "^GDAXI", "source": "yf", "weight": 0.04},
    "CSI300": {"name": "沪深300", "symbol": "000300", "source": "ak", "weight": 0.05},
    "CSI500": {"name": "中证500", "symbol": "000905", "source": "ak", "weight": 0.05},
    "HSI": {"name": "恒生指数", "ticker": "^HSI", "source": "yf", "weight": 0.03},
    "HSTECH": {"name": "恒生科技", "ticker": "3033.HK", "source": "yf", "weight": 0.03}
}

def main():
    results = []
    print(f"[{datetime.now()}] 启动修复版数据抓取...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            if info['source'] == "ak":
                df = ak.index_zh_a_hist(symbol=info['symbol'], period="daily")
                series = df['收盘'].astype(float)
            else:
                series = yf.Ticker(info['ticker']).history(period="3y")['Close'].dropna()

            if series.empty: continue

            curr = series.iloc[-1]
            min_val, max_val = series.min(), series.max()
            p_val = (curr - min_val) / (max_val - min_val)
            
            # --- 逻辑优化：建议仓位 ---
            # 新逻辑：即使在高位也建议保留部分仓位。公式：目标权重 * (1 - p_val * 0.8)
            # 这样当 p_val=100% 时，建议仓位仍有 20% 的目标配额，而不是接近 0
            suggested = info['weight'] * (1 - p_val * 0.8) * 100
            
            results.append({
                "display_name": info['name'],
                "method": "3年收盘价百分位",
                "percentile_val": round(p_val * 100, 2), # 仅输出数值，不带%
                "target_weight": info['weight'] * 100,     # 仅输出数值
                "suggested_pos": round(suggested, 2)       # 仅输出数值
            })
            print(f"完成: {info['name']}")
        except Exception as e:
            print(f"错误 {info['name']}: {e}")

    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump({"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
