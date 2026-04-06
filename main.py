from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import websockets

app = FastAPI()

# ✅ Mount static files on /static, not /
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

clients = set()
latest_frame = None


# 🔌 Connect to your C WebSocket server
async def streamer_client():
    global latest_frame
    uri = "ws://localhost:9000"

    while True:
        try:
            async with websockets.connect(uri) as ws:
                print("Connected to C streamer")

                async for message in ws:
                    latest_frame = message

                    # broadcast to all connected browsers
                    dead_clients = []
                    for client in clients:
                        try:
                            await client.send_bytes(message)
                        except:
                            dead_clients.append(client)

                    # cleanup disconnected clients
                    for dc in dead_clients:
                        clients.remove(dc)

        except Exception as e:
            print("Reconnect in 2s:", e)
            await asyncio.sleep(2)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(streamer_client())


# 🌐 WebSocket endpoint for browsers
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)

    # send last frame immediately for new clients
    if latest_frame:
        await ws.send_bytes(latest_frame)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        clients.remove(ws)


# ✅ Serve index.html at root
@app.get("/")
def home():
    return FileResponse("static/index.html")