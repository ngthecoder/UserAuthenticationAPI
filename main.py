from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, validator
from typing import Optional

app = FastAPI()
security = HTTPBasic()

class User(BaseModel):
    user_id: str
    password: str
    nickname: Optional[str] = None
    comment: Optional[str] = None

    @validator('user_id')
    def user_id_length(cls, v):
        if not (6 <= len(v) <= 20):
            raise ValueError('user_id must be 6 to 20 characters long')
        return v

    @validator('password')
    def password_length(cls, v):
        if not (8 <= len(v) <= 20):
            raise ValueError('password must be 8 to 20 characters long')
        return v

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    comment: Optional[str] = None

    @validator('nickname')
    def nickname_length(cls, v):
        if v is not None and len(v) > 30:
            raise ValueError('nickname must be within 30 characters')
        return v

    @validator('comment')
    def comment_length(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('comment must be within 100 characters')
        return v

users = {}

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    user_id, password = credentials.username, credentials.password
    user = users.get(user_id)
    if not user or user.password != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

@app.post("/signup", status_code=status.HTTP_200_OK)
def signup(user: User):
    if not user.user_id or not user.password:
        return {"message": "Account creation failed", "cause": "required user_id and password"}
    
    if user.user_id in users:
        return {"message": "Account creation failed", "cause": "already same user_id is used"}
    
    user.nickname = user.nickname or user.user_id

    users[user.user_id] = user
    return {"message": "Account successfully created", "user": {"user_id": user.user_id, "nickname": user.nickname}}

@app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
def get_user(user_id: str, user: User = Depends(authenticate_user)):
    if user.user_id != user_id:
        raise HTTPException(status_code=400, detail="No User found")
    
    user_details = {"user_id": user.user_id, "nickname": user.nickname or user.user_id}
    if user.comment:
        user_details["comment"] = user.comment

    return {"message": "User details by user_id", "user": user_details}

@app.patch("/users/{user_id}", status_code=status.HTTP_200_OK)
def update_user(user_id: str, update: UserUpdate, user: User = Depends(authenticate_user)):
    if user.user_id != user_id:
        raise HTTPException(status_code=403, detail="No Permission for Update")

    if not update.nickname and not update.comment:
        raise HTTPException(status_code=400, detail="required nickname or comment")

    current_user = users.get(user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="No User found")

    current_user.nickname = update.nickname if update.nickname is not None else current_user.nickname or current_user.user_id
    current_user.comment = update.comment if update.comment is not None else ""

    return {"message": "User successfully updated", "recipe": [{"nickname": current_user.nickname, "comment": current_user.comment}]}

@app.post("/close", status_code=status.HTTP_200_OK)
def close_account(user: User = Depends(authenticate_user)):
    if user.user_id in users:
        del users[user.user_id]
        return {"message": "Account and user successfully removed"}
    else:
        raise HTTPException(status_code=401, detail="Authentication Failed")

test_user = User(user_id="TaroYamada", password="PaSSwd4TY", nickname="たろー", comment="僕は元気です")
users[test_user.user_id] = test_user
