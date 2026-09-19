import uuid

import joblib
import pandas as pd
from prefect import flow, task


@task(retries=3, retry_delay_seconds=3)
def load_data():
    """Function for loading the data"""
    df = pd.read_csv("../data/test_data_1.csv")
    return df


@task
def load_model():
    """Function for loading the model"""
    model = joblib.load("../model-building/best_model.joblib")
    return model


@task
def generate_ids(df):
    """Function for generating unique ids for each row in the results"""
    df_result_ids = []
    n = df.shape[0]

    for i in range(n):
        df_result_ids.append(str(uuid.uuid4()))

    return df_result_ids


@task
def predict_and_store_results(model, df, df_result_ids):
    """Function for prediction"""
    y_pred = model.predict(df)
    df_result = pd.DataFrame()
    df_result["pred_id"] = df_result_ids
    for col in df.columns[1:]:
        df_result[col] = df[col]

    df_result["prediction"] = y_pred
    test_csv = pd.read_csv("../data/test_data_1_duration.csv")
    df_result["actual_duration"] = test_csv["duration"]
    df_result.to_csv("./outputs/result.csv", index=False)


@flow
def run():
    df = load_data()
    model = load_model()
    df_result_ids = generate_ids(df)
    predict_and_store_results(model, df, df_result_ids)


if __name__ == "__main__":
    run()
