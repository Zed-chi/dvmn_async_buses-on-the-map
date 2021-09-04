import itertools
import json
from sys import stderr
from typing import Dict
from random import randint

import trio
from trio_websocket import open_websocket_url

from load_routes import load_routes

URL = "ws://127.0.0.1:8080"
BUSES_ON_ROUTE = 5

async def bus_status_gen(bus_json):
    for lat, long in itertools.cycle(bus_json["coordinates"]):
        yield {
            "busId": bus_json["name"],
            "lat": lat,
            "lng": long,
            "route": bus_json["name"],
        }
        await trio.sleep(5)

def cycle(arr, start_id=0):
    counter = start_id
    while True:
        if counter == len(arr)-1:
            value = arr[counter]
            counter = 0
        else:
            value = arr[counter]
            counter += 1

        yield value


async def bus_status_gen2(bus_json):
    buses_start_positions = list(
        range(0, len(bus_json["coordinates"]),
            len(bus_json["coordinates"]) // BUSES_ON_ROUTE)
    )
    bus_names = [f"{bus_json['name']}{randint(0,10000)}" for _ in range(BUSES_ON_ROUTE)]
    bus_positions_gens = [
        cycle(bus_json["coordinates"],start) for start in buses_start_positions
    ]
    while True:
        for i in range(BUSES_ON_ROUTE):
            position = next(bus_positions_gens[i])
            yield {
                "busId": bus_names[i],
                "lat": position[0],
                "lng": position[1],
                "route": bus_json["name"],
            }
            await trio.sleep(2)

async def run_bus(url: str, bus_id: str, route: Dict):
    #bus_status = bus_status_gen(route)
    bus_status = bus_status_gen2(route)
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
