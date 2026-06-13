from typing import Optional, Annotated
from fastapi import FastAPI, HTTPException, Body, Query, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, constr, StringConstraints
import uvicorn

from User_Management import read_user, add_user, update_user

# This creates a security scheme for Swagger UI
bearer_scheme = HTTPBearer(auto_error=True)

# Hardcoded token for authentication
VALID_TOKEN = "u7-jh8gklj-987-traw8"

# Verify function for token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    if token != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
        )
    return token

PhoneRegex = r"^\+91-\d{5}-\d{5}$"
PhoneNumber = Annotated[str, StringConstraints(pattern=PhoneRegex)]

app = FastAPI(title="User Data Management")

# Data Model for create user record and update user record
class UserCreateModel(BaseModel):
    name: str = Field(..., min_length=2)
    age: int = Field(..., ge=18, le=120)
    city: str = Field(...)
    email: EmailStr
    phone_number: PhoneNumber


class UserUpdateModel(BaseModel):
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120)
    city: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[PhoneNumber] = None


# Get method for user - is not included with authentication
@app.get("/user", summary="Get User")
def get_user(user_id: str = Query(...)):
    """
    Returns masked user info for given user id.
    """
    try:
        user = read_user(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail=f"user {user_id} not found")

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Patch method for user - included with authentication
# Since patch method is used for data update, authentication needed
@app.patch("/user", summary="Update User")
def patch_user(payload: UserUpdateModel = Body(...),
               token: str = Depends(verify_token)):
    """
    Partial user update.
    for given user id, the provided fields are updated in the DB
    """
    body = payload.model_dump (exclude_unset=True)
    user_id = body.pop("user_id")

    body = {k: v for k, v in body.items() if v is not None}

    if not body:
        raise HTTPException(400, detail="No updatable fields provided")

    try:
        msg = update_user(user_id, **body)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {e}")

    updated_user = read_user(user_id)
    if updated_user is None:
        raise HTTPException(500, detail="Updated user not found")
    
    return {"message": msg, "user": updated_user}


# Post method for user - included with authentication
# Since Post method is used for record creation, authentication needed
@app.post("/add_user", summary="Add User", status_code=201)
def create_user(payload: UserCreateModel = Body(...),
                token: str = Depends(verify_token)):
    """
    Create a new user. Provided the details, it adds to DB and returns the user id
    
    """
    try:
        new_id = add_user(dict(payload))

    except Exception as e:
        raise HTTPException(500, detail=str(e))

    return {"user_id": new_id}


# -------------------------
# Run the app
# -------------------------
if __name__ == "__main__":
    uvicorn.run("6_Authentication:app", 
                host="0.0.0.0", 
                port=5603, 
                reload=True)