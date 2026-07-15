import asyncio
import websockets
import json
import sys
import uuid
import requests

async def test():
    # Login to get token
    login_resp = requests.post("http://localhost:8000/v1/auth/login", json={"email":"test@test.com", "password":"testpassword123"})
    if login_resp.status_code != 200:
        print("Login failed:", login_resp.text)
        sys.exit(1)
    token = login_resp.json()["access_token"]
    
    # Start session
    session_resp = requests.post("http://localhost:8000/v1/session/auto", json={"message": "hello"}, headers={"Authorization": f"Bearer {token}"})
    if session_resp.status_code != 200:
        print("Session start failed:", session_resp.text)
        sys.exit(1)
    session_id = session_resp.json()["id"]

    uri = f"ws://localhost:8000/v1/ws/session/{session_id}/turn?token={token}"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"message": "hello"}))
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print("Received event:", data["event"])
                if data["event"] == "done":
                    break
    except Exception as e:
        print("WS error:", e)

asyncio.run(test())
