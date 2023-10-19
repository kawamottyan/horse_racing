import numpy as np

def check_top3_in_top5_predictions(group):
    predicted_top5 = group.nsmallest(5, 'predicted_rank').index.tolist()
    actual_top3 = group.nsmallest(3, 'kakutei_chakujun').index.tolist()
    return all([horse in predicted_top5 for horse in actual_top3])

def calculate_group_profit(group):
    if check_top3_in_top5_predictions(group):
        payout_value = group['haraimodoshi_sanrenpuku_1b'].iloc[0]
        return payout_value - 1000
    else:
        return -1000

def profit(test_datas, years):
    """
    profitを計算する
    
    Parameters:
    - test_datas: リスト。それぞれの年のテストデータのデータフレームを含む
    - years: 計算する年数のリスト
    """
    mean_profits = []

    for test_data, year in zip(test_datas, years):
        profit_df = test_data.groupby('group').apply(calculate_group_profit).reset_index(name='profit')
        total_profit = profit_df['profit'].sum()
        average_net_profit = total_profit / len(profit_df)
        
        print(f"{year} Average Net Profit: {average_net_profit:.3f} yen")
        mean_profits.append(average_net_profit)
    
    print(f"Mean Average Net Profit: {np.mean(mean_profits):.3f} yen")