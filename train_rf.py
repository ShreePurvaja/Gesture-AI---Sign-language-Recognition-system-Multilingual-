import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

X = np.load("X.npy")
y = np.load("y.npy")

model = RandomForestClassifier(n_estimators=300)
model.fit(X, y)

joblib.dump(model, "rf_model.pkl")
print("Random Forest trained")
