import json

import trio
from trio_websocket import ConnectionClosed, serve_websocket

"""
To Frontend=>
{
  "msgType": "Buses",
  "buses": [
    {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
    {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
  ]
}
"""

"""
From frontend=>
{
  "msgType": "newBounds",
  "data": {
    "east_lng": 37.65563964843751,
    "north_lat": 55.77367652953477,
    "south_lat": 55.72628839374007,
    "west_lng": 37.54440307617188,
  },
}
"""
BUSES = {}


async def echo_server(request):
    """
    Accepts: json with "busId","lat","lng","route"
    """
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            json_data = json.loads(message)
            b_id = json_data["busId"]
            BUSES[b_id] = json_data
            print(f"got {b_id}")
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    """
    Sends: buses json
    """
    ws = await request.accept()
    while True:
        try:
            print("got client req")
            await ws.send_message(
                json.dumps({"msgType": "Buses", "buses": list(BUSES.values())})
            )
            await trio.sleep(2.5)
        except ConnectionClosed:
            break


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, echo_server, "127.0.0.1", 8080, None
        )
        nursery.start_soon(
            serve_websocket, talk_to_browser, "127.0.0.1", 8000, None
        )


trio.run(main)
