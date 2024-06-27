from typing import Callable, Dict

# Define a type for model functions
ModelFunction = Callable[..., list]

# Dictionary to store models
model_registry: Dict[int, ModelFunction] = {}

def register_model(index: int):
    def decorator(func: ModelFunction):
        model_registry[index] = func
        return func
    return decorator


@register_model(1)
def placeholder_linreg_model():
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.datasets import make_regression

    # Generate synthetic dataset with only numeric features
    X, y = make_regression(n_samples=100, n_features=3, noise=0.1)
    
    # Create and fit the model
    model = LinearRegression()
    model.fit(X, y)
    
    # Make predictions
    predictions = model.predict(X)
    
    return predictions.tolist()
