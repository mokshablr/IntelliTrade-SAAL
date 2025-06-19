import pandas as pd
import pandas_ta as ta

def compute_sma(df, window):
    return df['close'].rolling(window).mean()

def compute_ema(df, window):
    return df['close'].ewm(span=window, adjust=False).mean()

def compute_rsi(df, window):
    return ta.rsi(df['close'], length=window)

def compute_macd(df):
    return ta.macd(df['close'])  # returns DataFrame

def compute_bbands(df, window):
    return ta.bbands(df['close'], length=window)


# Supported indicator/function map
INDICATOR_FUNCTIONS = {
    "sma": compute_sma,
    "ema": compute_ema,
    "rsi": compute_rsi,
    "macd": compute_macd,
    "bbands": compute_bbands,
}

def apply_indicators(df: pd.DataFrame, indicators: dict) -> pd.DataFrame:
    for name, conf in indicators.items():
        kind = conf["type"].lower()
        window = conf.get("window", 14)

        if kind not in INDICATOR_FUNCTIONS:
            raise ValueError(f"Unsupported indicator type: {kind}")

        func = INDICATOR_FUNCTIONS[kind]

        if kind == "macd":
            # macd does not take window param, returns DataFrame
            result = func(df)
            for col in result.columns:
                df[f"{name}_{col.lower()}"] = result[col]

        else:
            # all others take window param
            result = func(df, window)

            if isinstance(result, pd.DataFrame):
                for col in result.columns:
                    df[f"{name}_{col.lower()}"] = result[col]
            else:
                df[name] = result

    return df


# Testing
from fetch_alpha_vantage import fetch_stock_data  # your ingestion module
if __name__ == "__main__":
    df = fetch_stock_data("AAPL")

    indicators = {
        "SMA_10": {"type": "sma", "window": 10},
        "RSI_14": {"type": "rsi", "window": 14},
        "MACD": {"type": "macd"},
        "BOLL": {"type": "bbands", "window": 20}
    }

    df = apply_indicators(df, indicators)
    df_clean = df.dropna(subset=[
        "SMA_10", "RSI_14",
        "MACD_macd_12_26_9",
        "BOLL_bbl_20_2.0"
    ])
    print(df_clean.head())
    print(df.loc[30:40, [
        "date",
        "MACD_macd_12_26_9",
        "MACD_macdh_12_26_9",
        "MACD_macds_12_26_9"
    ]])


