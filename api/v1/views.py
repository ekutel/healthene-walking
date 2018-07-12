from flask_jwt import jwt_required
from flask_restful import Resource


class BNResource(Resource):
    """
    Override system Resource settings
    """
    decorators = [jwt_required()]


class Login(Resource):
    def post(self):
        return {'message': 'login action'}


class TokenRefresh(BNResource):
    def post(self):
        return {'message': 'refresh token'}

