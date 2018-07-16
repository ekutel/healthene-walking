import math
from app import app
from googlemaps import Client
from app.util import deprecated

from .classes import Point, WalkingRouteItem


class WalkingRoute:
    SHIFT_MAX = 360  # in degrees
    SHIFT_STEP = 45  # in degrees
    SHIFT_START = 0  # in degrees

    DEFAULT_DIRECTION_MODE = "walking"
    DEFAULT_DIRECTION_AVOID = ["highways", "tolls", "ferries"]

    CAST_TO_MILES = app.config['CAST_TO_MILES']
    CAST_TO_KM = 1000  #

    CORRELATION_FACTOR = 1
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

    def __init__(self, coordinates, distance, direction=None):
        self.coordinates = coordinates
        self.distance = distance
        self.direction = self.DIRECTIONS.get(direction.lower() if direction else self.DEFAULT_DIRECTION)
        self.radius = self.distance / (2 * math.pi) * self.CORRELATION_FACTOR

        self.gmaps = Client(app.config['GOOGLE_MAPS_API_KEY'])  # geoCoding
        self.dirs = Client(app.config['GOOGLE_MAPS_API_KEY'])  # directions

    @staticmethod
    def flatten(items):
        return [value for deep_list in items for value in deep_list]

    def load_point_data(self):
        coordinates = self.coordinates
        if hasattr(self, 'center_coordinates'):
            coordinates = self.center_coordinates
        points = self.__find_lap_points(coordinates)
        points_info = []
        for i, point in enumerate(points):
            if WalkingRoute.__is_last(points, point):
                points_info.append(self.__compute_direction(point, points[0]))
            else:
                points_info.append(self.__compute_direction(point, points[i + 1]))
        flattened = WalkingRoute.flatten(points_info)
        return WalkingRouteItem(flattened, WalkingRoute.__compute_overall_distance(flattened), self.coordinates)

    def load_for_map(self):
        return ",\n".join(
            ["{{lat: {lat}, lng: {lng}}}".format(lat=point.lat, lng=point.lng) for point in
             self.load_point_data().points])

    @staticmethod
    def _get_way_point(coordinates, shift, radius):
        # https://www.movable-type.co.uk/scripts/latlong.html - see here for more details
        """
        Formula:
            φ2 = asin( sin φ1 ⋅ cos δ + cos φ1 ⋅ sin δ ⋅ cos θ )
            λ2 = λ1 + atan2( sin θ ⋅ sin δ ⋅ cos φ1, cos δ − sin φ1 ⋅ sin φ2 )
                where φ is latitude, λ is longitude, θ is the bearing (clockwise from north), δ is the angular distance d/R; d being the distance travelled, R the earth’s radius
        """
        radius = radius / WalkingRoute.EARTH_RADIUS_KM
        shift = math.radians(shift)

        lat = math.radians(coordinates[0])  # get lat
        lng = math.radians(coordinates[1])  # get lng

        lat_shift = math.asin(
            math.sin(lat) * math.cos(radius) + math.cos(lat) * math.sin(radius) * math.cos(shift)
        )

        lng_shift = lng + math.atan2(
            math.sin(shift) * math.sin(radius) * math.cos(lat), math.cos(radius) - math.sin(lat) * math.sin(lat_shift)
        )
        if not isinstance(lat_shift, float) \
                or not isinstance(lng_shift, float):
            return False

        return [math.degrees(lat_shift), math.degrees(lng_shift)]

    def __find_lap_points(self, coordinates):
        points = []
        shift = self.SHIFT_START
        while shift <= self.SHIFT_MAX:
            new_way_point = self._get_way_point(coordinates, shift, self.radius)
            points.append(new_way_point)
            shift += self.SHIFT_STEP
        return points

    @staticmethod
    def __compute_overall_distance(points_info):
        return sum(float(point.distance) for point in points_info) / WalkingRoute.CAST_TO_KM

    @deprecated('This method was deprecated')
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

        return WalkingRoute.__go_round_points(route_info)

    @staticmethod
    def __go_round_points(way_points):
        points = []
        for way_point in way_points:
            for steps in way_point['legs'][0]['steps']:
                dp = Point(address=way_point['legs'][0]['start_address'], **steps)
                points.append(dp)
        return points


class WalkingRouteFromCurrentPosition(WalkingRoute):
    def __init__(self, coordinates, distance, direction):
        super(WalkingRouteFromCurrentPosition, self).__init__(coordinates, distance, direction)
        self.center_coordinates = self.__get_lap_center()  # complete new center for lap

    def __get_lap_center(self):
        return self._get_way_point(self.coordinates, self.direction, self.radius)
