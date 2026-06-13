from fastapi import FastAPI

# Define an App
app = FastAPI()

@app.get("/")
def base ():
    return "My First API ..."

# To launch this App :
# From command prompt / console, activate the env that has fastapi package installed
# Command :
# fastapi dev <py file name>
#
# This will launch the Fast API app at a port (default localhost:8000)
#
# From browser type localhost:8000 to invoke the API