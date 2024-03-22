# **Base model for a secured machine learning API with FastAPI**
### ***api_basemodel_for_machine_learning_with_fastapi (v0.2)***

This template serves as a starting point to integrate ML services into a secured API.

1. [**Installation**](#installation)
2. [**Getting started**](#getting-started)
3. [**What's ready to use?**](#whats-ready-to-use)
4. [**What must be implemented?**](#what-must-be-implemented)


```bash
├── app
│   ├── database.py
│   ├── devtools.py
│   ├── html_text_variables.py
│   ├── __init__.py
│   ├── main.py
│   ├── ml_models
│   │   ├── __init__.py
│   │   ├── v1.py
│   │   └── v2.py
│   ├── models.py
│   ├── routers
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── ml_service_v1.py
│   │   ├── ml_service_v2.py
│   │   └── users.py
│   ├── schemas.py
│   └── templates
│       └── home.html
├── __init__.py
├── readme.md
├── requirements.txt
├── run.sh
├── run_tests.sh
├── sqlite3
│   └── test_db.db
└── test
    ├── __init__.py
    ├── test_admin.py
    ├── test_auth.py
    ├── test_main.py
    ├── test_ml_service_v1.py
    ├── test_ml_service_v2.py
    ├── test_users.py
    └── utils.py
```



## **Installation** <a name="installation"></a>


```bash
git clone ...

chmod +x run.sh

```

## **Getting started** <a name="getting-started"></a>

### **A. Securize the project**
- **Add `.environment` folder to the `.gitignore` file** to stop exposing sensitive information to git commits 
- **Access the `.environment` folder** from repository root, the folder may be hidden. 
```bash
nano .environment/env.dev

nano .environment/env.test 
```

- **Replace the dummy secret keys with your own keys**. You can generate base64 secrets with this command:
```bash
openssl rand -base64 32
```

- **Change the `superuser` password**. Modify the file `app/devtools.py` with the credentials of your choice:
```py
# from app/devtools.py
def create_superuser(db: Session):
    superuser = User(
        username='superuser@example.com',
        first_name='Super',
        last_name='User',
        hashed_password=pwd_context.hash('8888'),
...
```
Only an admin can register another admin. A permanent admin can be created once logged-in as the `superuser`, by sending a `post` request to this address:
`http://localhost:8080/admin/create`

### **B. Run app in development mode**

`superuser` argument initializes an admin at startup and deletes it at shutdown.

```bash
./run.sh dev superuser
```
superuser credentials (from app/dev_tools.py):
```py
def create_superuser(db: Session):
    superuser = User(
        username='superuser@example.com',
        first_name='Super',
        last_name='User',
        hashed_password=pwd_context.hash('8888'),
        is_active=True,
        role='admin',
        has_access_v1=True,
        has_access_v2=True
    )
    db.add(superuser)
    db.commit()
```


### **The authentication flow**


#### **Authentication as Superuser**

```bash
curl -X 'POST' \
  'http://localhost:8080/auth/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=&username=superuser%40example.com&password=8888&scope=&client_id=&client_secret='
  ```


![alt text](<readme/2.png>)




#### **Access Machine Learning services**

From `http://localhost:8080/docs`:
1. Authenticate:
Click on the lock
![alt text](<readme/3.png>)
2. Add superuser credentials
![alt text](<readme/4.png>)
3. Send input text
![alt text](<readme/5.png>)
4. Get output
![alt text](<readme/6.png>)




## **What's ready to use?** <a name="whats-ready-to-use"></a>

### **3.1 Endpoints and routers**

#### **A. Router structure**

To achieve separation of concerns and improved code organization, endpoints and helper functions are grouped into logical modules with their own namespaces (ex `/admin/...`):

- **auth** router file for registration / security related helpers and endpoint functions (see below)
- **admin** router file for admin specific actions, like grant/revoke access rights, delete user
- **user** router file for user specific actions (change password, #TODO get service call history)
- **ml_service_v1 / ml_service_v2**

#### **B. Endpoints**
API endpoints documentation (see below), and HTTP request templates are available at this address:
`http://localhost:8080/docs`

![alt text](<readme/1.png>)


### **3.2 Database**

This template populates 2 SQL tables, one registers the users and the other the service calls

```py
# from models.py
class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(127), unique=True)
    first_name: Mapped[str] = mapped_column(String(127))
    last_name: Mapped[str] = mapped_column(String(127))
    country: Mapped[str] = mapped_column(String(127), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(255))
    has_access_v1: Mapped[bool] = mapped_column(Boolean, default=False)
    has_access_v2: Mapped[bool] = mapped_column(Boolean, default=False)
    service_calls = relationship('ServiceCall', back_populates='user')

class ServiceCall(Base):
    __tablename__ = 'service_calls'
    
    id: Mapped[str] = mapped_column(Integer, primary_key=True, index=True)
    service_version: Mapped[str] = mapped_column(String(2))
    #priority: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    request_time: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    completion_time: Mapped[DateTime] = mapped_column(DateTime)
    duration: Mapped[Interval] = mapped_column(Interval)
    user = relationship('User', back_populates='service_calls')
```

#### **A. Users**

- The **username is an email address**, the email format is enforced. It must be unique.
- The columns `role`, `has_access_v1` and `has_access_v2` influence endpoint access and permissions (see security and credentials)

Users register themselves at this endpoint `/auth/create`, here is the form schema:

```py
# from schemas.py
class CreateUser(BaseUser):
    first_name: str
    last_name: str
    password: str
    country: Optional[str] = None
```
Users have permissions set to `False` by default, only an authenticated admin can grant them service access.   
To achieve this, a put request must be sent to this endpoint: `/admin/users/{user_id}` (replace {user_id} by the user's actual id).  
Here is the form schema:
```py
# from schemas.py
class ChangeUserAccessRights(BaseModel):
    is_active: bool
    has_access_v1: bool
    has_access_v2: bool
```


#### **B. ServiceCalls**
The **`ServiceCalls`** table serves as a comprehensive log, recording essential details for every service call made. It captures information crucial for deriving insights into both user-specific activity and global service usage patterns.

![alt text](<readme/7.png>)

The goal of this template is to serve as many purposes as possible without having to remove content. 
It is however easy to implement related tables that track user activity and service usage with more granularity.
Here's an example:  
```py
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class UserSpecificAnalytics(Base):
    """Table for user-specific analytics."""
    __tablename__ = 'user_specific_analytics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total_service_calls = Column(Integer)
    
    user = relationship('User', back_populates='specific_analytics')


class GlobalServiceUsageAnalytics(Base):
    """Table for global service usage analytics."""
    __tablename__ = 'global_service_analytics'
    
    id = Column(Integer, primary_key=True)
    hour_of_day = Column(Integer)
    day_of_week = Column(Integer)
    service_version = Column(String(2))
    total_service_calls = Column(Integer)
```



## **3.3 Security**

The API prioritizes security by utilizing various mechanisms:

**1. Password Hashing:**

- User passwords are never stored in plain text. They are hashed using a secure algorithm (`bcrypt`) before being saved in the database. This makes them significantly harder to crack in case of a data breach.

**2. JSON Web Tokens (JWT):**

- JWTs are used for user authentication. Users receive a JWT token after successful login, containing user information (username, ID, role, access rights) and an expiration time. Subsequent requests require including this token in the authorization header for verification.

```py
`# from auth.py
from jose import jwt, JWTError

SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = 'HS256'


def create_access_token(token_data: TokenData) -> str:
    encode = token_data.dict()
    expires = datetime.utcnow() + token_data.expires_delta
    encode.update({'exp': expires})
    encode.pop('expires_delta', None)
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: Annotated[str, Depends(oauth2bearer)]
) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # ... extract user information from payload
        return {
            'username': username,
            'id': user_id,
            'role': role,
            'has_access_v1': has_access_v1,
            'has_access_v2': has_access_v2
        }
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')`
```

**3. Role-Based Access Control (RBAC):**

- The API leverages RBAC to control user access to resources. User roles (e.g., "admin," "user") and access rights (e.g., `has_access_v1`, `has_access_v2`) are stored within the JWT token. Dependency injection in routers verifies a user's token and permissions before processing requests.


```py
`# ... other imports
from ..auth import get_current_user
from ..models import User

# ...
ml_model_v1_dependency = Annotated[PlaceholderMLModelV1, Depends(get_ml_model_v1)]

async def make_prediction_v1(prediction_input: PredictionInput, user: user_dependency, db: db_dependency, model: ml_model_v1_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is None")
    
    if not user.get('has_access_v1'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not have access to the service")
    
    # ... other code`
```
**4. Dependency Injection for Security:**
- Dependency injection (DI) strengthens security by promoting:
    - **Improved Modularity:** Security logic for creating database connections, user objects, or JWT tokens resides in dedicated functions, making them easier to test and isolate vulnerabilities.
    - **Clear Authorization Logic:** Dependencies like `user_dependency` inject user information into routes. You can then leverage the user's role or access rights within the route logic for clean and centralized authorization checks.

**5. Environment Variables:**

- Sensitive information like the JWT secret key is stored as environment variables and not directly in the code for improved security.

By implementing these security measures, the API provides a robust authentication and authorization system to protect user data and resources.

The files containing the environment variables are found in `.environment` directory. 

**[Caution] Don't forget to add the files containing the sensitive environment variables into the gitignore!**


### **3.3. Tests**

Run a test session with pytest:
```bash
chmod +x run_tests.sh

./run_tests.sh

# or in verbose mode:
./run_tests./sh -v 
```

####  **Test Setup and Fixtures:**

- Test context and fixtures are declared in `test/utils.py`. For convenience within test files, it's recommended to use `from .utils import *` at the beginning.

#### **Potential Test Failure Points:**

During test development or codebase changes, a test might fail even though the endpoint functions correctly in real-world scenarios. Here are common reasons for such failures:

1. **Dependency Override Issues:**
    - The `get_current_user` dependency is used to grant or revoke user access rights within tests.
    - If a test fails due to unexpected access permissions, ensure the dependency override in `test/utils.py` is set up correctly with the desired access level before the test function or class definition.
2. **User Fixture Misconfiguration:**
    - User fixtures in `test/utils.py` provide pre-defined user objects for testing purposes.
    - If a test fails due to user access issues, verify the user fixture configuration in `test/utils.py` aligns with the expected access rights for the test. Different fixtures might be available for granting or revoking specific permissions.
3. **Database Issues:**
    - Tests should ensure the database is properly populated with relevant data during each test and purged of any leftover data afterwards.
    - Utilize a context manager like `TestingSessionLocal` to achieve this. Here's the approach:
    
```py
from .utils import TestingSessionLocal

def test...():
    with TestingSessionLocal() as db:
        user = db.query(User).filter_by(username=user_data['username']).first()
        assert ...
```

### **3.4 Docker container**
Build and run  the api as a single container, for development purposes:
```bash
docker build -t ml_api_base:latest

docker run ml_api_base:latest
```




## **What must be implemented?** <a name="what-must-be-implemented"></a>


### **4.1. Machine Learning models**

Both services are just placeholders for now, but they are thought as containers for ML pipelines or trained models, which accept asynchrounous loading and prediction calls:


```py
class PlaceholderMLModelV1:
    def __init__(self):
        self.loaded = False
        self.model = None

    async def load_model(self):
        # Implementation for loading the actual model (placeholder removed)
        self.loaded = True

    async def predict(self, input: PredictionInput) -> PredictionOutput:
        if not self.loaded:
            await self.load_model()
        
        import random
        category = 'Category A' if int(len(input.text) * random.random()) % 2 else 'Category B'
        
        return PredictionOutput(category=category)
```

These models are lazily loaded during application startup:
```py
# from main.py
############### LIFESPAN ###############
@app.on_event('startup')
async def startup_event():
    ...
    ml_service_v1.placeholder_ml_model_v1.load_model()
    ml_service_v2.placeholder_ml_model_v2.load_model()
```

...and are invoked using dependency injection:
```py
# from routers/ml_service_v1.py
async def get_ml_model_v1(model: PlaceholderMLModelV1 = Depends()) -> PlaceholderMLModelV1:
    """Dependency to lazy-load a ML model"""
    if not model.loaded:
        await model.load_model()
    return model

...
ml_model_v1_dependency = Annotated[PlaceholderMLModelV1, Depends(get_ml_model_v1)]
```

Specific schemas should be created to match the model's input (ex categorical / numerical feature values) and output (ex a single value for classification, multiple values for sentiment analysis etc.)

Here's an example:
```py
from pydantic import BaseModel

class HousePricePredictionInput(BaseModel):
    age: int
    surface: float
    has_attic: bool
    garden_surface: float
    address: str

class HousePricePredictionOutput(BaseModel):
    price: float
```

By leveraging asynchronicity and lazy loading, the system ensures efficient resource utilization and responsive handling of requests, enhancing scalability and performance.


### **4.2 Model specific tables**

For now, only one User and one ServiceCall tables are implemented.  
Based on the type of predictor to implement, the model activity and performance should also be logged in another table.  

Taking the example of the house price prediction, we'd like to store the predicted prices, and get information about the model performances once the actual sale price is known . A new table could be created like this:
```py
# file: database.py
from sqlalchemy.orm import declarative_base
Base =  declarative_base()
...

# file: models.py
from database import Base

class MLModelLog(Base):
    __tablename__ = 'model_logs'
    
    id: Mapped[str] = mapped_column(Integer, primary_key=True, index=True)
    service_call_id: Mapped[int] = mapped_column(Integer, ForeignKey('service_calls.id'))
    is_train_data: Mapped[bool] = mapped_column(Boolean, default=False)
    r_2: Mapped[float] = mapped_column(Float, nullable=True)
    mae: Mapped[float] = mapped_column(Float, nullable=True)
    target_pred: Mapped[float] = mapped_column(Float)
    target_true: Mapped[float] = mapped_column(Float, nullable=True)
    feature_age: Mapped[int] = mapped_column(int)
    feature_surface: Mapped[float] = mapped_column(Float)
    feature_has_attic: Mapped[bool] = mapped_column(Boolean)
    feature_garden_surface: Mapped[float] = mapped_column(Float)
    feature_address: Mapped[str] = mapped_column(String)
    service_call = relationship('ServiceCall', back_populates='service_calls')
```


### **4.3 Production database**

#### **A. Database server**
Move the database from SQLite to a server hosted database (ex PostGreSQL, MySQL...)

Having such a structure also implies to have a migration tool setup...

#### **B. Setup Alembic migration tool**
Allowing a smooth scaling into new database functionalities

- Installation:
```bash
pip install alembic
# or
conda install alembic
# then
alembic init alembic
```

- Make the necessary changes in `alembic.ini`
  - adjust the database url:
```ini
...
sqlalchemy.url = :///./your/path/to/prod_db.db
...
```
etc
- Create a migration script
```bash
alembic revision -m "initial migration"
```  
- in alembic's `env.py`, check that the `target_metadata` is set `models.Base.metadata`
- Run the migration (upgrade to commit new structure or downgrade to rollback)
```bash
alembic upgrade head
# or
alembic downgrade head
```

### **4.4 Docker Compose**

For now, the api can live inside a single container, for development purposes only. 
Sensitive environment variables are currently exposed at image build,  they should be passed via a docker compose file instead of having them built-in. 

Aside from security issues, a single docker container handling api endpoints, database management and machine learning predictions is far from ideal.