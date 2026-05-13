import pandas as pd
import akshare as ak
import yfinance as yf
import json
from datetime import datetime

# 核心配置
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "ticker": "^GSPC", "source": "yf", "weight": 0.32},
    "NDX": {"name": "纳斯达克100", "ticker": "^NDX", "source": "yf", "weight": 0.32},
    "CSI300": {"name": "沪深300", "symbol": "000300", "source": "ak", "weight": 0.05},
    "CSI500": {"name": "中证500", "symbol": "000905", "source": "ak", "weight": 0.05}
}

def main():
    results = []
    print(f"[{datetime.now()}] 启动数据抓取...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            if info['source'] == "ak":
                # 使用东财历史接口抓取A股
                df = ak.index_zh_a_hist(symbol=info['symbol'], period="daily")
                series = df['收盘'].astype(float)
            else:
                # 抓取国际指数
                series = yf.Ticker(info['ticker']).history(period="3y")['Close'].dropna()

            curr = series.iloc[-1]
            # 计算分位点
            p_val = (curr - series.min()) / (series.max() - series.min())
            
            # 显式定义所有键名，必须与 HTML 对应
            item = {
                "display_name": info['name'],
                "method": "历史收盘价百分位",
                "percentile_str": f"{round(p_val * 100, 2)}%",
                "target_weight": info['weight'] * 100,
                "suggested_pos": round(info['weight'] * (1 - p_val) * 100, 2)
            }
            results.append(item)
            print(f"成功获取: {info['name']}")
        except Exception as e:
            print(f"!!! 抓取失败 {info['name']}: {e}")

    # 保存 JSON
    output = {"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
