import pandas as pd
import numpy as np
import sqlite3
from itertools import product
import pandas_ta as ta
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# --- Performance Metrics ---

def sharpe_ratio(returns, risk_free=0.0):
    """Calculate annualized Sharpe ratio"""
    excess = returns - risk_free
    if excess.std() == 0:
        return 0
    return np.sqrt(252) * excess.mean() / excess.std()

def sortino_ratio(returns, risk_free=0.0):
    """Calculate Sortino ratio (downside deviation)"""
    excess = returns - risk_free
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0
    return np.sqrt(252) * excess.mean() / downside.std()

def max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    if len(equity_curve) == 0:
        return 0
    roll_max = equity_curve.cummax()
    drawdown = (equity_curve - roll_max) / roll_max
    return drawdown.min()

def calmar_ratio(returns, equity_curve):
    """Calculate Calmar ratio (annual return / max drawdown)"""
    annual_return = (1 + returns.mean()) ** 252 - 1
    mdd = abs(max_drawdown(equity_curve))
    if mdd == 0:
        return 0
    return annual_return / mdd

def win_rate(returns):
    """Calculate percentage of winning trades"""
    if len(returns) == 0:
        return 0
    return (returns > 0).sum() / len(returns)

def trade_count(signals):
    """Count number of trades (signal changes)"""
    return signals.diff().abs().sum()

def compute_equity_curve(df, signal, initial_capital):
    """
    Simulates portfolio value over time using daily returns and signal.
    Assumes full allocation (1 means all-in, 0 means all-out).
    """
    df = df.copy()
    df['return'] = df['close'].pct_change().fillna(0)
    df['position'] = signal

    # Daily portfolio returns = signal * daily asset return
    df['strategy_return'] = df['position'] * df['return']
    df['equity'] = (1 + df['strategy_return']).cumprod() * initial_capital

    return df['equity']


# --- Enhanced Strategy Implementations ---

def sma_crossover(df, short, long):
    """Simple Moving Average Crossover Strategy"""
    if short >= long or long >= len(df) * 0.8:  # Need at least 20% of data after indicator calculation
        return pd.Series(0, index=df.index)
    
    df = df.copy()
    df['sma_short'] = ta.sma(df['close'], length=short)
    df['sma_long'] = ta.sma(df['close'], length=long)
    
    # Check if we have valid data
    if df['sma_short'].isna().all() or df['sma_long'].isna().all():
        return pd.Series(0, index=df.index)
    
    # Fill NaN values with 0 for comparison, then create signal
    sma_short_filled = df['sma_short'].fillna(0)
    sma_long_filled = df['sma_long'].fillna(0)
    
    signal = pd.Series(0, index=df.index)
    for i in range(1, len(df)):
        if pd.notna(df['sma_short'].iloc[i]) and pd.notna(df['sma_long'].iloc[i]):
            if df['sma_short'].iloc[i] > df['sma_long'].iloc[i]:
                signal.iloc[i] = 1
            else:
                signal.iloc[i] = 0
        else:
            signal.iloc[i] = signal.iloc[i-1] if i > 0 else 0
    
    return signal.shift(1).fillna(0)

def ema_crossover(df, short, long):
    """Exponential Moving Average Crossover Strategy"""
    if short >= long or long >= len(df) * 0.8:  # Need at least 20% of data after indicator calculation
        return pd.Series(0, index=df.index)
    
    df = df.copy()
    df['ema_short'] = ta.ema(df['close'], length=short)
    df['ema_long'] = ta.ema(df['close'], length=long)
    
    # Check if we have valid data
    if df['ema_short'].isna().all() or df['ema_long'].isna().all():
        return pd.Series(0, index=df.index)
    
    signal = pd.Series(0, index=df.index)
    for i in range(1, len(df)):
        if pd.notna(df['ema_short'].iloc[i]) and pd.notna(df['ema_long'].iloc[i]):
            if df['ema_short'].iloc[i] > df['ema_long'].iloc[i]:
                signal.iloc[i] = 1
            else:
                signal.iloc[i] = 0
        else:
            signal.iloc[i] = signal.iloc[i-1] if i > 0 else 0
    
    return signal.shift(1).fillna(0)

