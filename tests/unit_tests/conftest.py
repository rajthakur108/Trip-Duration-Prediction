from pathlib import Path

import joblib
import pandas as pd
import pytest


@pytest.fixture
def model():
    project_root = Path(__file__).parents[2]
    model_path = project_root / "model-building" / "best_model.joblib"
    return joblib.load(model_path)


@pytest.fixture
def trip():
    return pd.DataFrame(
        [
            {
                "pickup_hour": 15,
                "pickup_day": 11,
                "pickup_month": 1,
                "pickup_weekday": 6,
                "passenger_count": 1.0,
                "trip_distance": 2.87,
                "PULocationID": 74,
                "DOLocationID": 239,
                "PU_DO": "74_239",
            }
        ]
    )


@pytest.fixture
def input_columns():
    return [
        "pickup_hour",
        "pickup_day",
        "pickup_month",
        "pickup_weekday",
        "passenger_count",
        "trip_distance",
        "PULocationID",
        "DOLocationID",
        "PU_DO",
    ]
