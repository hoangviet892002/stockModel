import pandas as pd

# Example data for df_vni (replace this with your actual DataFrame)
data_vni = {
    'date': [
        '2013-01-02', '2013-01-03', '2013-01-04', '2013-01-07', '2013-01-08',
        '2013-01-09', '2013-01-10', '2013-01-11', '2013-01-14'
    ],
    'AAA': [14.5, 14.1, 14.3, 14.2, 14.2, 14.4, 14.8, 14.7, 14.5],
    'AAM': [17.3, 17.0, 17.2, 17.2, 17.3, 18.1, 18.3, 18.2, 18.0],
    'AAT': [12.6, 13.4, 13.4, 14.0, 14.0, 14.9, 13.9, 13.1, 13.1]
}

# Example data for df_DE_filtered (replace this with your actual DataFrame)
data_DE_filtered = {
    'STT': [1, 2, 3],
    'Mã': ['AAA', 'AAM', 'AAT']
    # Add other columns from df_DE_filtered
}

# Create DataFrame from provided data
df_vni = pd.DataFrame(data_vni)
df_DE_filtered = pd.DataFrame(data_DE_filtered)

# Melt the df_vni DataFrame to align values with 'Mã' and 'STT'
melted_vni = df_vni.melt(id_vars='date', var_name='Mã', value_name='Value')

# Pivot the melted DataFrame to have dates as columns
pivot_vni = melted_vni.pivot(index='Mã', columns='date', values='Value').reset_index()

# Merge the pivoted data into df_DE_filtered based on 'Mã'
merged_df = pd.merge(df_DE_filtered, pivot_vni, on='Mã', how='left')

# Display the merged DataFrame
print(merged_df)
date_columns = merged_df.columns[2:].tolist()

# Tạo một dictionary để lưu trữ dữ liệu với key là Mã cổ phiếu và value là dictionary chứa thông tin 'Value', 'Date', 'Ngành'
data = {}

for index, row in merged_df.iterrows():
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
start = pd.to_datetime('2023-11-01')
end = pd.to_datetime('2023-11-05')

stocks_losses_W_pct = {}
for stock in stock_data.keys():
    stock_close = stock_data[stock]['Value']
    stock_losses = (stock_close.shift(1) - stock_close) / stock_close.shift(1)
    stock_losses = stock_losses[(stock_losses.index >= start) & (stock_losses.index <= end)].dropna()
    stocks_losses_W_pct[stock] = (100 * (1 - (1 - stock_losses).resample("W").prod()))

stocks_losses_W_pct = pd.DataFrame(stocks_losses_W_pct)
stocks_losses_W_pct = stocks_losses_W_pct.loc[:, (stocks_losses_W_pct.isna().sum(axis=0) < 2)]

print(stocks_losses_W_pct.describe())