def rsi_strategy(df, low, high, length=14):
    """RSI Mean Reversion Strategy with proper state management"""
    df = df.copy()
    df['rsi'] = ta.rsi(df['close'], length=length)
    
    # Proper RSI strategy: buy when oversold, sell when overbought, hold in between
    signal = pd.Series(0, index=df.index)
    position = 0
    
    for i in range(1, len(df)):
        if pd.notna(df['rsi'].iloc[i]):
            if df['rsi'].iloc[i] < low:
                position = 1  # Buy signal
            elif df['rsi'].iloc[i] > high:
                position = 0  # Sell signal
            # Otherwise maintain current position
        signal.iloc[i] = position
    
    return signal.shift(1).fillna(0)

def macd_strategy(df, fast=12, slow=26, signal_period=9):
    """MACD Strategy"""
    df = df.copy()
    macd_data = ta.macd(df['close'], fast=fast, slow=slow, signal=signal_period)
    if macd_data is None or macd_data.empty:
        return pd.Series(0, index=df.index)
    
    # Use MACD line crossing above/below signal line
    macd_line = macd_data.iloc[:, 0].reindex(df.index, fill_value=np.nan)  # MACD line
    signal_line = macd_data.iloc[:, 1].reindex(df.index, fill_value=np.nan)  # Signal line
    
    signal = pd.Series(0, index=df.index)
    
    for i in range(1, len(df)):
        if pd.notna(macd_line.iloc[i]) and pd.notna(signal_line.iloc[i]):
            if macd_line.iloc[i] > signal_line.iloc[i]:
                signal.iloc[i] = 1
            else:
                signal.iloc[i] = 0
        else:
            signal.iloc[i] = signal.iloc[i-1] if i > 0 else 0
    
    return signal.shift(1).fillna(0)

def bollinger_strategy(df, window, stddev):
    """Bollinger Bands Mean Reversion Strategy"""
    df = df.copy()
    bb = ta.bbands(df['close'], length=window, std=stddev)
    if bb is None or bb.empty:
        return pd.Series(0, index=df.index)
    
    # Get lower and upper bands and align with df index
    lower_band = bb.iloc[:, 0].reindex(df.index, fill_value=np.nan)  # Lower band
    upper_band = bb.iloc[:, 2].reindex(df.index, fill_value=np.nan)  # Upper band
    
    signal = pd.Series(0, index=df.index)
    position = 0
    
    for i in range(1, len(df)):
        if pd.notna(lower_band.iloc[i]) and pd.notna(upper_band.iloc[i]):
            if df['close'].iloc[i] <= lower_band.iloc[i]:
                position = 1  # Buy
            elif df['close'].iloc[i] >= upper_band.iloc[i]:
                position = 0  # Sell
        signal.iloc[i] = position
    
    return signal.shift(1).fillna(0)

def stochastic_strategy(df, k_period=14, d_period=3, oversold=20, overbought=80):
    """Stochastic Oscillator Strategy"""
    df = df.copy()
    stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)
    if stoch is None or stoch.empty:
        return pd.Series(0, index=df.index)
    
    # Get the %K column (first column) and align with df index
    k_line = stoch.iloc[:, 0].reindex(df.index, fill_value=np.nan)
    
    signal = pd.Series(0, index=df.index)
    position = 0
    
    for i in range(1, len(df)):
        if pd.notna(k_line.iloc[i]):
            if k_line.iloc[i] < oversold:
                position = 1
            elif k_line.iloc[i] > overbought:
                position = 0
        signal.iloc[i] = position
    
    return signal.shift(1).fillna(0)

def williams_r_strategy(df, period=14, oversold=-80, overbought=-20):
    """Williams %R Strategy"""
    df = df.copy()
    wr = ta.willr(df['high'], df['low'], df['close'], length=period)
    if wr is None or wr.empty:
        return pd.Series(0, index=df.index)
    
    # Align Williams %R with df index
    wr = wr.reindex(df.index, fill_value=np.nan)
    
    signal = pd.Series(0, index=df.index)
    position = 0
    
    for i in range(1, len(df)):
        if pd.notna(wr.iloc[i]):
            if wr.iloc[i] < oversold:
                position = 1
            elif wr.iloc[i] > overbought:
                position = 0
        signal.iloc[i] = position
    
    return signal.shift(1).fillna(0)

def momentum_strategy(df, period=10, threshold=0.02):
    """Price Momentum Strategy"""
    df = df.copy()
    df['momentum'] = df['close'].pct_change(periods=period)
    
    signal = pd.Series(0, index=df.index)
    position = 0
    
    for i in range(period, len(df)):
        if pd.notna(df['momentum'].iloc[i]):
            if df['momentum'].iloc[i] > threshold:
                position = 1
            elif df['momentum'].iloc[i] < -threshold:
                position = 0
        signal.iloc[i] = position
    
    return signal.shift(1).fillna(0)

