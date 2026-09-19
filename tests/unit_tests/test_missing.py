import pandas as pd


def test_feature_transformation_no_missing(model, trip):

    transformed = model.named_steps["preprocessor"].transform(trip)

    assert not pd.isna(transformed)
