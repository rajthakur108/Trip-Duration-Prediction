def test_model_prediction(model, trip):
    pred = model.predict(trip)
    assert pred >= 0
