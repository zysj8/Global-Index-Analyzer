import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 指数配置：针对 GitHub 环境优化了数据源
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300", "source": "ak_a"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905", "source": "ak_a"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "ticker": "^HSI", "source": "yf_hk"},
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "ticker": "3033.HK", "source": "yf_hk"}
}

def get_valuation_signal(percentile):
    """仓位管理逻辑：根据估值水平调整建议比例"""
    p = float(percentile)
    if p < 0.2: return 100.0
    elif p < 0.5: return 70.0
    elif p < 0.8: return 40.0
    else: return 15.0 # 对应 2026 年 5 月的减仓目标

def main():
    results = []
    print("开始获取全球指数数据...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            pct = 0.0
            # 修复 A 股抓取：使用每日行情计算价格分位
            if info['source'] == "ak_a":
                df = ak.stock_zh_index_daily(symbol=info['symbol'])
                curr = float(df['close'].iloc[-1])
                hist = df['close'].tail(1250).astype(float) # 约 5 年数据
                pct = (curr - hist.min()) / (hist.max() - hist.min())
            # 修复港股抓取：使用海外环境更稳定的 yfinance
            else:
                ticker = yf.Ticker(info['ticker'])
                hist = ticker.history(period="3y")['Close'].dropna()
                curr = float(hist.iloc[-1])
                pct = (curr - hist.min()) / (hist.max() - hist.min())

            signal = get_valuation_signal(pct)
            results.append({
                "index": info['name'],
                "method": "价格分位",
                "percentile": f"{round(float(pct) * 100, 2)}%",
                "target_weight": f"{round(float(info['weight']) * 100, 1)}", # 纯数字，不加%
                "suggested_pos": f"{round(signal, 1)}" # 纯数字，不加%
            })
        except Exception as e:
            print(f"无法获取 {info['name']}: {e}")
            results.append({
                "index": info['name'],
                "method": "获取失败",
                "percentile": "0%",
                "target_weight": f"{round(float(info['weight']) * 100, 1)}",
                "suggested_pos": "15.0"
            })

    # 导出 JSON
    output = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
