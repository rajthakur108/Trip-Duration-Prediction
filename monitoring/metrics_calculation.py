import datetime
import logging
import time

import joblib
import pandas as pd
import psycopg
from evidently import ColumnMapping
from evidently.metrics import (
    ColumnDriftMetric,
    DatasetDriftMetric,
    DatasetMissingValuesMetric,
    RegressionQualityMetric,
)
from evidently.report import Report

SEND_TIMEOUT = 10
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s"
)
begin = datetime.datetime(2026, 9, 17, 0, 0)
reference_data = pd.read_csv("./data/reference_data.csv")
data = ["./data/result_1.csv", "./data/result_2.csv", "./data/result_3.csv"]

column_mapping = ColumnMapping(target="actual_duration", prediction="prediction")

report = Report(
    metrics=[
        ColumnDriftMetric(column_name="prediction"),
        DatasetDriftMetric(),
        DatasetMissingValuesMetric(),
        RegressionQualityMetric(),
    ]
)

create_table_statement = """
drop table if exists taxi_metrics;
create table taxi_metrics(
    timestamp timestamp,
    prediction_drift float,
    num_drifted_columns integer,
    share_missing_values float,
    rmse float,
    mae float,
    r2_score float
)
"""


def prep_db():
    """Function for creating the database and table inside the database"""
    with psycopg.connect(
        "host =localhost port=5432 user=postgres password=example", autocommit=True
    ) as conn:
        res = conn.execute("select 1 from pg_database where datname ='test'")
        if len(res.fetchall()) == 0:  # No database named test
            conn.execute("create database test;")
        with psycopg.connect(
            "host=localhost port=5432 dbname = test user=postgres password=example"
        ) as conn:
            conn.execute(create_table_statement)


def calculate_metric_postgres(curr, data_path, start_day):
    """Function for calculating thr prediction on a single row of the
    current data(simulated as single day) and then logging the resuts in the table(fraud_metrics)
    """

    current_data = pd.read_csv(data_path)
    remove_columns = ["pred_id", "Unnamed: 0", "prediction_time"]

    current_data.drop(columns=remove_columns, inplace=True)

    report.run(
        reference_data=reference_data,
        current_data=current_data,
        column_mapping=column_mapping,
    )
    results = report.as_dict()

    drift_score = results["metrics"][0]["result"]["drift_score"]
    num_drifted_columns = results["metrics"][1]["result"]["number_of_drifted_columns"]
    share_of_missing_values = results["metrics"][2]["result"]["current"][
        "share_of_missing_values"
    ]
    regression_metrics = results["metrics"][3]["result"]

    rmse = regression_metrics["current"]["rmse"]
    mae = regression_metrics["current"]["mean_abs_error"]
    r2_score = regression_metrics["current"]["r2_score"]

    curr.execute(
        "insert into taxi_metrics (timestamp,prediction_drift,num_drifted_columns,share_missing_values,rmse,mae,r2_score) values(%s, %s, %s, %s, %s, %s, %s)",
        (
            begin + datetime.timedelta(start_day),
            drift_score,
            num_drifted_columns,
            share_of_missing_values,
            rmse,
            mae,
            r2_score,
        ),
    )


def run():
    start_day = -1
    prep_db()
    last_send = datetime.datetime.now()

    with psycopg.connect(
        "host = localhost port=5432 dbname = test user=postgres password=example",
        autocommit=True,
    ) as conn:
        for data_path in data:
            with conn.cursor() as curr:
                start_day += 1
                calculate_metric_postgres(curr, data_path, start_day)

            new_send = datetime.datetime.now()
            time_elapsed = (new_send - last_send).total_seconds()
            if time_elapsed < SEND_TIMEOUT:
                time.sleep(SEND_TIMEOUT - time_elapsed)

            last_send = last_send + datetime.timedelta(seconds=10)
            logging.info("data sent")


if __name__ == "__main__":
    run()
