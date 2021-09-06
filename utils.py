from dataclasses import dataclass
from itertools import cycle
import trio

@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


@dataclass
class WindowBounds:
    east_lng: float
    north_lat: float
    south_lat: float
    west_lng: float


class Frame:
    def __init__(self):
        self.bounds = None

    def get_bounds(self):
        return self.bounds

    def update(self, bounds: WindowBounds):
        self.bounds = bounds

    def is_inside(self, bus: Bus):
        lat = bus.lat
        lng = bus.lng
        return (lat < self.bounds.north_lat\
            and lat > self.bounds.south_lat\
            and lng > self.bounds.west_lng\
            and lng < self.bounds.east_lng)        


class Channels_container():
    def __init__(self, num) -> None:
        self.receive_channels = []
        self.send_channels = []
        for _ in range(num):
            s, r = trio.open_memory_channel(0)
            self.receive_channels.append(r)
            self.send_channels.append(s)
        self.send_gen = self.channel_generator(self.send_channels)
        self.recv_gen = self.channel_generator(self.receive_channels)
    
    def channel_generator(self, channels):
        for channel in cycle(channels):
            yield channel
    
    def get_receive_channel(self):
        return next(self.recv_gen)
    
    def get_send_channel(self):
        return next(self.send_gen)
