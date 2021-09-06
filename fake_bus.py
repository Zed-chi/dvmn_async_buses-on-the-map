import json
import logging
from random import randint
from sys import stderr
from typing import Iterable

import asyncclick as click
import trio
from trio_websocket import open_websocket_url
from trio_websocket._impl import ConnectionClosed, HandshakeError

from load_routes import load_routes

RECONNECT_INTERVAL = 5


def cycle(arr: Iterable, start_id: int = 0):
    counter = start_id
    while True:
        if counter == len(arr) - 1:
            value = arr[counter]
            counter = 0
        else:
            value = arr[counter]
            counter += 1

        yield value


def get_positions_in_range(coordinates, bus_num):
    step = max(1, len(coordinates) // bus_num)
    length = len(coordinates)
    return range(0, length, step)


async def bus_info_generator(
    refresh_timeout,
    emulator_id,
    buses_per_route,
    bus_info_dict,
):
    buses_start_positions = get_positions_in_range(
        bus_info_dict["coordinates"],
        buses_per_route,
    )

    bus_names = [
        f"{bus_info_dict['name']}{'-'+str(emulator_id) if emulator_id else ''}{'-'+str(randint(0,10000))}"
        for _ in range(buses_per_route)
    ]
    bus_position_generators = [
        cycle(bus_info_dict["coordinates"], start)
        for start in buses_start_positions
    ]

    while True:
        for idx in range(buses_per_route):
            position = next(bus_position_generators[idx])
            yield {
                "busId": bus_names[idx],
                "lat": position[0],
                "lng": position[1],
                "route": bus_info_dict["name"],
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
    bus_info = bus_info_generator(
        refresh_timeout,
        emulator_id,
        buses_per_route,
        route,
    )
    while True:
        try:
            message = await bus_info.__anext__()
            await send_channel.send(message)
        except OSError as ose:
            logging.info("Connection attempt failed: %s" % ose, file=stderr)


async def send_data_to_server(ws, receive_channel):
    async for value in receive_channel:
        await ws.send_message(json.dumps(value))


async def send_to_server(url, receive_channel):
    while True:
        try:
            async with open_websocket_url(url) as ws:
                logging.info("connected to server")
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(send_data_to_server, ws, receive_channel)
                    nursery.start_soon(get_response_messages, ws)  
        except OSError as ose:
            logging.info("Connection attempt failed: %s" % ose, file=stderr)
        except (HandshakeError, ConnectionClosed) as e:
            logging.info(e)
            logging.info("waiting")
            await trio.sleep(RECONNECT_INTERVAL)
            logging.info("trying to reconnect to server")


async def get_response_messages(ws):             
    while True:
        message = await ws.get_message()
        logging.debug(message)    


async def main(
    server,
    routes_number,
    buses_per_route,
    websockets_number,
    emulator_id,
    refresh_timeout,
    v,
):
    if v:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)

    routes = list(load_routes())
    if routes_number < len(routes) and routes_number != 0:
        routes = routes[:routes_number]

    async with trio.open_nursery() as nursery:
        send_channel, receive_channel = trio.open_memory_channel(0)
        for _ in range(websockets_number):
            nursery.start_soon(
                send_to_server,
                ("ws://" + server),
                receive_channel,
        )

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


@click.command()
@click.option("--server", default="127.0.0.1:8080", help="адрес сервера")
@click.option("--routes_number", default=10, help="количество маршрутов")
@click.option(
    "--buses_per_route",
    default=5,
    help="количество автобусов на каждом маршруте",
)
@click.option(
    "--websockets_number",
    default=1,
    help="количество открытых веб-сокетов",
)
@click.option(
    "--emulator_id",
    default="",
    help="префикс к busId на случай запуска нескольких экземпляров имитатора",
)
@click.option(
    "--refresh_timeout",
    default=1,
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
