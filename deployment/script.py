import json
import os
import re
import uuid
from datetime import datetime

import joblib
import pandas as pd
from prefect import flow, task

DATA_DIR = "./data"
OUTPUT_DIR = "./outputs"
STATE_FILE = os.path.join(OUTPUT_DIR, "batch_state.json")


@task
def get_next_batch_file():
    """Find the next unprocessed batch file in order:
    test_data_1.csv -> test_data_2.csv -> test_data_3.csv ...
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # all csvs in data folder
    all_files = os.listdir(DATA_DIR)

    # keep only input batch files, not duration files
    batch_files = []
    for file in all_files:
        if re.match(r"test_data_\d+\.csv$", file):
            batch_files.append(file)

    # sort by numeric suffix
    batch_files = sorted(
        batch_files, key=lambda x: int(re.search(r"test_data_(\d+)\.csv", x).group(1))
    )

    if not batch_files:
        raise ValueError("No batch files found in data folder.")

    # read last processed batch number
    last_processed = 0
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            last_processed = state.get("last_processed_batch", 0)

    # find next batch
    next_file = None
    next_batch_num = None

    for file in batch_files:
        batch_num = int(re.search(r"test_data_(\d+)\.csv", file).group(1))
        if batch_num > last_processed:
            next_file = file
            next_batch_num = batch_num
            break

    if next_file is None:
        print("No new batch file left to process.")
        return None, None, None

    input_file = os.path.join(DATA_DIR, next_file)
    actual_file = os.path.join(DATA_DIR, f"test_data_{next_batch_num}_duration.csv")
    output_file = os.path.join(OUTPUT_DIR, f"result_{next_batch_num}.csv")

    return input_file, actual_file, output_file


@task(retries=3, retry_delay_seconds=3)
def load_data(input_file):
    """Load batch input data"""
    df = pd.read_csv(input_file)
    return df


@task
def load_actual_duration(actual_file):
    """Load actual duration file if available"""
    if os.path.exists(actual_file):
        return pd.read_csv(actual_file)
    return None


@task
def load_model():
    """Load trained model"""
    model = joblib.load("./best_model.joblib")
    return model


@task
def generate_ids(df):
    """Generate unique ids for predictions"""
    return [str(uuid.uuid4()) for _ in range(len(df))]


@task
def predict_and_store_results(model, df, df_result_ids, actual_df, output_file):
    """Run batch prediction and save output"""

    y_pred = model.predict(df)

    df_result = pd.DataFrame()
    df_result["pred_id"] = df_result_ids

    for col in df.columns:
        df_result[col] = df[col]

    df_result["prediction"] = y_pred
    df_result["prediction_time"] = datetime.now()

    if actual_df is not None and "duration" in actual_df.columns:
        df_result["actual_duration"] = actual_df["duration"]

    df_result.to_csv(output_file, index=False)

    return output_file


@task
def update_state(input_file):
    """Update state file so next run picks the next batch"""
    batch_num = int(
        re.search(r"test_data_(\d+)\.csv", os.path.basename(input_file)).group(1)
    )

    state = {"last_processed_batch": batch_num, "last_run_time": str(datetime.now())}

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


@flow
def run_batch_prediction():
    """Prefect batch prediction flow"""

    input_file, actual_file, output_file = get_next_batch_file()

    if input_file is None:
        print("Flow exiting: no new batch to process.")
        return

    df = load_data(input_file)
    actual_df = load_actual_duration(actual_file)
    model = load_model()
    df_result_ids = generate_ids(df)

    predict_and_store_results(
        model=model,
        df=df,
        df_result_ids=df_result_ids,
        actual_df=actual_df,
        output_file=output_file,
    )

    update_state(input_file)


if __name__ == "__main__":
    run_batch_prediction()
# if __name__ == "__main__":
#     run_batch_prediction.serve(
#         name="taxi-batch-prediction",
#         interval=60  # every 2 hours
#     )
