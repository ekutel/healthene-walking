# Data object classes
import json
from app import app


class WalkingRouteItem:
    CAST_TO_MILES = app.config['CAST_TO_MILES']

    def __init__(self, point=None, distance_km=None, current_position=None):
        """
        Data object for route information
        :param point: Point object
        :param distance_km: Overall distance (km)
        :output distance_miles: Overall distance (miles)
        :param current_position: Received current position
        """
        self.points = point
        self.distance_km = distance_km
        self.distance_miles = self._distance_miles
        self.current_position = current_position

    def __iter__(self):
        return self

    @property
    def _distance_miles(self):
        return self.distance_km * self.CAST_TO_MILES


class Point(object):
    def __init__(self, start_location=None, address=None, distance=None, **kwargs):
        """
        Data object for route point
        :param lat:
        :param lng:
        :param street:
        :param distance:
        """
        self.lat = kwargs.get('lat') if 'lat' in kwargs else start_location.get('lat')
        self.lng = kwargs.get('lng') if 'lng' in kwargs else start_location.get('lng')
        self.street = kwargs.get('street') if 'street' in kwargs else address
        self.distance = distance.get('value', 0) if isinstance(distance, dict) else distance

    def __repr__(self):
        return 'Coordinates: [{lat}, {lng}], Address: {street}, Distance: {distance}'.format(lat=self.lat, lng=self.lng,
                                                                                             street=self.street,
                                                                                             distance=self.distance)

    def __iter__(self):
        return self


class WalkingItemEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        Serialize Walking objects to json
        """
        if isinstance(obj, WalkingRouteItem):
            return obj.__dict__
        if isinstance(obj, Point):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)
