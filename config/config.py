# -*- coding: utf-8 -*-

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'SECRET_KEY')
    APPLICATION_ROOT = '/app'
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', None)
    CAST_TO_MILES = 0.621371192
    BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', "whitesalt")
    BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', "123qazWSX")
    BASIC_AUTH_FORCE = True


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


def load_config():
    from distutils.util import strtobool
    # prepare load config
    if strtobool(os.getenv('FLASK_DEBUG', 'false')):
        return DevelopmentConfig
    elif strtobool(os.getenv('FLASK_TEST', 'false')):
        return TestingConfig
    else:
        return ProductionConfig
