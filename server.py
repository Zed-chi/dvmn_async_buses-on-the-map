from typing import Dict
import trio
import itertools
import asyncio
import json
from trio_websocket import serve_websocket, ConnectionClosed

route_data:Dict = {}

with open("./coords.json", "r", encoding="utf-8") as file:
    route_data = json.loads(file.read())



async def form_message():    
    for lat, long in  itertools.cycle(route_data["coordinates"]):        
        yield {
            "msgType": "Buses",
            "buses": [
                {"busId": "test", "lat": lat, "lng":long, "route": "156"},
            ]
        }
        await trio.sleep(2.5)



async def echo_server(request):
    
    ws = await request.accept()
    c = form_message()
    while True:
        try:            
            out_message = await c.__anext__()
            print(out_message)
            await ws.send_message(json.dumps(out_message))            
        except ConnectionClosed:
            break
        
async def main():
    await serve_websocket(echo_server, '127.0.0.1', 8000, ssl_context=None)


trio.run(main)