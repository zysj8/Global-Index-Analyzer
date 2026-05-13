import pandas as pd
import akshare as ak
import yfinance as yf
import json
import os
from datetime import datetime

# 核心资产配置：A股使用东财接口，国际指数使用 yf
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "ticker": "^NDX", "source": "yf"},
    "CSI300": {"name": "沪深300", "symbol": "000300", "source": "ak_em"}, # 改为东财代码
    "CSI500": {"name": "中证500", "symbol": "000905", "source": "ak_em"}
}

def main():
    results = []
    print(f"[{datetime.now()}] 开始部署：数据抓取启动...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            if info['source'] == "ak_em":
                # 修复逻辑：使用更稳定的东方财富日频接口
                df = ak.stock_zh_index_daily_em(symbol=info['symbol'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                series = df['close'].astype(float)
            else:
                # 国际指数逻辑保持不变
                series = yf.Ticker(info['ticker']).history(period="2y")['Close'].dropna()

            curr = series.iloc[-1]
            prev = series.iloc[-2]
            
            # 构建最简 MVP 数据包，确保 index.html 100% 兼容
            item = {
                "name": info['name'],
                "price": round(curr, 2),
                "change": f"{'+' if curr > prev else ''}{round((curr/prev - 1)*100, 2)}%",
                "percentile": f"{round(((curr - series.min()) / (series.max() - series.min())) * 100, 2)}%"
            }
            results.append(item)
            print(f"成功获取: {info['name']}")

        except Exception as e:
            print(f"!!! 无法获取 {info['name']}, 错误详情: {e}")

    # 写入 JSON 文件
    output = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("valuation_report.json 已重置并成功更新。")

if __name__ == "__main__":
    main()
