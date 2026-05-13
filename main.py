import pandas as pd
import yfinance as yf
import akshare as ak
import json
import os
from datetime import datetime

# 1. 核心配置：定义 10 个指数及其目标权重
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300", "source": "ak_pe"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905", "source": "ak_pe"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "symbol": "hkHSI", "source": "ak_hk"},
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "symbol": "hkHSTECH", "source": "ak_hk"}
}

def get_valuation_signal(percentile):
    """仓位管理逻辑：根据估值梯度确定持仓比例"""
    p = float(percentile)
    if p < 0.2: return 100.0 # 满额
    elif p < 0.5: return 70.0 # 7成
    elif p < 0.8: return 40.0 # 4成
    else: return 15.0 # 高估，仅保留 15% (对应你的减仓策略)

def main():
    results = []
    print(f"[{datetime.now()}] 开始执行数据爬取任务...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            method = "价格百分位"
            pct = 0.0
            
            if info['source'] == "ak_pe":
                # A股 PE 估值抓取
                df = ak.stock_a_indicator_lg(symbol=info['symbol'])
                curr_pe = float(df['pe'].iloc[-1])
                hist_pe = df['pe'].tail(2520).astype(float)
                pct = (hist_pe < curr_pe).mean()
                method = "PE百分位"
            elif info['source'] == "ak_hk":
                # 港股数据抓取 (新浪财经接口)
                df = ak.stock_hk_index_daily_sina(symbol=info['symbol'])
                curr_price = float(df['close'].iloc[-1])
                hist_price = df['close'].tail(1250).astype(float)
                pct = (curr_price - hist_price.min()) / (hist_price.max() - hist_price.min())
            else:
                # 国际市场价格区间抓取
                data = yf.Ticker(info['ticker'])
                hist = data.history(period="3y")['Close'].dropna()
                curr_price = float(hist.iloc[-1])
                pct = (curr_price - hist.min()) / (hist.max() - hist.min())

            signal_val = get_valuation_signal(pct)
            
            results.append({
                "index": str(info['name']),
                "method": str(method),
                "percentile": f"{round(float(pct) * 100, 2)}%",
                "target_weight": f"{round(float(info['weight']) * 100, 1)}%",
                "suggested_pos": f"{round(signal_val, 1)}%" # 确保键名与前端完全一致
            })
        except Exception as e:
            print(f"数据抓取失败 [{info['name']}]: {e}")
            # 异常情况下返回兜底数据，确保表格不缺失行
            results.append({
                "index": str(info['name']),
                "method": "获取异常",
                "percentile": "---",
                "target_weight": f"{round(float(info['weight']) * 100, 1)}%",
                "suggested_pos": "15.0"
            })

    # 输出 JSON 文件
    report_data = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)
    print("分析报告已成功写入 valuation_report.json")

if __name__ == "__main__":
    main()
