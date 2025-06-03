from sklearn.ensemble import RandomForestRegressor
import joblib
import numpy as np

# Dummy training data: 6 features and a target
X = np.array([
    [10, 20, 30, 40, 50, 60],
    [15, 25, 35, 45, 55, 65],
    [20, 30, 40, 50, 60, 70],
    [25, 35, 45, 55, 65, 75],
])
y = np.array([50, 60, 70, 80])  # dummy target AQI

# Train a simple model
model = RandomForestRegressor()
model.fit(X, y)

# Save the model to file
joblib.dump(model, 'airquality.joblib')
print("Model trained and saved as airquality.joblib")
