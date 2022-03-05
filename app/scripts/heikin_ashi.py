import pandas as pd
import pandas_ta as ta

def heikin_ashi(df):
    # heikin_ashi_df = pd.DataFrame(index=df.index.values, columns=['open', 'high', 'low', 'close'])
    # heikin_ashi_df = pd.DataFrame(index=df.index.values, columns=['open', 'high', 'low', 'close', 'volume', 'hl2'])
    heikin_ashi_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'hl2'])
    
    # heikin_ashi_df['datetime'] = df['datetime']
    
    heikin_ashi_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    
    for i in range(len(df)):
        if i == 0:
            heikin_ashi_df.iat[0, 0] = df['open'].iloc[0]
        else:
            heikin_ashi_df.iat[i, 0] = (heikin_ashi_df.iat[i-1, 0] + heikin_ashi_df.iat[i-1, 3]) / 2
        
    heikin_ashi_df['high'] = heikin_ashi_df.loc[:, ['open', 'close']].join(df['high']).max(axis=1)
    
    heikin_ashi_df['low'] = heikin_ashi_df.loc[:, ['open', 'close']].join(df['low']).min(axis=1)
    
    heikin_ashi_df['volume'] = df['volume']
    
    heikin_ashi_df['hl2'] = ta.hl2(heikin_ashi_df['high'], heikin_ashi_df['low'])
    
    column_order_names = ["high", "low", "open", "close", "volume", "hl2"]
    heikin_ashi_df = heikin_ashi_df.reindex(columns=column_order_names)
    
    return heikin_ashi_df
