# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from getpass import getpass

from fire import Fire

from . import DATA_DIR, LoginConf, Session, logger


class Account:
    def __init__(
            self,
            index_url: str,
            login_url: str,
            user: str,
            password: str,
            path: str,
            force: bool
    ):
        """
        参数配置
        :param index_url: homepage url
        :param login_url: login url
        :param user: user name
        :param password: user password
        :param path: cookies path
        :param force: re-login
        """

        self.index_url = index_url
        self.login_url = login_url

        self.user = user
        self.password = password
        self.path = path

        self.force = force

        self.session = Session()

        self.logger = logger(name=self.__class__.__name__)

    def index(self) -> tuple:
        """访问首页"""

        self.session.set_cookies(self.load())
        resp = self.session.request(url=self.index_url)
        return resp.url, self.session.get_cookies()['csrftoken'], self.check(text=resp.text)

    def login(self):
        """登录"""

        refer, token, logged = self.index()
        if not self.force and logged:
            self.logger.info('No need to login again')
            return True

        headers = {'Referer': refer}
        data = {
            'login': self.user,
            'password': self.password,
            'next': '/problems',
            'csrfmiddlewaretoken': token
        }

        resp = self.session.request(method='post', url=self.login_url, headers=headers, data=data)
        if not self.check(text=resp.text):
            self.logger.info('Login failed, please check your user and password')
            return False

        self.logger.info('Login succeed, save cookies')
        self.dump(cookies=self.session.get_cookies())

        return True

    def logout(self):
        """登出"""

        if os.path.exists(self.path):
            os.remove(self.path)

    def check(self, text: str = ''):
        """检查登录状态"""

        if not text:
            return self.index()[-1]

        return 'isSignedIn: true' in text

    def dump(self, cookies: dict):
        """保存登录信息"""

        with open(self.path, mode='w') as fp:
            json.dump(obj=cookies, fp=fp, ensure_ascii=False, indent='\t', sort_keys=True)

    def load(self) -> dict:
        """读取登录信息"""

        if not os.path.exists(self.path):
            return {}

        with open(self.path) as fp:
            try:
                return json.load(fp)
            except ValueError:
                return {}


def config() -> tuple:
    """读配置"""

    conf = LoginConf().value

    path = conf['path']['cookie'].format(data_dir=DATA_DIR, user=conf['account']['user'])
    os.makedirs(os.path.dirname(path), exist_ok=True)

    return conf, path


def main(target: str, force: bool = False):
    """
    执行器
    :param target: 目标方法
    :param force: 重新登录
    """

    logger_ = logger('account')

    conf, path = config()

    if not target:
        logger_.info(f'Available targets:', conf['targets'])
        return

    password = ''
    if target == 'login':
        password = getpass()
        assert password, 'Empty password not allowed'

    account = Account(
        index_url=conf['url']['index'],
        login_url=conf['url']['login'],
        user=conf['account']['user'],
        password=password,
        path=path,
        force=force,
    )
    return getattr(account, target)(), account.session.get_cookies()


if __name__ == '__main__':
    Fire(main)
