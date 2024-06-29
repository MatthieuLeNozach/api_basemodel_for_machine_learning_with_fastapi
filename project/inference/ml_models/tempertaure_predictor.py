from typing import List
from pydantic import BaseModel


class TemperatureModel:

    class Input(BaseModel):
        latitude: int
        longitude: int
        month: int
        hour: int

    class Output(BaseModel):
        temperature: float

    class Dataset:
        @staticmethod
        def generate(np):
            # Generate synthetic dataset
            np.random.seed(42)
            latitudes = np.random.randint(-90, 90, 1000)
            longitudes = np.random.randint(-180, 180, 1000)
            months = np.random.randint(1, 13, 1000)
            hours = np.random.randint(0, 24, 1000)
            temperatures = (
                30 - np.abs(latitudes) / 3 + np.sin((months - 1) / 12 * 2 * np.pi) * 10
                + np.cos((hours - 12) / 24 * 2 * np.pi) * 5
                + np.random.normal(0, 2, 1000)
            )
            X = np.column_stack((latitudes, longitudes, months, hours))
            y = temperatures
            return X, y

    def __init__(self):
        import numpy as np
        from sklearn.linear_model import LinearRegression
        
        self.np = np
        self.LinearRegression = LinearRegression
        self.model = self.LinearRegression()
        
        X, y = self.Dataset.generate(self.np)
        self.model.fit(X, y)

    def predict(self, input_data: Input) -> Output:
        X_new = self.np.array([[input_data.latitude, input_data.longitude, input_data.month, input_data.hour]])
        temperature = self.model.predict(X_new)[0]
        return self.Output(temperature=temperature)