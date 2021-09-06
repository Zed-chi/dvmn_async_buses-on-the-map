import json
import logging
from dataclasses import asdict
from json.decoder import JSONDecodeError

import asyncclick as click
import trio
from trio_websocket import ConnectionClosed, serve_websocket

from utils import Bus, Frame, WindowBounds
from validators import get_validated_bus_data, get_validated_map_frame

BUSES = {}


async def start_bus_data_share(request):
    """
    Accepts: json with "busId","lat","lng","route"
    """
    ws = await request.accept()
    while True:
        try:
            bus_json = await ws.get_message()
            bus_dict = get_validated_bus_data(bus_json)
            if bus_dict is None:
                continue
            else:
                await ws.send_message("ok")
            bus_id = bus_dict["busId"]
            BUSES[bus_id] = Bus(**bus_dict)
            logging.info(f"got {bus_id}")
        except ValueError as e:
            logging.info(f"bus = {e}")
            await ws.send_message(
                json.dumps({"bus_error": str(e), "msgType": "Error"})
            )
        except JSONDecodeError:
            logging.info("Invalid JSON Data")
            await ws.send_message(
                '{"bus_error": "Invalid JSON Data", "msgType": "Error"}'
            )


async def start_browser_data_share(request):
    """
    Sends: buses json
    Receives: Browser Frame with coordinatess
    """
    frame = Frame()
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(get_map_frame, ws, frame)
        nursery.start_soon(send_buses_data, ws, frame)


async def send_buses_data(ws, frame: Frame):
    while True:
        logging.info("got browser request")
        if frame.get_bounds() is not None:
            filtered_buses = filter(frame.is_inside, BUSES.values())

            await ws.send_message(
                json.dumps(
                    {
                        "msgType": "Buses",
                        "buses": [asdict(bus) for bus in filtered_buses],
                    }
                )
            )
        else:
            logging.info("frame is empty")
        await trio.sleep(2.5)


async def get_map_frame(ws, frame: Frame):
    while True:
        try:
            frame_json = await ws.get_message()
            logging.info("got frame from browser")
            frame_dict = get_validated_map_frame(frame_json)
            if frame_dict is None or (not "data" in frame_dict):
                continue
            frame.update(WindowBounds(**frame_dict["data"]))
        except ValueError as e:
            logging.info(f"map = {e}")
            await ws.send_message(
                json.dumps({"frame_error": str(e), "msgType": "Error"})
            )
        except JSONDecodeError:
            logging.info("Invalid JSON Data")
            await ws.send_message(
                '{"frame_error": "Invalid JSON Data", "msgType": "Error"}'
            )


async def bus_connection(port):
    while True:
        try:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(
                    serve_websocket,
                    start_bus_data_share,
                    "127.0.0.1",
                    port,
                    None,
                )
        except ConnectionClosed:
            logging.info("sensors connection problem")


async def browser_connection(port):
    while True:
        try:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(
                    serve_websocket,
                    start_browser_data_share,
                    "127.0.0.1",
                    port,
                    None,
                )
        except ConnectionClosed:
            logging.info("closed browser")


async def main(bus_port: int, browser_port: int, v: bool):
    if v:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(bus_connection, bus_port)
        nursery.start_soon(browser_connection, browser_port)


@click.command()
@click.option("--bus_port", default=8080, help="порт для имитатора автобусов")
@click.option("--browser_port", default=8000, help=" порт для браузера")
@click.option("--v", default=False, help="настройка логирования")
def run(bus_port: int, browser_port: int, v: bool):
    trio.run(main, bus_port, browser_port, v)


if __name__ == "__main__":
    run()
