def test_input_data(trip, input_columns):
    assert list(trip.columns) == input_columns
