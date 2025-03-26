import pytest
import json
import pandas as pd
from io import BytesIO
from backend import app, process_reconciliation, train_anomaly_model, predict_anomalies

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_reconcile_endpoint(client):
    test_data = pd.DataFrame({
        "Column1": [100, 200, 300],
        "Column2": [95, 195, 310]
    })
    excel_buffer = BytesIO()
    test_data.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    response = client.post("/reconcile", data={"file": (excel_buffer, "test.xlsx")})
    data = response.get_json()
    
    assert response.status_code == 200
    assert "processed_count" in data
    assert "anomalous_count" in data

def test_train_model(client):
    response = client.post("/train/model", data={})
    assert response.status_code == 200
    assert "message" in response.get_json()

def test_anomaly_detection():
    df = pd.DataFrame({
        "feature1": [1, 2, 100],
        "feature2": [1, 2, 100]
    })
    model = train_anomaly_model(df, ["feature1", "feature2"])
    assert model is not None

    anomalies = predict_anomalies(df, ["feature1", "feature2"])
    assert len(anomalies) == len(df)
    assert "Yes" in anomalies

def test_get_options(client):
    response = client.get("/chat/options")
    assert response.status_code == 200
    assert isinstance(response.get_json(), dict)
