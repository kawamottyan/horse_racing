import numpy as np
from sklearn.metrics import mean_squared_error

def rmse(test_datas, years):
    """
    RMSEを計算する
    
    Parameters:
    - test_datas: リスト。それぞれの年のテストデータのデータフレームを含む
    - years: 計算する年数のリスト
    """
    rmse_values = []
    
    for test_data, year in zip(test_datas, years): # 各年のデータをループする
        rmse_value = np.sqrt(mean_squared_error(test_data['predicted_rank'], test_data['kakutei_chakujun']))
        rmse_values.append(rmse_value)
        print(f"RMSE for {year}: {rmse_value:.3f}")
    
    mean_rmse = np.mean(rmse_values)
    print(f"Mean RMSE: {mean_rmse:.3f}")