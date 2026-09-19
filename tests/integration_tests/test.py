import pandas as pd


def test_prediction_output():

    df = pd.read_csv("./tests/integration_tests/result_1.csv")

    # Check output exists and has rows
    assert len(df) > 0

    # Check prediction column exists
    assert "prediction" in df.columns


def test_prediction_count():

    input_df = pd.read_csv("./data/test_data_1.csv")
    output_df = pd.read_csv("./tests/integration_tests/result_1.csv")

    # Same number of predictions as input records
    assert len(input_df) == len(output_df)
