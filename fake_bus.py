import itertools
import json
from sys import stderr
from typing import Dict

import trio
from trio_websocket import open_websocket_url

from load_routes import load_routes

URL = "ws://127.0.0.1:8080"


async def bus_status_gen(bus_json):
    for lat, long in itertools.cycle(bus_json["coordinates"]):
        yield {
            "busId": bus_json["name"],
            "lat": lat,
            "lng": long,
            "route": bus_json["name"],
        }
        await trio.sleep(5)


async def run_bus(url: str, bus_id: str, route: Dict):
    bus_status = bus_status_gen(route)
    while True:
        try:
            async with open_websocket_url(url) as ws:
                message = await bus_status.__anext__()
                await ws.send_message(json.dumps(message))
        except OSError as ose:
            print("Connection attempt failed: %s" % ose, file=stderr)


async def main():
    async with trio.open_nursery() as nursery:
        for route in load_routes():
            nursery.start_soon(run_bus, URL, route["name"], route)


trio.run(main)
