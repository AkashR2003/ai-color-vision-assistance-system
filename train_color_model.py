import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

data = [
    # RED
    [255,0,0,"Red"], [200,30,30,"Red"], [180,20,20,"Red"],

    # GREEN
    [0,255,0,"Green"], [30,200,30,"Green"], [20,180,20,"Green"],

    # BLUE
    [0,0,255,"Blue"], [30,30,200,"Blue"], [20,20,180,"Blue"],

    # YELLOW
    [255,255,0,"Yellow"], [240,240,50,"Yellow"], [220,220,80,"Yellow"],

    # ORANGE
    [255,165,0,"Orange"], [230,140,20,"Orange"],

    # WHITE
    [255,255,255,"White"], [230,230,230,"White"],

    # BLACK
    [0,0,0,"Black"], [30,30,30,"Black"],
]

df = pd.DataFrame(data, columns=["R", "G", "B", "Label"])

X = df[["R", "G", "B"]]   # ✅ ONLY 3 FEATURES
y = df["Label"]

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, "color_model.pkl")

print("New Color Model Trained ✅")