import json


def get_validated_map_frame(text):
    json_data = json.loads(text)
    for key in ["msgType", "data"]:
        if key not in json_data:
            raise ValueError(f"{key} is missing")
    if json_data["msgType"] != "newBounds":
        raise ValueError("Wrong msg type")
    if not type(json_data["data"]) == dict:
        raise ValueError("'data' value type error")
    else:
        for k, v in json_data["data"].items():
            if k not in ["east_lng", "north_lat", "south_lat", "west_lng"]:
                raise ValueError("Invalid key in json[data]")
            if type(v) != float:
                raise ValueError("Invalid position type")
    return json_data


def get_validated_bus_data(text):
    json_data = json.loads(text)
    for key in [
        "busId",
        "lat",
        "lng",
        "route",
    ]:
        if key not in json_data:
            raise ValueError(f"{key} is missing")
    if type(json_data["busId"]) != str:
        raise ValueError("busId type error")
    if type(json_data["lat"]) != float:
        raise ValueError("lat type error")
    if type(json_data["lng"]) != float:
        raise ValueError("lng type error")
    if type(json_data["route"]) != str:
        raise ValueError("route type error")
    return json_data
