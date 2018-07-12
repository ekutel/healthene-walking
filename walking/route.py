import math
from app import app
from flask import json
from googlemaps import Client


class WalkingRoute:
    SHIFT_MAX = 360  # in degrees
    SHIFT_STEP = 45  # in degrees
    SHIFT_START = 0  # in degrees

    DEFAULT_DIRECTION_MODE = "walking"
    DEFAULT_DIRECTION_AVOID = ["highways", "tolls", "ferries"]

    CAST_TO_MILES = 0.621371192  #
    CAST_TO_KM = 1000  #

    CORRELATION_FACTOR = 0.5
    EARTH_RADIUS_KM = 6371

    CENTER = 360
    NORTH = 0
    NORTHEAST = 45
    EAST = 90
    SOUTHEAST = 135
    SOUTH = 180
    SOUTHWEST = 225
    WEST = 270
    NORTHWEST = 215

    DIRECTIONS = {
        'center': CENTER,
        'north': NORTH,
        'northeast': NORTHEAST,
        'east': EAST,
        'southeast': SOUTHEAST,
        'south': SOUTH,
        'southwest': SOUTHWEST,
        'west': WEST,
        'northwest': NORTHWEST,
    }

    DEFAULT_DIRECTION = 'center'

    def __init__(self, coordinates, distance, direction=DEFAULT_DIRECTION):
        self.coordinates = coordinates
        self.distance = distance
        self.direction = self.DIRECTIONS.get(direction.lower())
        self.radius = self.distance / (2 * math.pi) * self.CORRELATION_FACTOR

        self.gmaps = Client(app.config['GOOGLE_MAPS_API_KEY'])  # geoCoding
        self.dirs = Client(app.config['GOOGLE_MAPS_API_KEY'])  # directions

    # https://www.movable-type.co.uk/scripts/latlong.html - see here for more details
    """
    Formula: 
        φ2 = asin( sin φ1 ⋅ cos δ + cos φ1 ⋅ sin δ ⋅ cos θ ) 
        λ2 = λ1 + atan2( sin θ ⋅ sin δ ⋅ cos φ1, cos δ − sin φ1 ⋅ sin φ2 ) 
            where φ is latitude, λ is longitude, θ is the bearing (clockwise from north), δ is the angular distance d/R; d being the distance travelled, R the earth’s radius
    """

    def load_point_data(self):
        points = self.__find_lap_points()
        points_info = []
        for i, point in enumerate(points):
            if WalkingRoute.__is_last(points, point):
                points_info.append(self.__compute_direction(point, points[0]))
            else:
                points_info.append(self.__compute_direction(point, points[i + 1]))

        return WalkingRouteItem(points_info, WalkingRoute.__compute_overall_distance(points_info), self.coordinates)

    def load_for_map(self):
        return ",\n".join(
            ["{{lat: {lat}, lng: {lng}}}".format(lat=point.lat, lng=point.lng) for point in
             self.load_point_data().points])

    @staticmethod
    def __get_way_point(coordinates, shift, dist):
        dist = dist / WalkingRoute.EARTH_RADIUS_KM
        shift = math.radians(shift)

        lat = math.radians(coordinates[0])  # get lat
        lng = math.radians(coordinates[1])  # get lng

        lat_shift = math.asin(
            math.sin(lat) * math.cos(dist) + math.cos(lat) * math.sin(dist) * math.cos(shift)
        )

        lng_shift = lng + math.atan2(
            math.sin(shift) * math.sin(dist) * math.cos(lat), math.cos(dist) - math.sin(lat) * math.sin(lat_shift)
        )
        if not isinstance(lat_shift, float) \
                or not isinstance(lng_shift, float):
            return False

        return [math.degrees(lat_shift), math.degrees(lng_shift)]

    def __find_lap_points(self):
        points = []
        shift = self.SHIFT_START
        while shift <= self.SHIFT_MAX:
            new_way_point = self.__get_way_point(self.coordinates, shift, self.radius)
            points.append(new_way_point)
            shift += self.SHIFT_STEP
        return points

    @staticmethod
    def __compute_overall_distance(points_info):
        return sum(float(point.distance) for point in points_info) / WalkingRoute.CAST_TO_KM

    def __overall_to_miles(self, points):
        return WalkingRoute.__compute_overall_distance(points) * self.CAST_TO_MILES

    @staticmethod
    def __is_last(existing_list, current):
        return existing_list[-1] == current

    def __compute_direction(self, start, end):
        """
        Load information from Google Maps Directions for each route point
        :param start:
        :param end:
        :return:
        """
        route_info = self.dirs.directions(start, end, mode=self.DEFAULT_DIRECTION_MODE,
                                          avoid=self.DEFAULT_DIRECTION_AVOID)
        dp = Point(
            lat=start[0],
            lng=start[1],
            street=route_info[0]['legs'][0]['start_address'],
            distance=route_info[0]['legs'][0]['distance']['value'],
        )
        return dp


class WalkingRouteFromCurrentPosition(WalkingRoute):

    def __find_lap_points(self):
        lap_center = self.__get_lap_center()
        points = []
        shift = self.SHIFT_START
        while shift <= self.SHIFT_MAX:
            new_way_point = self.__get_way_point(lap_center, shift, self.radius)
            points.append(new_way_point)
            shift += self.SHIFT_STEP
        return points

    def __get_lap_center(self):
        return self.__get_way_point(self.coordinates, self.direction, self.radius)


# Data object classes

class WalkingRouteItem:
    def __init__(self, point=None, distance=None, current_position=None):
        """
        Data object for route information
        :param point:
        :param distance:
        :param current_position:
        """
        self.points = point
        self.distance = distance
        self.current_position = current_position

    def __iter__(self):
        return self


class Point:
    def __init__(self, lat=None, lng=None, street=None, distance=None):
        """
        Data object for route point
        :param lat:
        :param lng:
        :param street:
        :param distance:
        """
        self.lat = lat
        self.lng = lng
        self.street = street
        self.distance = distance

    def __repr__(self):
        return '{} {} {} {}'.format(self.lat, self.lng, self.street, self.distance)

    def __iter__(self):
        return self.distance


class WalkingItemEncoder(json.JSONEncoder):
    def default(self, obj):
        """Serialize Walking objects to json
               """
        if isinstance(obj, WalkingRouteItem):
            return obj.__dict__
        if isinstance(obj, Point):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)
