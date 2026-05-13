import pandas as pd
import yfinance as yf
import akshare as ak
import json
import os
from datetime import datetime

# ==========================================
# 1. 配置模块：定义指数、权重及获取方式
# ==========================================
INDEX_CONFIG = {
    # 国际指数 (使用 yfinance)
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "ticker": "^HSI", "source": "yf"},
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "ticker": "HSTECH.HK", "source": "yf"},
    
    # 国内指数 (使用 akshare 抓取 PE)
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300", "source": "ak"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905", "source": "ak"}
}

# ==========================================
# 2. 核心算法模块
# ==========================================
def get_valuation_signal(percentile):
    """
    估值梯度加仓法：
    - < 20%: 极低估 -> 100% 目标权重
    - 20%-50%: 偏低 -> 70% 目标权重
    - 50%-80%: 偏高 -> 40% 目标权重
    - > 80%: 高估 -> 15% 目标权重 (风险防范)
    """
    if percentile < 0.2: return 1.0
    elif percentile < 0.5: return 0.7
    elif percentile < 0.8: return 0.4
    else: return 0.15

def fetch_ak_valuation(symbol):
    """从 akshare 获取 A 股 PE 分位数"""
    try:
        df = ak.stock_a_indicator_lg(symbol=symbol)
        current_pe = df['pe'].iloc[-1]
        # 计算 10 年分位数 (约 2520 个交易日)
        history_pe = df['pe'].tail(2520)
        percentile = (history_pe < current_pe).mean()
        return round(current_pe, 2), percentile
    except Exception as e:
        print(f"Error fetching AK data for {symbol}: {e}")
        return None, None

def fetch_yf_valuation(ticker):
    """从 yfinance 获取国际指数价格分位数"""
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="3y")
        current_price = hist['Close'].iloc[-1]
        p_min = hist['Close'].min()
        p_max = hist['Close'].max()
        percentile = (current_price - p_min) / (p_max - p_min)
        return round(current_price, 2), percentile
    except Exception as e:
        print(f"Error fetching YF data for {ticker}: {e}")
        return None, None

# ==========================================
# 3. 执行模块
# ==========================================
def main():
    results = []
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for key, info in INDEX_CONFIG.items():
        print(f"正在处理: {info['name']}...")
        
        if info['source'] == "ak":
            val, pct = fetch_ak_valuation(info['symbol'])
        else:
            val, pct = fetch_yf_valuation(info['ticker'])
            
        if pct is not None:
            signal_ratio = get_valuation_signal(pct)
            suggested_weight = info['weight'] * signal_ratio
            
            results.append({
                "index": info['name'],
                "current_val": val,
                "percentile": f"{round(pct * 100, 2)}%",
                "target_weight": f"{round(info['weight'] * 100, 2)}%",
                "suggested_pos_ratio": f"{round(signal_ratio * 100, 2)}%",
                "final_pos": f"{round(suggested_weight * 100, 2)}%"
            })

    output = {
        "update_time": update_time,
        "results": results
    }

    # 保存结果
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    print(f"任务完成，数据已更新至 valuation_report.json")

if __name__ == "__main__":
    main()
