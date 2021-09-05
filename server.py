import json
from dataclasses import asdict, dataclass
import trio
from trio_websocket import ConnectionClosed, serve_websocket


@dataclass
class Bus:
    busId:str
    lat:float
    lng:float
    route:str


@dataclass
class WindowBounds:
    east_lng:float
    north_lat:float
    south_lat:float
    west_lng:float

class Frame:
    def __init__(self):
        self.bounds = None

    def get_bounds(self):
        return self.bounds
    
    def set_bounds(self, bounds:WindowBounds):
        self.bounds = bounds
    
    def is_inside(self, bus:Bus):
        lat = bus.lat
        lng = bus.lng
        if lat < self.bounds.north_lat and lat > self.bounds.south_lat and\
            lng > self.bounds.west_lng and lng < self.bounds.east_lng:
            return True
        else:
            return False


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
            BUSES[b_id] = Bus(**json_data)
            #BUSES[b_id] = Bus(**json_data)
            print(f"got {b_id}")
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    """
    Sends: buses json
    """ 
    frame = Frame()           
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(get_map_frame, ws, frame)
        nursery.start_soon(send_buses_data, ws, frame)


async def send_buses_data(ws, frame:Frame):
    while True:
        try:
            print("got client req")            
            if frame.get_bounds() != None:
                filtered_buses = filter(frame.is_inside, BUSES.values())

                await ws.send_message(
                    json.dumps({"msgType": "Buses", "buses": [asdict(bus) for bus in filtered_buses]})
                )
            else:
                print("frame is none")
            await trio.sleep(2.5)
        except ConnectionClosed:
            break


def check_position(bounds:WindowBounds):
    def check(bus_data:Bus):        
        lat = bus_data.lat
        lng = bus_data.lng
        if lat < bounds.north_lat and lat > bounds.south_lat and\
            lng > bounds.west_lng and lng < bounds.east_lng:
            return True
        else:
            return False
    return check


async def get_map_frame(ws, frame:Frame):
    while True:
        message = await ws.get_message()
        print("got frame")
        json_data = json.loads(message)
        if not "data" in json_data:
            continue
        frame.set_bounds(WindowBounds(**json_data["data"]))


async def sensors_connection():
    while True:
        try:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(
                    serve_websocket, echo_server, "127.0.0.1", 8080, None
                )                
        except Exception as e:
            print("sensors problem")
            await trio.sleep(2)


async def browser_connection():
    while True:
        try:
            async with trio.open_nursery() as nursery:                
                nursery.start_soon(
                    serve_websocket, talk_to_browser, "127.0.0.1", 8000, None
                )
        except ConnectionClosed:
            print("closed browser")
            await trio.sleep(2)


async def main():    
    async with trio.open_nursery() as nursery:
        nursery.start_soon(sensors_connection)
        nursery.start_soon(browser_connection)


trio.run(main)
