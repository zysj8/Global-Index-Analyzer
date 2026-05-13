import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 指数配置：代码、名称、目标权重
# 注：A股使用akshare，国际指数使用yfinance
CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "ticker": "^HSI"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905"}
}

def get_valuation_signal(percentile):
    """
    估值梯度加仓法逻辑实现：
    - 百分位 < 20%: 极低估，满额定投 (100% 目标权重)
    - 20% - 50%: 合理，标准定投 (70% 目标权重)
    - 50% - 80%: 微高，减少定投 (40% 目标权重)
    - > 80%: 高估，停止加仓或维持低位 (15% 目标权重)
    """
    if percentile < 0.2: return 1.0
    elif percentile < 0.5: return 0.7
    elif percentile < 0.8: return 0.4
    else: return 0.15

def run_task():
    report = {"update_time": str(datetime.now()), "results": []}
    
    for key, info in CONFIG.items():
        try:
            # 简化版百分位计算（基于近3年价格区间作为估值参考）
            # 提示：更精确的PE百分位需调用ak.stock_a_indicator_lg等特定接口
            ticker = yf.Ticker(info['ticker'])
            hist = ticker.history(period="3y")
            current = hist['Close'].iloc[-1]
            p_min, p_max = hist['Close'].min(), hist['Close'].max()
            percentile = (current - p_min) / (p_max - p_min)
            
            signal = get_valuation_signal(percentile)
            
            report["results"].append({
                "index": info['name'],
                "percentile": f"{round(percentile*100, 2)}%",
                "target_weight": info['weight'],
                "suggested_pos_ratio": f"{round(signal * 100, 2)}% of target"
            })
        except Exception as e:
            print(f"Error processing {key}: {e}")

    # 保存为JSON
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_task()
