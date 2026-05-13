import pandas as pd
import akshare as ak
import yfinance as yf
import json
from datetime import datetime

# 1. 你的全球指数组合配置 (共10个)
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
    print(f"[{datetime.now()}] 正在同步 10 个全球指数数据...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            # 2. 差异化抓取逻辑
            if info['source'] == "ak":
                # A股使用东财稳定接口
                df = ak.index_zh_a_hist(symbol=info['symbol'], period="daily")
                series = df['收盘'].astype(float)
            else:
                # 国际指数使用 yfinance (取近3年数据计算分位)
                series = yf.Ticker(info['ticker']).history(period="3y")['Close'].dropna()

            if series.empty: continue

            curr = series.iloc[-1]
            # 3. 计算估值百分位
            min_val = series.min()
            max_val = series.max()
            p_val = (curr - min_val) / (max_val - min_val)
            
            # 4. 构建输出字典
            results.append({
                "display_name": info['name'],
                "method": "3年收盘价百分位",
                "percentile_str": f"{round(p_val * 100, 2)}%",
                "target_weight": f"{int(info['weight'] * 100)}%",
                "suggested_pos": f"{round(info['weight'] * (1 - p_val) * 100, 2)}%", # 逆向补仓逻辑
                "status": "Normal"
            })
            print(f"成功更新: {info['name']}")
            
        except Exception as e:
            print(f"!!! 跳过 {info['name']}, 错误原因: {e}")

    # 5. 持久化存储
    output = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print(f"\n部署成功：已完成 {len(results)}/10 个指数的更新。")

if __name__ == "__main__":
    main()
