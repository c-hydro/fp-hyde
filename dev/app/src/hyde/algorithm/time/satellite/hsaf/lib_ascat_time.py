# -------------------------------------------------------------------------------------
# Library
import pandas as pd
from datetime import timedelta
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to select analysis period
def select_period(time_end, time_start=None, time_freq='D', time_period=30):

    if time_start is None:
        time_steps = pd.date_range(end=time_end, periods=time_period, freq=time_freq)
    else:
        time_steps = pd.date_range(start=time_start, end=time_end, freq=time_freq)

    time_from = time_steps[0].round(time_freq)
    time_to = time_steps[-1]

    time_from = time_from.to_pydatetime()
    time_to = time_to.to_pydatetime()

    time_now = time_to

    return time_now, time_from, time_to
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to match df based on window time
def df_selecting_period(df, time, window=64):

    win_hours = float(window)
    time_to = time + timedelta(hours=int(win_hours))
    time_from = time - timedelta(hours=int(win_hours))

    df_period = df.loc[time_from:time_to]

    return df_period
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to match df based on given time
def df_selecting_step(df, time):

    time_idx = df.index.get_loc(time, method='nearest')

    time_ref = pd.Timestamp(time)
    time_select = df.index[time_idx]

    time_diff = time_ref - time_select

    time_df = df.iloc[time_idx]

    return time_df, time_diff, time_idx
# -------------------------------------------------------------------------------------
