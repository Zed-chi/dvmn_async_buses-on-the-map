import itertools
import json
from random import choice, randint
from sys import stderr
from typing import Dict

import asyncclick as click
# import click
import trio
from trio_websocket import open_websocket_url
from trio_websocket._impl import ConnectionClosed, HandshakeError

from load_routes import load_routes

URL = "127.0.0.1:8080"
BUSES_ON_ROUTE = 5
INTERVAL_TIME = 1


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


async def bus_status_gen2(
    refresh_timeout, emulator_id, buses_per_route, route_json
) -> Dict:
    buses_start_positions = list(
        range(
            0,
            len(route_json["coordinates"]),
            len(route_json["coordinates"]) // buses_per_route,
        ),
    )
    bus_names = [
        f"{route_json['name']}{'-'+str(emulator_id)}{'-'+str(randint(0,10000))}"
        for _ in range(buses_per_route)
    ]
    bus_positions_gens = [
        cycle(route_json["coordinates"], start)
        for start in buses_start_positions
    ]
    while True:
        for i in range(buses_per_route):
            position = next(bus_positions_gens[i])
            yield {
                "busId": bus_names[i],
                "lat": position[0],
                "lng": position[1],
                "route": route_json["name"],
            }
            await trio.sleep(refresh_timeout)


async def run_bus(
    send_channel,
    emulator_id,
    refresh_timeout,
    buses_per_route,
    name,
    route,
):
    bus_status = bus_status_gen2(
        refresh_timeout, emulator_id, buses_per_route, route
    )
    while True:
        try:
            message = await bus_status.__anext__()
            await send_channel.send(message)

        except OSError as ose:
            print("Connection attempt failed: %s" % ose, file=stderr)


async def send_to_server(url, receive_channel):
    while True:
        try:
            async with open_websocket_url(url) as ws:
                print("connected")
                async for value in receive_channel:
                    await ws.send_message(json.dumps(value))

        except OSError as ose:
            print("Connection attempt failed: %s" % ose, file=stderr)
        except (HandshakeError, ConnectionClosed) as e:

            print("waiting")
            await trio.sleep(5)


async def main(
    server,
    routes_number,
    buses_per_route,
    websockets_number,
    emulator_id,
    refresh_timeout,
    v,
):
    routes = list(load_routes())
    if routes_number < len(routes) and routes_number != 0:
        routes = routes[:routes_number]

    async with trio.open_nursery() as nursery:
        send_channel, receive_channel = trio.open_memory_channel(0)

        for route in routes:
            nursery.start_soon(
                run_bus,
                send_channel,
                emulator_id,
                refresh_timeout,
                buses_per_route,
                route["name"],
                route,
            )

        for i in range(websockets_number):
            nursery.start_soon(
                send_to_server, ("ws://" + server), receive_channel
            )


@click.command()
@click.option("--server", default=URL, help="адрес сервера")
@click.option("--routes_number", default=10, help="количество маршрутов")
@click.option(
    "--buses_per_route",
    default=BUSES_ON_ROUTE,
    help="количество автобусов на каждом маршруте",
)
@click.option(
    "--websockets_number", default=1, help="количество открытых веб-сокетов"
)
@click.option(
    "--emulator_id",
    default="",
    help="префикс к busId на случай запуска нескольких экземпляров имитатора",
)
@click.option(
    "--refresh_timeout",
    default=INTERVAL_TIME,
    help="задержка в обновлении координат сервера",
)
@click.option("--v", default=False, help="настройка логирования")
def run(
    server,
    routes_number,
    buses_per_route,
    websockets_number,
    emulator_id,
    refresh_timeout,
    v,
):
    trio.run(
        main,
        server,
        routes_number,
        buses_per_route,
        websockets_number,
        emulator_id,
        refresh_timeout,
        v,
    )


if __name__ == "__main__":
    run()


# todo loggging
