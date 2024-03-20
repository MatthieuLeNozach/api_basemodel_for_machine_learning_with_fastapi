# **api_basemodel_for_machine_learning_with_fastapi**

This is a template to integrate 2 machine learning services in a secured API.

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
chmod +x run_tests.sh

```

## **Getting started** <a name="getting-started"></a>

### **Run app in development mode**

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

### **Run app in production mode with PostGreSQL server (#TODO)**

```bash
./run.sh prod
```

### **The authentication flow**


![alt text](<Screenshot from 2024-03-20 15-56-59.png>)


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

### **3.1 Database**

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

- The username must be an email address
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
This table creates a row with basic information for every service call, and collects raw data t information that can be aggregated into insightful user activity info.

![alt text](<readme/7.png>)


### **3.2 Router structure**

To achieve separation of concenrn and improved code organization, endpoints and helper functions are grouped into logical modules with their own namespaces (ex `/admin/...`):

- **auth** router file for registration / security related helpers and endpoint functions (see below)
- **admin** router file for admin specific actions, like grant/revoke access rights, delete user
- **user** router file for user specific actions (change password, #TODO get service call history)
- **ml_service_v1 / ml_service_v2**




## **3.3 Security**

The API prioritizes security by utilizing various mechanisms:

**1. Password Hashing:**

- User passwords are never stored in plain text. They are hashed using a secure algorithm (`bcrypt`) before being saved in the database. This makes them significantly harder to crack in case of a data breach.

**2. JSON Web Tokens (JWT):**

- JWTs are used for user authentication. Users receive a JWT token after successful login, containing user information (username, ID, role, access rights) and an expiration time. Subsequent requests require including this token in the authorization header for verification.

**Code Snippet (auth.py):**
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

**Code Snippet (routers/ml_service_v1.py):**

**Python**
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
    - **Controlled Object Lifecycle:** DI allows for secure object management (e.g., closing database connections after use, invalidating JWT tokens upon logout).
    - **Clear Authorization Logic:** Dependencies like `user_dependency` inject user information into routes. You can then leverage the user's role or access rights within the route logic for clean and centralized authorization checks.

**5. Environment Variables:**

- Sensitive information like the JWT secret key is stored as environment variables and not directly in the code for improved security.

By implementing these security measures, the API provides a robust authentication and authorization system to protect user data and resources.


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

Taking the example of the house price prediction, we would be interested to compare the price predictions and the actual sale price later. A new table could be created like this:
```py
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