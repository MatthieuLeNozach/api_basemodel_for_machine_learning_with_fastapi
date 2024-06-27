from typing import Callable, Dict, Any

# Define a type for model functions
ModelFunction = Callable[..., list]

# Dictionary to store models and their metadata
model_registry: Dict[int, Dict[str, Any]] = {}

def register_model(
    index: int,name: str, problem: str, category: str, version: str, access_policy_id: int
):
    def decorator(func: ModelFunction):
        model_registry[index] = {
            "func": func,
            "name": name,
            "problem": problem,
            "category": category,
            "version": version,
            "access_policy_id": access_policy_id
        }
        return func
    return decorator

# Example model registration
@register_model(
    index=1,
    name="linreg_placeholder",
    problem="regression",
    category="linear",
    version="0.0.1",
    access_policy_id=1
)
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