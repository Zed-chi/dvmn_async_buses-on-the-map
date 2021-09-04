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

class Frame:
    def __init__(self):
        self.data = None

    def get_data(self):
        return self.data
    
    def set_data(self, data):
        self.data = data


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
    frame = Frame()           
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(get_map_frame, ws, frame)
        nursery.start_soon(send_buses_data, ws, frame)


         

async def send_buses_data(ws, frame:Frame):
    while True:
        try:
            print("got client req")
            frame_data = frame.get_data()
            if frame_data != None:
                filtered_buses = filter(check_position(frame_data), BUSES.values())
                await ws.send_message(
                    json.dumps({"msgType": "Buses", "buses": list(filtered_buses)})
                )
            else:
                print("frame is none")
            await trio.sleep(2.5)
        except ConnectionClosed:
            break


def check_position(frame):
    def check(bus_data): 
        print(bus_data)
        lat =bus_data["lat"] 
        lng = bus_data["lng"]
        if lat < frame["north_lat"] and lat > frame["west_lng"] and\
            lng > frame["west_lng"] and lng < frame["east_lng"]:
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
        frame.set_data(
            {
                "east_lng": json_data["data"]["east_lng"],
                "north_lat": json_data["data"]["north_lat"],
                "south_lat": json_data["data"]["south_lat"],
                "west_lng": json_data["data"]["west_lng"],  
            }
        )
            


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
