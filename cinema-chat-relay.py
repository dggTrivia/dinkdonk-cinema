"""Read-only public DGG chat relay for the local cinema pages (aiohttp)."""
import asyncio
import contextlib
import json
from aiohttp import ClientSession, ClientTimeout, WSMsgType, web

clients = {}
users = {}
connected = False
received = 0


async def health(request):
    return web.json_response({"service": "cinema-chat-relay", "connected": connected,
                              "clients": len(clients), "frames": received})


async def socket(request):
    if not connected:
        raise web.HTTPServiceUnavailable(text="DGG chat reconnecting")
    ws = web.WebSocketResponse(heartbeat=25, max_msg_size=4096)
    await ws.prepare(request)
    queue = asyncio.Queue(maxsize=128)
    clients[ws] = queue
    await ws.send_str("NAMES " + json.dumps({"connectioncount": len(users), "users": list(users.values())}))

    async def send():
        try:
            while True:
                await asyncio.wait_for(ws.send_str(await queue.get()), timeout=5)
        except (TimeoutError, ConnectionError, RuntimeError):
            await ws.close()

    sender = asyncio.create_task(send())
    try:
        async for _ in ws:
            pass  # Browser messages are never forwarded upstream.
    finally:
        clients.pop(ws, None)
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender
    return ws


async def upstream():
    global connected, received
    delay = 1
    async with ClientSession(timeout=ClientTimeout(total=None, sock_connect=15)) as session:
        while True:
            try:
                async with session.ws_connect("wss://chat.destiny.gg/ws", origin="https://www.destiny.gg",
                                              heartbeat=25, receive_timeout=180) as ws:
                    connected = True
                    delay = 1
                    print("DGG public chat connected", flush=True)
                    async for message in ws:
                        if message.type != WSMsgType.TEXT:
                            continue
                        received += 1
                        text = message.data
                        kind, _, payload = text.partition(" ")
                        if kind in ("NAMES", "JOIN", "QUIT"):
                            try:
                                data = json.loads(payload)
                                if kind == "NAMES":
                                    users.clear()
                                    users.update((u["nick"], u) for u in data.get("users", []) if "nick" in u)
                                elif kind == "JOIN" and data.get("nick"):
                                    users[data["nick"]] = data
                                elif kind == "QUIT":
                                    users.pop(data.get("nick"), None)
                            except (ValueError, TypeError, KeyError):
                                pass
                        for client, queue in list(clients.items()):
                            if queue.full():
                                await client.close(code=1013, message=b"Slow client; reconnect")
                            else:
                                queue.put_nowait(text)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                print(f"DGG reconnecting: {type(error).__name__}", flush=True)
            finally:
                connected = False
                users.clear()
                await asyncio.gather(*(c.close(code=1013, message=b"DGG reconnecting")
                                       for c in list(clients)), return_exceptions=True)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)


async def lifecycle(app):
    task = asyncio.create_task(upstream())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = web.Application()
app.router.add_get("/healthz", health)
app.router.add_get("/__dgg_chat_ws", socket)
app.cleanup_ctx.append(lifecycle)
if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=18765, access_log=None)
