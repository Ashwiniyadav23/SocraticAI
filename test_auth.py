import requests
try:
    resp = requests.post("http://localhost:8000/v1/auth/google", json={"token": "test"})
    print("Status:", resp.status_code)
    print("JSON:", resp.json())
except Exception as e:
    print("Error:", e)
