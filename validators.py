import json


def get_validated_map_frame(frame_json):
    frame_dict = json.loads(frame_json)
    for key in ["msgType", "data"]:
        if key not in frame_dict:
            raise ValueError(f"{key} is missing")

    if frame_dict["msgType"] != "newBounds":
        raise ValueError("Wrong msg type")

    if not isinstance(frame_dict["data"], dict):
        raise ValueError("'data' value type error")
    else:
        for key, value in frame_dict["data"].items():
            if key not in ["east_lng", "north_lat", "south_lat", "west_lng"]:
                raise ValueError("Invalid key in json[data]")
                
            if not isinstance(value, float):
                raise ValueError("Invalid position type")

    return frame_dict


def get_validated_bus_data(bus_json):
    bus_dict = json.loads(bus_json)
    for key in [
        "busId",
        "lat",
        "lng",
        "route",
    ]:
        if key not in bus_dict:
            raise ValueError(f"{key} is missing")

    if not isinstance(bus_dict["busId"], str):
        raise ValueError("busId type error")

    if not isinstance(bus_dict["lat"], float):
        raise ValueError("lat type error")

    if not isinstance(bus_dict["lng"], float):
        raise ValueError("lng type error")

    if not isinstance(bus_dict["route"], str):
        raise ValueError("route type error")

    return bus_dict
