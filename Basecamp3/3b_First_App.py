from fastapi import FastAPI, Body, Header
import uvicorn
import time
from datetime import datetime

app = FastAPI()

# End Point definition with a GET method
@app.get("/welcome")
def welcome (name : str):
    """
    GET /welcome : Takes name as input
    Returns a welcome message
    """

    return "Welcome "+str(name)+". This is your first FastAPI app ...!"

# End Point definition with a GET method
# This function simulates a delay
@app.get("/test")
def test ():
    """
    Simulates a delay and return a string
    """
    st = datetime.now ()
    time.sleep (5)
    en = datetime.now ()

    return "Entry : "+str(st)+" | Exit : "+str(en)

# End point data with PUT method
@app.put("/data")
def welcome (q_param : int,
             record_id : str = Header (...),
             record : str = Body (...)):
    """
    PUT /data : 
    q_param (int) as query param input
    record_id (str) as Header
    record (str) as Body 
    
    Returns a JSON data
    """

    return {'q_param' : str(q_param),
            'record_id' : record_id,
            'record' : record}

# Uvicorn startup block
if __name__ == "__main__":
    uvicorn.run(
        "3b_First_App:app",
        host="0.0.0.0",
        port=5600,
        reload=True
    )
