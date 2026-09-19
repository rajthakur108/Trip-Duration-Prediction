def test_feature_engineering(model, trip, input_columns):
    pred = model.named_steps["preprocessor"].transform(trip)
    assert pred.shape[1] == 2788
