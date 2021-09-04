import itertools
import json
from random import randint
from sys import stderr
from typing import Dict

import trio
from trio_websocket import open_websocket_url

from load_routes import load_routes

URL = "ws://127.0.0.1:8080"
BUSES_ON_ROUTE = 15
INTERVAL_TIME = 5


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
        if counter == len(arr) - 1:
            value = arr[counter]
            counter = 0
        else:
            value = arr[counter]
            counter += 1

        yield value


async def bus_status_gen2(bus_json)-> Dict:
    buses_start_positions = list(
        range(
            0,
            len(bus_json["coordinates"]),
            len(bus_json["coordinates"]) // BUSES_ON_ROUTE,
        ),
    )
    bus_names = [
        f"{bus_json['name']}{randint(0,10000)}" for _ in range(BUSES_ON_ROUTE)
    ]
    bus_positions_gens = [
        cycle(bus_json["coordinates"], start)
        for start in buses_start_positions
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
            await trio.sleep(randint(1,INTERVAL_TIME))


async def run_bus(send_channel, name, route: Dict):    
    bus_status = bus_status_gen2(route)
    while True:
        try:            
            message = await bus_status.__anext__()
            await send_channel.send(message)
        except OSError as ose:
            print("Connection attempt failed: %s" % ose, file=stderr)


async def send_to_server(url, receive_channel):
    async with open_websocket_url(url) as ws:
        while True:
            try:
                async for value in receive_channel:
                    await ws.send_message(json.dumps(value))
            except OSError as ose:
                print("Connection attempt failed: %s" % ose, file=stderr)


async def main():   
    async with trio.open_nursery() as nursery:
        send_channel, receive_channel = trio.open_memory_channel(0)

        for route in load_routes():
            nursery.start_soon(run_bus, send_channel, route["name"], route)
        
        nursery.start_soon(send_to_server, URL, receive_channel)       


trio.run(main)
