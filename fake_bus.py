import json
import logging
from itertools import cycle
from math import ceil
from random import randint
from sys import stderr
from typing import Iterable
import async_generator

import asyncclick as click
import trio
from trio_websocket import open_websocket_url
from trio_websocket._impl import ConnectionClosed, HandshakeError
from load_routes import load_routes
from utils import Channels_container

RECONNECT_INTERVAL = 5


def make_bus_name(route_id, emulator_id):
    emu_part = "-" + emulator_id if emulator_id else ""
    num_part = "-" + str(randint(0, 10000))
    (route_id, emu_part, num_part)
    return f"{route_id}{emu_part}{num_part}"


def coordinates_generator(coordinates: Iterable, start_id: int = 0):
    coordinates = coordinates[start_id:] + coordinates[:start_id]
    for item in cycle(coordinates):
        yield item


def get_start_ids_in_range(coordinates, bus_num):
    length = len(coordinates)
    step = max(1, length // bus_num)

    ids = list(range(0, length, step))
    if bus_num > length:
        ids = ids * (ceil(bus_num / length))
    return ids[:bus_num]


async def get_bus_info_generator(
    refresh_timeout, position_generator, name, route_id
):
    while True:
        position = next(position_generator)
        yield {
            "busId": name,
            "lat": position[0],
            "lng": position[1],
            "route": route_id,
        }
        await trio.sleep(refresh_timeout)


def get_bus_info_generator_list(
    refresh_timeout,
    emulator_id,
    buses_per_route,
    bus_info_dict,
):
    buses_start_positions = get_start_ids_in_range(
        bus_info_dict["coordinates"],
        buses_per_route,
    )

    bus_names = [
        make_bus_name(bus_info_dict["name"], emulator_id)
        for _ in range(buses_per_route)
    ]

    bus_position_generators = [
        coordinates_generator(bus_info_dict["coordinates"], start)
        for start in buses_start_positions
    ]

    return [
        get_bus_info_generator(
            refresh_timeout,
            bus_position_generators[i],
            bus_names[i],
            bus_info_dict["name"],
        )
        for i in range(buses_per_route)
    ]


async def run_bus(send_channel, bus_info: async_generator):
    while True:
        try:
            message = await bus_info.__anext__()
            await send_channel.send(message)
        except OSError as ose:
            logging.info(f"Connection attempt failed: {ose}")


async def send_data_to_server(ws, receive_channel):
    async for value in receive_channel:
        await ws.send_message(json.dumps(value))


async def start_server_data_share(url, receive_channel):
    while True:
        try:
            async with open_websocket_url(url) as ws:
                logging.info("connected to server")
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(
                        send_data_to_server, ws, receive_channel
                    )
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

    channels_container = Channels_container(websockets_number)
    async with trio.open_nursery() as nursery:

        for _ in range(websockets_number):
            nursery.start_soon(
                start_server_data_share,
                ("ws://" + server),
                channels_container.get_receive_channel(),
            )

        for route in routes:
            bus_info_gen_list = get_bus_info_generator_list(
                refresh_timeout, emulator_id, buses_per_route, route
            )
            for bus_info_gen in bus_info_gen_list:
                nursery.start_soon(
                    run_bus,
                    channels_container.get_send_channel(),
                    bus_info_gen,
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
