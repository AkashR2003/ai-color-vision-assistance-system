import joblib
import numpy as np

model = joblib.load("color_model.pkl")

def predict_color(r, g, b):
    data = np.array([[r, g, b]])
    prediction = model.predict(data)[0]
    return prediction