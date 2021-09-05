import json

import trio
from trio_websocket import open_websocket_url


async def frame():
    try:
        async with open_websocket_url("ws://127.0.0.1:8000") as ws:
            await ws.send_message("hello world!")
            print("done")
            message = await ws.get_message()
            print(message)
    except OSError as ose:
        print("Connection attempt failed: %s", ose)


async def position():
    try:
        async with open_websocket_url("ws://127.0.0.1:8080") as ws:
            invalid_json = {
                "info": "test",
                "busId": "123",
                "lat": 123.123,
                "lng": 789.123,
                "route": "123",
            }
            await ws.send_message(json.dumps(invalid_json))
            print("done")
            message = await ws.get_message()
            print(message)
    except OSError as ose:
        print("Connection attempt failed: %s", ose)


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(frame)
        nursery.start_soon(position)


trio.run(main)
