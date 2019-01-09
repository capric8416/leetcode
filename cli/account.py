# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from getpass import getpass

from fire import Fire

from .common import AccountConf, DATA_DIR, Session, logger


class Account:
    def __init__(
            self,
            index_url: str,
            sign_in_url: str,
            user: str,
            password: str,
            path: str,
            force: bool
    ):
        """
        Initial
        :param index_url: homepage url
        :param sign_in_url: sign in url
        :param user: user name
        :param password: user password
        :param path: cookies path
        :param force: force re-sign-in
        """

        self.index_url = index_url
        self.sign_in_url = sign_in_url

        self.user = user
        self.password = password
        self.path = path

        self.force = force

        self.session = Session()

        self.logger = logger(name=self.__class__.__name__)

    @classmethod
    def run(cls, method: str, force: bool = False):
        """
        launch entry
        :param method: target method
        :param force: force re-sign-in
        :return:
        """

        logger_ = logger(cls.__name__)

        conf, path = cls.config()

        if method not in conf['methods']:
            logger_.info('Available methods: %s', conf['methods'])
            return

        password = ''
        if method == cls.sign_in.__name__:
            password = getpass()
            assert password, 'Empty password not allowed'

        obj = cls(
            index_url=conf['url']['index'],
            sign_in_url=conf['url']['sign_in'],
            user=conf['account']['user'],
            password=password,
            path=path,
            force=force,
        )
        return getattr(obj, method)(), obj.session.get_cookies()

    @staticmethod
    def config() -> tuple:
        """read configuration"""

        conf = AccountConf().value

        path = conf['path']['cookie'].format(data_dir=DATA_DIR, user=conf['account']['user'])
        os.makedirs(os.path.dirname(path), exist_ok=True)

        return conf, path

    def index(self) -> tuple:
        """visit index page"""

        self.session.set_cookies(self.load())
        resp = self.session.request(url=self.index_url)
        return resp.url, self.session.get_cookies()['csrftoken'], self._check(text=resp.text)

    def sign_in(self):
        """sign in"""

        refer, token, signed_in = self.index()
        if not self.force and signed_in:
            self.logger.info('No need to login again')
            return True

        headers = {'Referer': refer}
        data = {
            'login': self.user,
            'password': self.password,
            'next': '/problems',
            'csrfmiddlewaretoken': token
        }

        resp = self.session.request(method='post', url=self.sign_in_url, headers=headers, data=data)
        if not self.check(text=resp.text):
            self.logger.info('Login failed, please check your user and password')
            return False

        self.logger.info('Login succeed, save cookies')
        self.dump(cookies=self.session.get_cookies())

        return True

    def sign_out(self):
        """sign out"""

        if os.path.exists(self.path):
            os.remove(self.path)

    def check(self, text: str = ''):
        """check signed_in"""

        return self._check(text) if text else self.index()[-1]

    @staticmethod
    def _check(text: str):
        return 'isSignedIn: true' in text

    def dump(self, cookies: dict):
        """write cookies"""

        with open(self.path, mode='w') as fp:
            json.dump(obj=cookies, fp=fp, ensure_ascii=False, indent='\t', sort_keys=True)

    def load(self) -> dict:
        """read cookies"""

        if not os.path.exists(self.path):
            return {}

        with open(self.path) as fp:
            try:
                return json.load(fp)
            except ValueError:
                return {}


account = Account.run

if __name__ == '__main__':
    Fire(account)
