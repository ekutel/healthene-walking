from app import app
from walking.route import WalkingRoute, WalkingRouteFromCurrentPosition
from walking.classes import WalkingItemEncoder
from flask import render_template, json, request
from flask import Blueprint

api = Blueprint('api', __name__)


@api.route('/test')
def test():
    route = WalkingRouteFromCurrentPosition([32.8205862,-96.8719689], 20, 'west')
    context = {
        "key": app.config['GOOGLE_MAPS_API_KEY'],
    }
    return render_template('template.html', map=route.load_for_map(), context=context)


@api.route('/routes', methods=["POST"])
def walking():
    data = json.loads(request.data)
    route = WalkingRouteFromCurrentPosition([data.get('lat'), data.get('lng')], data.get('distance'),
                                            data.get('direction', None))
    return json.dumps(route.load_point_data(), cls=WalkingItemEncoder), 200, {'content-type': 'application/json'}
