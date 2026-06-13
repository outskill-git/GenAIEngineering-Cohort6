from typing import Optional, Annotated
from fastapi import FastAPI, HTTPException, Body, status, Query
from pydantic import BaseModel, Field, EmailStr, constr, StringConstraints
import uvicorn

from User_Management import read_user, add_user, update_user

PhoneRegex = r"^\+91-\d{5}-\d{5}$"
PhoneNumber = Annotated[str, StringConstraints(pattern=PhoneRegex)]

app = FastAPI(title="User Data Management")

# Define data model as class based on pydantic
# class for create user
class UserCreateModel(BaseModel):
    name: str = Field(..., min_length=2)
    age: int = Field(..., ge=18, le=120)
    city: str = Field(...)
    email: EmailStr
    phone_number: PhoneNumber

# class for update user
class UserUpdateModel(BaseModel):
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120)
    city: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[PhoneNumber] = None


# Get method for user end point
# Based on query param, which is string. No date model used here
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


# Patch method user
# Its for updating a user record
# Corresponding data model is used
@app.patch("/user", summary="Update User")
def patch_user(payload: UserUpdateModel = Body(...)):
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


# -------------------------
# POST /add_user
# -------------------------
@app.post("/add_user", summary="Add User", status_code=201)
def create_user(payload: UserCreateModel = Body(...)):
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
    uvicorn.run("5_Pydantic_Checks:app", 
                host="0.0.0.0", 
                port=5602, 
                reload=True)