# --- Enhanced Strategy Grid with adaptive parameters ---

def get_adaptive_strategy_grid(data_length):
    """Generate strategy grid adapted to available data length"""
    
    return {
        'SMA': {'func': sma_crossover, 'params': {
            'short': [3, 5, 7, 10, 13, 15, 20, 21], 
            'long': [30, 50, 55, 89, 100, 144, 150, 200]
        }},
        'EMA': {'func': ema_crossover, 'params': {
            'short': [5, 8, 9, 10, 12, 13, 15, 20, 21], 
            'long': [21, 26, 30, 34, 50, 55, 89, 100, 144, 200]
        }},
        'RSI': {'func': rsi_strategy, 'params': {
            'low': [10, 20, 25, 30, 40], 
            'high': [60, 70, 75, 80, 90], 
            'length': [5, 7, 10, 14, 21, 28]
        }},
        'MACD': {'func': macd_strategy, 'params': {
            'fast': [5, 8, 12], 
            'slow': [13, 21, 26, 34], 
            'signal_period': [3, 5, 9]
        }},
        'Bollinger': {'func': bollinger_strategy, 'params': {
            'window': [10, 14, 20, 21, 25], 
            'stddev': [1.5, 2, 2.5, 3]
        }},
        'Stochastic': {'func': stochastic_strategy, 'params': {
            'k_period': [5, 9, 14], 
            'd_period': [3, 5, 7], 
            'oversold': [15, 20, 25, 30], 
            'overbought': [70, 75, 80, 85]
        }},
        'Williams_R': {'func': williams_r_strategy, 'params': {
            'period': [7, 10, 14, 20, 21], 
            'oversold': [-90, -85, -80], 
            'overbought': [-20, -15, -10]
        }},
        'Momentum': {'func': momentum_strategy, 'params': {
            'period': [5, 10, 14, 21, 30], 
            'threshold': [-1, -0.5, 0, 0.5, 1]
        }},
    }

def sanitize(value):
    """Ensure value is JSON-serializable float"""
    if pd.isna(value) or value in [np.inf, -np.inf]:
        return 0.0
    return float(value)


# --- Enhanced Backtest Function ---

def backtest(df, signals, initial_capital=10000, transaction_cost=0.001):
    """
    Enhanced backtest with transaction costs and multiple metrics
    """
    if len(signals) == 0 or signals.sum() == 0:
        return {
            'pnl': 0, 'sharpe': 0, 'sortino': 0, 'calmar': 0,
            'max_drawdown': 0, 'win_rate': 0, 'trades': 0,
            'annual_return': 0, 'volatility': 0, 'equity_curve': pd.Series([initial_capital])
        }

    trades_list = []
    for i in range(1, len(signals)):
        if signals.iloc[i] > signals.iloc[i - 1]:
            trades_list.append({'timestamp': str(df.index[i]), 'action': 'buy', 'price': float(df['close'].iloc[i])})
        elif signals.iloc[i] < signals.iloc[i - 1]:
            trades_list.append({'timestamp': str(df.index[i]), 'action': 'sell', 'price': float(df['close'].iloc[i])})
    
    returns = df['close'].pct_change().fillna(0)
    
    # Apply transaction costs when position changes
    position_changes = signals.diff().abs()
    transaction_costs = position_changes * transaction_cost
    
    # Calculate strategy returns
    strategy_returns = signals * returns - transaction_costs
    
    # Calculate equity curve
    equity_curve = (1 + strategy_returns).cumprod() * initial_capital
    
    # Calculate metrics
    pnl = equity_curve.iloc[-1] - initial_capital
    sr = sharpe_ratio(strategy_returns)
    sortino = sortino_ratio(strategy_returns)
    calmar = calmar_ratio(strategy_returns, equity_curve)
    mdd = max_drawdown(equity_curve)
    
    # Trade-based metrics
    trades = trade_count(signals)
    trade_returns = strategy_returns[strategy_returns != 0]
    wr = win_rate(trade_returns)
    
    # Annual metrics
    annual_return = (1 + strategy_returns.mean()) ** 252 - 1
    volatility = strategy_returns.std() * np.sqrt(252)

    cleaned_equity_curve = equity_curve.replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(method='bfill')

    return {
    'pnl': sanitize(pnl),
    'sharpe': sanitize(sr),
    'sortino': sanitize(sortino),
    'calmar': sanitize(calmar),
    'max_drawdown': sanitize(mdd),
    'win_rate': sanitize(wr),
    'trades': int(trades),
    'annual_return': sanitize(annual_return),
    'volatility': sanitize(volatility),
    'equity_curve': [
        [str(date), sanitize(value)] for date, value in cleaned_equity_curve.items()
    ],
    'trades_list': trades_list
    }


