import joblib
import pandas as pd

model = joblib.load("color_model.pkl")

def predict_confusion(color1, color2):
    data = pd.DataFrame([{
        'r1': color1[0],
        'g1': color1[1],
        'b1': color1[2],
        'r2': color2[0],
        'g2': color2[1],
        'b2': color2[2]
    }])

    return model.predict(data)[0]