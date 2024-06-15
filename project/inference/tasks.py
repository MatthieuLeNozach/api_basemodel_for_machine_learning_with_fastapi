from celery import shared_task


@shared_task
def run_regression():
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