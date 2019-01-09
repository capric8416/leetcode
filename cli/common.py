# !/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import logging
import os
import sys

import requests
import yaml

__all__ = (
    'PKG_NAME', 'PKG_PATH', 'CONF_DIR', 'DATA_DIR',
    'AccountConf', 'PullConf', 'PushConf', 'QueryConf',
    'Singleton', 'Session', 'logger'
)

# package path
PKG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# package name
PKG_NAME = PKG_PATH.rpartition('/')[-1]

# conf dir: ~/.package_name/conf, package_path/.conf
CONF_DIR = os.path.expanduser(f'~/.{PKG_NAME}/conf')
if not os.path.exists(CONF_DIR):
    CONF_DIR = f'{PKG_PATH}/.conf'

# data dir: ~/.package_name/data, package_path/.data
DATA_DIR = os.path.expanduser(f'~/.{PKG_NAME}/data')
if not os.path.exists(DATA_DIR):
    DATA_DIR = f'{PKG_PATH}/.data'


class Singleton(type):
    def __init__(cls, *args, **kwargs):
        cls._instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class _LoggerConf(metaclass=Singleton):
    """logger conf"""

    def __init__(self):
        with open(f'{CONF_DIR}/logger.yml') as fp:
            self.value = yaml.load(fp)


class _RequestsConf(metaclass=Singleton):
    """requests session config"""

    def __init__(self):
        with open(f'{CONF_DIR}/request.yml') as fp:
            self.value = yaml.load(fp)


class AccountConf(metaclass=Singleton):
    """account config"""

    def __init__(self):
        with open(f'{CONF_DIR}/account.yml') as fp:
            self.value = yaml.load(fp)


class PullConf(metaclass=Singleton):
    """pull config"""

    def __init__(self):
        with open(f'{CONF_DIR}/pull.yml') as fp:
            self.value = yaml.load(fp)


class PushConf(metaclass=Singleton):
    """push config"""

    def __init__(self):
        with open(f'{CONF_DIR}/push.yml') as fp:
            self.value = yaml.load(fp)


class QueryConf(metaclass=Singleton):
    """query config"""

    def __init__(self):
        with open(f'{CONF_DIR}/query.graphql') as fp:
            self.value = fp.read()


@functools.lru_cache(maxsize=128)
def logger(name):
    """get logger"""

    conf = _LoggerConf().value
    fmt = logging.Formatter(conf['fmt'])
    level = getattr(logging, conf['level'])

    logger_ = logging.getLogger(name=name)
    logger_.setLevel(level)
    if not logger_.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(fmt)
        logger_.addHandler(handler)

    return logger_


class Session:
    """request session wrapper"""

    def __init__(self):
        conf = _RequestsConf().value
        self.timeout = conf['timeout']
        self.user_agent = conf['user_agent']

        self.session = requests.session()

    def request(self, method='get', *args, **kwargs):
        kwargs['timeout'] = self.timeout
        if 'headers' not in kwargs:
            kwargs['headers'] = {'User-Agent': self.user_agent}
        else:
            kwargs['headers']['User-Agent'] = self.user_agent

        return getattr(self.session, method)(*args, **kwargs)

    def get_cookies(self):
        return self.session.cookies.get_dict()

    def set_cookies(self, data):
        return requests.utils.add_dict_to_cookiejar(self.session.cookies, data)
