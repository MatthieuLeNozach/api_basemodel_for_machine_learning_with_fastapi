import factory
from factory import LazyAttribute, Faker
from uuid import uuid4
from fastapi_users.password import PasswordHelper
from datetime import datetime

from project.database import async_session_maker
from project.fu_core.users.models import User
from project.inference.models import (
    UserAccess,
    ServiceCall,
    InferenceModel,
    AccessPolicy
) 

password_helper = PasswordHelper()

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = async_session_maker()
        sqlalchemy_session_persistence = "commit"
        
    id = LazyAttribute(lambda _: uuid4())
    email = Faker("email")
    hashed_password = factory.LazyFunction(lambda: password_helper.hash("password"))
    is_active = True
    is_superuser = False
    is_verified = False
    
    
class AccessPolicyFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AccessPolicy
        sqlalchemy_session = async_session_maker()
        sqlalchemy_session_persistence = "commit"
        
    id = factory.sequence(lambda n: n)
    name = Faker("word")
    daily_api_calls = 1000
    monthly_api_calls = 30000
    
    

class InferenceModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = InferenceModel
        sqlalchemy_session = async_session_maker()
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    name = Faker("word")
    problem = Faker("word")
    category = Faker("word")
    version = "1.0.0"
    first_deployed = LazyAttribute(lambda _: datetime.now())
    last_updated = LazyAttribute(lambda _: datetime.now())
    deployment_status = "Pending"
    in_production = False
    mlflow_id = Faker("uuid4")
    source_url = Faker("url")
    access_policy_id = factory.SubFactory(AccessPolicyFactory)


class UserAccessFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserAccess
        sqlalchemy_session = async_session_maker()
        sqlalchemy_session_persistence = "commit"

    user_id = LazyAttribute(lambda _: uuid4())
    model_id = factory.SubFactory(InferenceModelFactory)
    access_policy_id = factory.SubFactory(AccessPolicyFactory)
    api_calls = 0
    access_granted = True
    last_accessed = LazyAttribute(lambda _: datetime.now())


class ServiceCallFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ServiceCall
        sqlalchemy_session = async_session_maker()
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    model_id = factory.SubFactory(InferenceModelFactory)
    user_id = LazyAttribute(lambda _: uuid4())
    time_requested = LazyAttribute(lambda _: datetime.now())
    time_completed = None
    celery_task_id = Faker("uuid4")
    
    
    
    
