import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 指数配置
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300", "source": "ak_pe"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905", "source": "ak_pe"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "symbol": "hkHSI", "source": "ak_hk"}, # 改用 akshare 接口
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "symbol": "hkHSTECH", "source": "ak_hk"} # 解决抓取不到问题
}

def get_valuation_signal(percentile):
    if percentile < 0.2: return 1.0
    elif percentile < 0.5: return 0.7
    elif percentile < 0.8: return 0.4
    else: return 0.15

def main():
    results = []
    for key, info in INDEX_CONFIG.items():
        try:
            print(f"分析中: {info['name']}...")
            method = "价格百分位"
            
            if info['source'] == "ak_pe":
                # A股 PE 百分位
                df = ak.stock_a_indicator_lg(symbol=info['symbol'])
                val = float(df['pe'].iloc[-1])
                pct = float((df['pe'].tail(2520) < val).mean())
                method = "PE百分位"
            elif info['source'] == "ak_hk":
                # 港股估值 (通过指数历史行情估算)
                df = ak.stock_hk_index_daily_sina(symbol=info['symbol'])
                current_val = float(df['close'].iloc[-1])
                hist = df['close'].tail(1250) # 约5年数据
                pct = (current_val - hist.min()) / (hist.max() - hist.min())
                method = "价格百分位"
            else:
                # 国际指数价格百分位
                data = yf.Ticker(info['ticker'])
                hist = data.history(period="3y")['Close']
                current_val = float(hist.iloc[-1])
                pct = (current_val - hist.min()) / (hist.max() - hist.min())

            signal_ratio = get_valuation_signal(pct)
            
            # 确保 weight 为 float 避免 NaN
            target_w = float(info['weight'])
            
            results.append({
                "index": info['name'],
                "method": method,
                "percentile": f"{round(float(pct) * 100, 2)}%",
                "target_weight": f"{round(target_w * 100, 0)}%",
                "suggested_pos_ratio": f"{round(signal_ratio * 100, 1)}%"
            })
        except Exception as e:
            print(f"跳过 {info['name']}: {e}")

    output = {"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
