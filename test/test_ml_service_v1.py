# file: test/test_admin.py

from fastapi import status
from datetime import timedelta

from .utils import *
from ..app.routers.ml_service_v1 import get_db, get_current_user
from ..app.models import User, ServiceCall
from ..app.routers.auth import create_access_token
from ..app.schemas import PredictionInput, TokenData



app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_healthcheck_v1():
    response = client.get('/mlservice/v1/healthcheck')
    print(response.json())
    assert response.status_code == status.HTTP_200_OK


class TestMakePredictionV1:
    @pytest.fixture(autouse=True)
    def setup(self, test_superuser, test_user_revoked):
        superuser_token_data = TokenData(
            username=test_superuser.username,
            user_id=test_superuser.id,
            role=test_superuser.role,
            has_access_v1=test_superuser.has_access_v1,
            has_access_v2=test_superuser.has_access_v2,
            expires_delta=timedelta(minutes=30)
        )
        self.superuser_token = create_access_token(superuser_token_data)

        revoked_user_token_data = TokenData(
            username=test_user_revoked.username,
            user_id=test_user_revoked.id,
            role=test_user_revoked.role,
            has_access_v1=test_user_revoked.has_access_v1,
            has_access_v2=test_user_revoked.has_access_v2,
            expires_delta=timedelta(minutes=30)
        )
        self.revoked_user_token = create_access_token(revoked_user_token_data)
    def test_endpoint_ok(self):
        input_data = PredictionInput(text="Sample test for prediction")
        headers = {'Authorization': f'Bearer {self.superuser_token}'}
        response = client.post('/mlservice/v1/predict', json=input_data.dict(), headers=headers)
        assert response.status_code == status.HTTP_200_OK
     
    def test_not_legit_user_cannot_call_service(self):
        app.dependency_overrides[get_current_user] = override_get_current_user_revoked
        input_data = PredictionInput(text='Sample text for prediction')
        headers = {'Authorization': f'Bearer {self.revoked_user_token}'}
        response = client.post('/mlservice/v1/predict', json=input_data.dict(), headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_predict_legit_user(self):
        app.dependency_overrides[get_current_user] = override_get_current_user
        input_data = PredictionInput(text='Sample text for prediction')
        headers = {'Authorization': f'Bearer {self.superuser_token}'}
        response = client.post('/mlservice/v1/predict', json=input_data.dict(), headers=headers)
        assert response.status_code == status.HTTP_200_OK