# --- Enhanced Grid Search ---
def grid_search(df, initial_capital=10000, ranking_metric='sharpe'):
    all_results = defaultdict(list)
    strategy_grid = get_adaptive_strategy_grid(len(df))

    print(f"Adaptive parameter grid created for {len(df)} data points")

    for strat_name, details in strategy_grid.items():
        func = details['func']
        param_grid = details['params']
        print(f"Testing {strat_name} strategy...")

        if not param_grid or not any(param_grid.values()):
            continue

        keys, values = zip(*param_grid.items())
        total_combos = len(list(product(*values)))
        completed = 0

        for combo in product(*values):
            params = dict(zip(keys, combo))

            # Validate
            if strat_name in ['SMA', 'EMA'] and params['short'] >= params['long']:
                continue
            if strat_name == 'RSI' and params['low'] >= params['high']:
                continue
            if strat_name in ['Stochastic', 'Williams_R'] and params['oversold'] >= params['overbought']:
                continue

            try:
                signals = func(df.copy(), **params)
                stats = backtest(df, signals, initial_capital)
                if stats['trades'] > 0:
                    all_results[strat_name].append((params, stats))
            except Exception as e:
                print(f"[ERROR] {strat_name} {params} failed: {e}")

            completed += 1
            if completed % 20 == 0:
                print(f"  Completed {completed}/{total_combos} combinations")

    best_results = []
    for strat_name, result_list in all_results.items():
        if not result_list:
            continue
        if ranking_metric == 'max_drawdown':
            best = min(result_list, key=lambda x: -x[1][ranking_metric])
        else:
            best = max(result_list, key=lambda x: x[1][ranking_metric])
        best_results.append((strat_name, best[0], best[1]))

    if ranking_metric == 'max_drawdown':
        best_results.sort(key=lambda x: -x[2][ranking_metric])
    else:
        best_results.sort(key=lambda x: x[2][ranking_metric], reverse=True)

    return best_results, all_results



# --- Data Fetching ---

