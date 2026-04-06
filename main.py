from fastapi import FastAPI, WebSocket
import asyncio
import websockets

app = FastAPI()

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

                    for dc in dead_clients:
                        clients.remove(dc)

        except Exception as e:
            print("Reconnect in 2s:", e)
            await asyncio.sleep(2)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(streamer_client())


# 🌐 Browser WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        clients.remove(ws)