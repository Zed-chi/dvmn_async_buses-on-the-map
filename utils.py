from dataclasses import dataclass


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