def fetch_data(asset_type, symbol, interval='daily', db_path='../db/market_data.db'):
    """Fetch market data from database"""
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            f"SELECT * FROM candles WHERE type='{asset_type}' AND symbol='{symbol}' AND interval='{interval}' ORDER BY timestamp",
            conn,
            parse_dates=['timestamp']
        )
        conn.close()
        
        if df.empty:
            raise ValueError(f"No data found for {symbol} with interval {interval}")
        
        df.set_index('timestamp', inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# --- Results Analysis ---

def analyze_results(results, top_n=10):
    """Analyze and display top performing strategies"""
    if not results:
        print("No results to analyze")
        return
    
    print(f"\n=== TOP {top_n} STRATEGIES ===")
    print("-" * 100)
    print(f"{'Rank':<4} {'Strategy':<12} {'Parameters':<30} {'PnL%':<8} {'Sharpe':<8} {'Sortino':<8} {'MaxDD%':<8} {'Trades':<8}")
    print("-" * 100)
    
    for i, (strat_name, params, stats) in enumerate(results[:top_n], 1):
        pnl_pct = (stats['pnl'] / 10000) * 100
        param_str = str(params)[:28] + '..' if len(str(params)) > 30 else str(params)
        
        print(f"{i:<4} {strat_name:<12} {param_str:<30} {pnl_pct:<8.2f} "
              f"{stats['sharpe']:<8.3f} {stats['sortino']:<8.3f} "
              f"{stats['max_drawdown']*100:<8.2f} {int(stats['trades']):<8}")

def autotest(initial_capital, ranking_metric, asset_type, symbol, interval, start_date, end_date):
    df = fetch_data(asset_type, symbol, interval, "app/db/market_data.db")
    if df is None or df.empty:
        return {"status": "error", "message": "Failed to fetch data or no data available."}

    df.index = pd.to_datetime(df.index)
    df = df.loc[(df.index.date >= start_date) & (df.index.date <= end_date)]

    if df.empty:
        return {"status": "error", "message": "No data in the selected date range."}

    # best_results, all_results = grid_search(df, initial_capital, ranking_metric)
    best_results, all_results = grid_search(df, initial_capital, ranking_metric)

    # Sort best_results based on ranking_metric
    if ranking_metric == "max_drawdown":
        best_results = sorted(best_results, key=lambda x: x[2][ranking_metric])  # minimize drawdown
    else:
        best_results = sorted(best_results, key=lambda x: x[2][ranking_metric], reverse=True)

    if not best_results:
        return {"status": "error", "message": "No valid results found during grid search."}

    top_results = []
    for strat, params, stats in best_results[:10]:
        top_results.append({
            "strategy": strat,
            "parameters": params,
            "stats": {
                "pnl": round(stats['pnl'], 2),
                "pnl_percent": round((stats['pnl'] / initial_capital) * 100, 2),
                "annual_return": round(stats['annual_return'], 4),
                "sharpe_ratio": round(stats['sharpe'], 4),
                "sortino_ratio": round(stats['sortino'], 4),
                "calmar_ratio": round(stats['calmar'], 4),
                "max_drawdown": round(stats['max_drawdown'], 4),
                "win_rate": round(stats['win_rate'], 4),
                "volatility": round(stats['volatility'], 4),
                "total_trades": int(stats['trades']),
                "equity_curve": stats['equity_curve'],
                "trades_list": stats['trades_list']
            },
        })

    full_param_results = {}
    for strat, results in all_results.items():
        full_param_results[strat] = []
        for param_set, stats in results:
            full_param_results[strat].append({
                "parameters": param_set,
                "stats": {
                    "pnl": round(stats['pnl'], 2),
                    "pnl_percent": round((stats['pnl'] / initial_capital) * 100, 2),
                    "annual_return": round(stats['annual_return'], 4),
                    "sharpe_ratio": round(stats['sharpe'], 4),
                    "sortino_ratio": round(stats['sortino'], 4),
                    "calmar_ratio": round(stats['calmar'], 4),
                    "max_drawdown": round(stats['max_drawdown'], 4),
                    "win_rate": round(stats['win_rate'], 4),
                    "volatility": round(stats['volatility'], 4),
                    "total_trades": int(stats['trades']),
                }
            })

    best_strategy = top_results[0]

    return {
        "status": "success",
        "data": {
            "summary": {
                "symbol": symbol,
                "interval": interval,
                "data_points": len(df),
                "from": str(df.index[0]),
                "to": str(df.index[-1]),
            },
            "top_strategies": top_results,
            "best_strategy": best_strategy,
            "all_results": full_param_results
        }
    }



# --- Main Execution ---

if __name__ == '__main__':
    # Configuration
    symbol = 'TSLA'
    interval = 'daily'
    initial_capital = 10000
    ranking_metric = 'pnl'  # Options: 'sharpe', 'sortino', 'calmar', 'pnl'
    
    print(f"Starting backtest for {symbol} ({interval})")
    print(f"Initial Capital: ${initial_capital:,}")
    print(f"Ranking Metric: {ranking_metric}")
    print("=" * 50)
    
    # Fetch data
    df = fetch_data(symbol, interval)
    if df is None:
        exit(1)
    
    print(f"Data loaded: {len(df)} candles from {df.index[0]} to {df.index[-1]}")
    
    # Check if we have sufficient data
    if len(df) < 50:
        print(f"WARNING: Only {len(df)} data points available. Results may be unreliable.")
        print("Consider using longer timeframes or more historical data.")
    
    # Run grid search
    results = grid_search(df, initial_capital, ranking_metric)
    
    if results:
        # Analyze results
        analyze_results(results, top_n=10)
        
        # Best strategy details
        best_strat, best_params, best_stats = results[0]
        print(f"\n=== BEST STRATEGY DETAILS ===")
        print(f"Strategy: {best_strat}")
        print(f"Parameters: {best_params}")
        print(f"PnL: ${best_stats['pnl']:.2f} ({(best_stats['pnl']/initial_capital)*100:.2f}%)")
        print(f"Annual Return: {best_stats['annual_return']:.2%}")
        print(f"Sharpe Ratio: {best_stats['sharpe']:.4f}")
        print(f"Sortino Ratio: {best_stats['sortino']:.4f}")
        print(f"Calmar Ratio: {best_stats['calmar']:.4f}")
        print(f"Max Drawdown: {best_stats['max_drawdown']:.2%}")
        print(f"Win Rate: {best_stats['win_rate']:.2%}")
        print(f"Volatility: {best_stats['volatility']:.2%}")
        print(f"Total Trades: {int(best_stats['trades'])}")
    else:
        print("No valid results found")
