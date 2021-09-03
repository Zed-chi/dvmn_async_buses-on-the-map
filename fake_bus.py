import json
import trio
import itertools
from sys import stderr
from trio_websocket import open_websocket_url


route_data = {}

with open("./coords.json", "r", encoding="utf-8") as file:
    route_data = json.loads(file.read())

async def form_message():    
    for lat, long in  itertools.cycle(route_data["coordinates"]):        
        yield {
            "busId": "c790сс",
            "lat": lat,
            "lng": long,
            "route": "156"
        }
        await trio.sleep(2.5)

async def main():
    data = form_message()
    while True:
        try:
            async with open_websocket_url('ws://127.0.0.1:8080') as ws:
                message = await data.__anext__()
                await ws.send_message(
                    json.dumps(message)
                )            
        except OSError as ose:
            print('Connection attempt failed: %s' % ose, file=stderr)

trio.run(main)