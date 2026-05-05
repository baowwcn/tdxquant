import sqlite3
import numpy as np
import pandas as pd
from scipy import stats

db_path = "C:/new_tdx64/PYPlugins/user/a_share_full.db"
conn = sqlite3.connect(db_path)

stock = "000001.SZ"
df = pd.read_sql(
    f"SELECT date, open, close FROM stock_data WHERE code='{stock}' AND date >= '2018-01-01' ORDER BY date",
    conn,
    parse_dates=["date"],
)
conn.close()

print(f"数据量: {len(df)}")

df.columns = ["Date", "Open", "Close"]
df = df.set_index("Date").sort_index()

df["MA60"] = df["Close"].rolling(60).mean()
df["MA120"] = df["Close"].rolling(120).mean()


def calculate_slope(series, window=120):
    def slope_on_window(y):
        if len(y) < 2 or np.any(np.isnan(y)):
            return np.nan
        x = np.arange(len(y))
        slope, _, _, _, _ = stats.linregress(x, y)
        return slope

    return series.rolling(window).apply(slope_on_window, raw=True)


df["K60"] = calculate_slope(df["MA60"], window=120).round(2)
df["K120"] = calculate_slope(df["MA120"], window=120).round(2)

cond1 = (df["K60"] - df["K120"]).abs() <= 0.02
cond2 = df["K60"] > df["K120"]
cond3 = df["K60"] * df["K120"] >= 0
df["Signal"] = (cond1 & cond2 & cond3).astype(int)

print(f"满足条件的日期数: {df['Signal'].sum()}")
print("\n满足条件的日期:")
print(df[df["Signal"] == 1][["Close", "K60", "K120"]].head(20))
