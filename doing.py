import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
from scipy import stats

window_size = 52 * 3

# Đường dẫn đến file Excel
file_path_macro = 'MAcro-2018-2023.xlsx'
file_path_index = 'Dữ liệu Lịch sử VN Index.xlsx'
file_path_vni = 'vni.xlsx'
file_path_DE = 'FiinProX_DE_Doanh_nghiep_20231020.xlsx'

# Đọc file Excel vào DataFrame
skip_rows = [i for i in range(8, 19)] 
system = pd.read_excel(file_path_index)
df_macro = pd.read_excel(file_path_macro, header=7,skiprows=skip_rows, nrows=60)
df_vni = pd.read_excel(file_path_vni)
df_DE = pd.read_excel(file_path_DE, header=7, nrows=416)

# Chuyển đổi cột 'Ngày' trong cả hai DataFrame về cùng định dạng datetime để thực hiện merge
system['Ngày'] = pd.to_datetime(system['Ngày'])
df_macro['Ngày'] = pd.to_datetime(df_macro['Ngày'])

# Merge dữ liệu từ cột "% Thay đổi" của DataFrame 'Dữ liệu Lịch sử VN Index.xlsx' dựa trên cột 'Ngày'
merged_data = pd.merge(df_macro, system, on='Ngày', how='left')
stateVariables_D = merged_data.sort_values('Ngày', ascending=False)
stateVariables_D = stateVariables_D.drop(columns='Lãi suất trái phiếu chính phủ 1 năm\nĐơn vị:')
stateVariables_D = stateVariables_D.drop(columns='Lãi suất trái phiếu chính phủ 10 năm\nĐơn vị: %')

# print(stateVariables_D)
# Lấy danh sách các mã từ DataFrame VNI
các_mã_trong_vni = df_vni.columns[1:].tolist()  # Bỏ cột 'date' và lấy các mã cổ phiếu

# Lọc các mã từ DataFrame DE sao cho chỉ hiển thị những mã có trong DataFrame VNI
df_DE_filtered = df_DE[df_DE['Mã'].isin(các_mã_trong_vni)]

df_vni['date'] = pd.to_datetime(df_vni['date'])

# Lọc dữ liệu từ ngày 1/1/2018 đến 31/12/2022
start_date = pd.to_datetime('2018-01-01')
end_date = pd.to_datetime('2022-12-31')

filtered_df_vni = df_vni[(df_vni['date'] >= start_date) & (df_vni['date'] <= end_date)]


# Melt the df_vni DataFrame to align values with 'Mã' and 'STT'
melted_vni = filtered_df_vni.melt(id_vars='date', var_name='Mã', value_name='Value')

# Pivot the melted DataFrame to have dates as columns
pivot_vni = melted_vni.pivot(index='Mã', columns='date', values='Value').reset_index()

# Merge the pivoted data into df_DE_filtered based on 'Mã'
stock_data = pd.merge(df_DE_filtered, pivot_vni, on='Mã', how='left')

# Display the merged DataFrame
print(stock_data)


#Out [28]
print(stateVariables_D.describe().iloc[[1,2,3,4,6,7], :])

#Out [30]
print(system.describe().iloc[[1,2,3,4,6,7], :])

start=0
end=1249
market_close= system[['Lần cuối']]
market_losses = (market_close.shift(1) - market_close) / market_close.shift(1)
market_losses = market_losses[(market_losses.index >= start) & (market_losses.index <= end)].dropna()
market_losses = market_losses.rename(columns={'Lần cuối': 'Market_Losses'})
market_losses['Market_Losses'] = market_losses['Market_Losses'] * 100
print(market_losses.describe().iloc[[1,2,3,4,6,7], :])

#Output [32]

data = {}
date_columns = stock_data.columns[64:].tolist()
for index, row in stock_data.iterrows():
    data[row['Mã']] = {
        'Value': row[date_columns].values.tolist(),
        'Date': date_columns,
        # 'Ngành': row['Ngành']  # Lấy thông tin về ngành từ cột 'Ngành'
    }


# Chuyển đổi dữ liệu thành DataFrame
stock_data = {key: pd.DataFrame(value) for key, value in data.items()}
for stock in stock_data:
    stock_data[stock]['Date'] = pd.to_datetime(stock_data[stock]['Date'])
    stock_data[stock] = stock_data[stock].set_index('Date')

# Tính toán tỷ lệ lỗ và lọc các cột có ít hơn 2 giá trị NaN
start = pd.to_datetime('2018-01-01')
end = pd.to_datetime('2022-12-31')

stocks_losses_W_pct = {}
for stock in stock_data.keys():
    stock_close = stock_data[stock]['Value']
    stock_losses = (stock_close.shift(1) - stock_close) / stock_close.shift(1)
    stock_losses = stock_losses[(stock_losses.index >= start) & (stock_losses.index <= end)].dropna()
    stocks_losses_W_pct[stock] = (100 * (1 - (1 - stock_losses).resample("W").prod()))

stocks_losses_W_pct = pd.DataFrame(stocks_losses_W_pct)
stocks_losses_W_pct = stocks_losses_W_pct.loc[:, (stocks_losses_W_pct.isna().sum(axis=0) < 2)]

print(stocks_losses_W_pct.describe())
#In [34]
def historical_var(stock_name, q, window_size = window_size, stocks_losses_series = stocks_losses_W_pct):
    return stocks_losses_series[stock_name].dropna().rolling(
        window = window_size, min_periods = int(0.8 * window_size)
    ).apply(lambda x: np.quantile(x, q)).dropna().rename(stock_name + "_VaR_" + str(q))

print(historical_var("AAA", 0.99))
#In [35]
def formula_var(stock_name, q, window_size = window_size, stocks_losses_series = stocks_losses_W_pct):
    rolling = stocks_losses_series[stock_name].dropna().rolling(window = window_size, min_periods = int(0.8 * window_size))
    mean_series = rolling.mean()
    std_series = rolling.std()
    return (mean_series + stats.norm.ppf(q) * std_series).dropna().rename(stock_name + "_VaR_" + str(q))
print(formula_var("AAA", 0.99))