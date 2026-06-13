import streamlit as st
import requests
import json

st.set_option('client.showErrorDetails', False)

# Page title
st.set_page_config(page_title="User Management Portal", layout="centered")
st.title("User Management")
st.write("Front End UI for User Management App")

# App URL and Authentication token entry
st.sidebar.header("App & Authentication")
BASE_URL = st.sidebar.text_input("API App URL", help="Enter your App location")
token_input = st.sidebar.text_input("Bearer token", type="password", help="Enter token")

# Select action
action = st.selectbox("Select action", ["user GET", "user PATCH", "add_user POST"])

# Internal functions
def pretty(obj):
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)

def get_headers(require_auth: bool):
    headers = {"Accept": "application/json"}
    if require_auth and token_input:
        headers["Authorization"] = f"Bearer {token_input}"
    return headers

def show_response(resp):
    st.write("Status:", resp.status_code)
    try:
        data = resp.json()
        st.json(data)
        # st.text_area("Raw response (JSON)", pretty(data), height=240)
    except Exception:
        st.text_area("Raw response (text)", str(resp), height=200)


# UI elements
if action == "user GET":
    st.subheader("GET /user")
    user_id = st.text_input("user_id", value="")
    if st.button("Fetch user"):
        params = {"user_id": user_id}
        try:
            resp = requests.get(f"{BASE_URL}/user", params=params, headers=get_headers(False), timeout=10)
            show_response(resp)
        except requests.RequestException as e:
            st.error(f"Request failed: {e}")
            pass

elif action == "user PATCH":
    st.subheader("PATCH /user")
    st.write("Provide user_id and any fields to update. Inputs are sent exactly as entered.")
    user_id = st.text_input("user_id", value="")
    name = st.text_input("name", value="")
    city = st.text_input("city", value="")
    age = st.text_input("age", value="")
    phone_number = st.text_input("phone_number", value="")
    email = st.text_input("email", value="")

    if st.button("Update user"):
        payload = {
            "user_id": user_id,
            "name": name,
            "city": city,
            "age": age,
            "phone_number": phone_number,
            "email": email,
        }
        # print ("Before cleaning : \n", payload)
        
        # Take non empty fields alone 
        payload = {k : v for k, v in payload.items () if v != ""}
        # print ("After cleaning : \n", payload)
        
        try:
            resp = requests.patch(f"{BASE_URL}/user", json=payload, headers=get_headers(require_auth=True), timeout=10)
            show_response(resp)
        except requests.RequestException as e:
            st.error(f"Request failed: {e}")

else:  # add_user POST
    st.subheader("POST /add_user")
    st.write("Provide new user details. Inputs are sent exactly as entered.")
    name = st.text_input("name", value="")
    city = st.text_input("city", value="")
    age = st.text_input("age", value="")
    phone_number = st.text_input("phone_number", value="")
    email = st.text_input("email", value="")

    if st.button("Add user"):
        payload = {
            "name": name,
            "city": city,
            "age": age,
            "phone_number": phone_number,
            "email": email,
        }
        try:
            resp = requests.post(f"{BASE_URL}/add_user", json=payload, headers=get_headers(require_auth=True), timeout=10)
            show_response(resp)
        except requests.RequestException as e:
            st.error(f"Request failed: {e}")

st.markdown("---")
st.caption("Note: UI for managing the user data")
