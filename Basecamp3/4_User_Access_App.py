
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Body, status
import uvicorn

# Import from the User Management Module
from User_Management import read_user, add_user, update_user

# FastAPI app
app = FastAPI(title="User Data Management")

# Declaration of End point User with GET method
@app.get("/user", summary="Get User")
def get_user(user_id: str):
    """
    Read user by user_id (query param).
    Example: GET /user?user_id=U_0001
    Returns masked contact info (as produced by user_csv_store.read_user).
    """
    try :
        user = read_user(user_id)
        return user
    
    except Exception :
        return "Error Fetching Details"

# User end point with PATCH meethod
# Patch is used to update record partially

@app.patch("/user", summary="Update User")
def patch_user(payload: Dict[str, Any] = Body(...)):
    """
    Update user fields. Expect JSON body with:
    {
      "user_id": "U_0001",
      "name": "New Name",          # optional
      "age": 32,                  # optional
      "city": "New City",         # optional
      "email": "x@y.com",         # optional
      "phone_number": "+91-..."   # optional
    }
    Returns confirmation message and updated user record.
    """
    
    # Error Handling in the request input
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request body must be a JSON object")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'user_id' in request body")

    # Make a copy of payload and remove the user id

    user_details = dict (payload)
    user_details.pop ('user_id', None)
    
    # invoke the update user function
    try:
        # print (payload)
        msg = update_user(user_id, **user_details)        

        # Read back the record for confirmation
        try :
            updated = read_user(user_id)

        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User not found after update")
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update user: {e}")

    # Return the status of update and the updated record
    return {"message": msg, "user": updated}


# Adding of a User record with add_user end point
@app.post("/add_user", summary="Add User")
def create_user(payload: Dict[str, Any] = Body(...)):
    """
    Add a new user. Expect JSON body with keys:
    {
      "name": "...",
      "age": 30,
      "city": "...",
      "email": "...",
      "phone_number": "+91-xxxxx-xxxxx"
    }
    Returns: {"user_id": "U_0021"}
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request body must be a JSON object")

    required = {"name", "age", "city", "email", "phone_number"}
    missing = required - set(payload.keys())
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing fields: {sorted(list(missing))}")

    # Invoke Add user function
    try:
        new_id = add_user(payload)
   
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add user: {e}")

    return {"user_id": new_id}


# Execute the Uvicorn app
if __name__ == "__main__":
    uvicorn.run("4_User_Access_App:app", 
                host="0.0.0.0", 
                port=5601, 
                reload=True)
