import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 完整配置 10 个指数
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300", "source": "ak"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905", "source": "ak"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "ticker": "^HSI", "source": "yf"},
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "ticker": "HSTECH.HK", "source": "yf"}
}

def get_valuation_signal(percentile):
    """根据估值百分位计算梯度仓位"""
    if percentile < 0.2: return 1.0     # 低估：全额
    elif percentile < 0.5: return 0.7   # 合理：7成
    elif percentile < 0.8: return 0.4   # 偏高：4成
    else: return 0.15                   # 高估：1.5成 (风险管理)

def main():
    results = []
    # 记录当前北京时间或执行时间
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for key, info in INDEX_CONFIG.items():
        try:
            print(f"正在分析: {info['name']}...")
            if info['source'] == "ak":
                # 获取 A 股 PE 估值 (乐咕乐股数据源)
                df = ak.stock_a_indicator_lg(symbol=info['symbol'])
                current_pe = df['pe'].iloc[-1]
                # 计算近10年分位
                pct = (df['pe'].tail(2520) < current_pe).mean()
            else:
                # 获取国际指数行情 (Yahoo Finance)
                data = yf.Ticker(info['ticker'])
                hist = data.history(period="3y") # 使用3年价格区间
                current_val = hist['Close'].iloc[-1]
                p_min, p_max = hist['Close'].min(), hist['Close'].max()
                pct = (current_val - p_min) / (p_max - p_min)
            
            signal_ratio = get_valuation_signal(pct)
            
            results.append({
                "index": info['name'],
                "percentile": f"{round(pct * 100, 2)}%",
                "target_weight": f"{round(info['weight'] * 100, 0)}%",
                "suggested_pos_ratio": f"{round(signal_ratio * 100, 1)}% of target"
            })
        except Exception as e:
            # 单个指数报错不中断程序，继续下一个
            print(f"无法获取 {info['name']} 数据: {e}")

    # 导出结果
    output = {"update_time": update_time, "results": results}
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
