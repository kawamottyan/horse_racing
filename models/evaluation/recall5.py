import numpy as np

def precision_at_5(predictions, actual):
    top_5_predictions = predictions.argsort()[-5:][::-1]
    top_3_actual = actual.argsort()[-3:][::-1]
    common_elements = np.intersect1d(top_5_predictions, top_3_actual)
    precision = len(common_elements) / 5
    return precision

def recall_at_5(predictions, actual):
    top_5_predictions = predictions.argsort()[-5:][::-1]
    top_3_actual = actual.argsort()[-3:][::-1]
    common_elements = np.intersect1d(top_5_predictions, top_3_actual)
    recall = len(common_elements) / 3
    return recall

def recall5(test_datas, years):
    """
    recall@5とprecision@5を計算する
    
    Parameters:
    - test_datas: リスト。それぞれの年のテストデータのデータフレームを含む
    - years: 計算する年数のリスト
    """
    for test_data, year in zip(test_datas, years):
        group_ids = test_data['group'].unique()
        precisions = []
        recalls = []
        
        for group_id in group_ids:
            group_test_data = test_data[test_data['group'] == group_id]
            p = precision_at_5(group_test_data['predicted_rank'].values, group_test_data['kakutei_chakujun'].values)
            r = recall_at_5(group_test_data['predicted_rank'].values, group_test_data['kakutei_chakujun'].values)
            precisions.append(p)
            recalls.append(r)
        
        print(f"{year} Precision@5: {np.mean(precisions):.3%}")
        print(f"{year} Recall@5: {np.mean(recalls):.3%}")
