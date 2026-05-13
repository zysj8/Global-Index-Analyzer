import pandas as pd
import akshare as ak
import yfinance as yf
import json
import os
from datetime import datetime

# 指数配置：A股统一使用 EM 历史接口代码
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "ticker": "^NDX", "source": "yf"},
    "CSI300": {"name": "沪深300", "symbol": "000300", "source": "ak_hist"},
    "CSI500": {"name": "中证500", "symbol": "000905", "source": "ak_hist"}
}

def main():
    results = []
    print(f"[{datetime.now()}] 启动修复部署：增强型数据抓取...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            if info['source'] == "ak_hist":
                # 使用 ak.index_zh_a_hist 接口，这是目前最稳定的东财数据源
                # period="daily" 获取日频数据
                df = ak.index_zh_a_hist(symbol=info['symbol'], period="daily")
                
                if df.empty:
                    raise ValueError(f"{info['name']} 接口返回数据为空")
                
                # 东财接口返回的列名为：日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
                # 我们需要将其标准化
                df['date'] = pd.to_datetime(df['日期'])
                df.set_index('date', inplace=True)
                series = df['收盘'].astype(float)
            else:
                # 国际指数逻辑
                series = yf.Ticker(info['ticker']).history(period="2y")['Close'].dropna()

            if len(series) < 2:
                continue

            curr = series.iloc[-1]
            prev = series.iloc[-2]
            
            item = {
                "name": info['name'],
                "price": round(curr, 2),
                "change": f"{'+' if curr > prev else ''}{round((curr/prev - 1)*100, 2)}%",
                "percentile": f"{round(((curr - series.min()) / (series.max() - series.min())) * 100, 2)}%"
            }
            results.append(item)
            print(f"成功更新: {info['name']}")

        except Exception as e:
            print(f"!!! 抓取失败 {info['name']}: {str(e)}")

    # 导出 JSON
    output = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("---------------------------------------")
    print(f"部署完成。成功获取 {len(results)}/4 条数据。")

if __name__ == "__main__":
    main()
