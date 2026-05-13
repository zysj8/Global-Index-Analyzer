import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 核心配置：明确资产权重
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "000300", "source": "ak_a"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "000905", "source": "ak_a"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "ticker": "^HSI", "source": "yf_hk"},
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "ticker": "3033.HK", "source": "yf_hk"}
}

def get_valuation_signal(percentile):
    """仓位管理逻辑"""
    p = float(percentile)
    if p < 0.2: return 100.0
    elif p < 0.5: return 70.0
    elif p < 0.8: return 40.0
    else: return 15.0 # 对应 2026 年 5 月的减仓策略

def main():
    results = []
    for key, info in INDEX_CONFIG.items():
        try:
            method = "价格分位"
            pct = 0.0
            
            if info['source'] == "ak_a":
                # 尝试使用 A 股指数行情接口计算价格分位
                df = ak.stock_zh_index_daily(symbol=f"sh{info['symbol']}")
                curr = float(df['close'].iloc[-1])
                hist = df['close'].tail(1250).astype(float) # 近 5 年
                pct = (curr - hist.min()) / (hist.max() - hist.min())
            elif info['source'] == "yf_hk":
                # 港股在 GitHub (海外) 环境下使用 yf 更加稳定
                data = yf.Ticker(info['ticker'])
                hist = data.history(period="3y")['Close'].dropna()
                curr = float(hist.iloc[-1])
                pct = (curr - hist.min()) / (hist.max() - hist.min())
            else:
                data = yf.Ticker(info['ticker'])
                hist = data.history(period="3y")['Close'].dropna()
                curr = float(hist.iloc[-1])
                pct = (curr - hist.min()) / (hist.max() - hist.min())

            signal = get_valuation_signal(pct)
            results.append({
                "index": info['name'],
                "method": method,
                "percentile": f"{round(float(pct) * 100, 2)}%",
                "target_weight": f"{round(float(info['weight']) * 100, 1)}", # 移除后缀 %，由前端统一处理
                "suggested_pos": f"{round(signal, 1)}" # 移除后缀 %
            })
        except Exception as e:
            results.append({
                "index": info['name'],
                "method": "获取失败",
                "percentile": "0%",
                "target_weight": f"{round(float(info['weight']) * 100, 1)}",
                "suggested_pos": "15.0"
            })

    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump({"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
