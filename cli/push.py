# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os

from fire import Fire

from .account import account
from .common import DATA_DIR, PullConf, PushConf, Session, logger


class Push:
    def __init__(
            self,
            cookies: dict,
            content_url: str,
            submit_url: str,
            check_url: str,
            submit_src: str,
            ext_lang: dict,
            ext_comment: dict,
            slug_id: dict,
            delimiter: str,
    ):
        """
        Initial
        :param cookies: sign in cookies
        :param content_url: content url
        :param submit_url: submit url
        :param check_url: submission check url
        :param submit_src: source path
        :param ext_lang: dict[ext][lang]
        :param ext_comment: dict[ext][comment]
        :param slug_id: dict[slug][id]
        :param delimiter: delimiter line
        """

        self.content_url = content_url

        self.submit_src = submit_src
        self.submit_url = submit_url
        self.check_url = check_url

        name, ext = os.path.splitext(os.path.basename(submit_src))
        ext = ext.lstrip('.')
        self.lang = ext_lang[ext]
        self.slug = name.replace('_', '-')
        self.id = slug_id[self.slug]
        s_comment, e_comment = ext_comment[ext]
        self.delimiter = f'{s_comment} {delimiter} {e_comment}'

        self.session = Session()
        self.session.set_cookies(cookies)

        self.logger = logger(name=self.__class__.__name__)

    @classmethod
    def run(cls, method: str, path: str, clean: bool = False):
        """
        launch entry
        :param method: target method
        :param path: path of source
        :param clean: remove source
        """

        logger_ = logger(cls.__name__)

        pull_conf, push_conf = cls.config()

        if method not in push_conf['methods']:
            logger_.info('Available methods: %s', push_conf['methods'])
            return

        with open(pull_conf['path']['toc'].format(data_dir=DATA_DIR)) as fp:
            toc = json.load(fp)

        stat = pull_conf['keys']['toc']['stat']
        question_slug = pull_conf['keys']['toc']['question_slug']
        question_id = pull_conf['keys']['toc']['question_id']
        slug_id = {entry[stat][question_slug]: entry[stat][question_id] for entry in toc}

        ext_lang = {v['ext']: k for k, v in pull_conf['languages'].items()}
        ext_comment = {v['ext']: v['comment'] for k, v in pull_conf['languages'].items()}

        while True:
            signed_in, cookies = account(method='check')
            if signed_in:
                break
            signed_in, cookies = account(method='sign_in')
            if signed_in:
                break

        obj = cls(
            cookies=cookies,
            content_url=pull_conf['url']['content'],
            submit_url=push_conf['url']['submit'],
            check_url=push_conf['url']['check'],
            submit_src=path,
            ext_lang=ext_lang,
            ext_comment=ext_comment,
            slug_id=slug_id,
            delimiter=pull_conf['source']['delimiter']
        )
        result = getattr(obj, method)()

        if clean:
            os.remove(path)

        return result

    @staticmethod
    def config() -> tuple:
        """read configuration"""

        return PullConf().value, PushConf().value

    def submit(self):
        """submit source"""

        with open(self.submit_src) as fp:
            src_code = fp.read()
            s, e = src_code.find(self.delimiter), src_code.rfind(self.delimiter)
            s = 0 if s < 0 else s + len(self.delimiter)
            if e < 0:
                e = len(src_code)
            src_code = src_code[s:e].strip()

        refer, token = self.content()
        headers = {'x-csrftoken': token, 'Referer': refer, 'content-type': 'application/json'}
        data = {
            'lang': self.lang,
            'question_id': self.id,
            'typed_code': src_code
        }

        resp = self.session.request(method='post', url=self.submit_url, headers=headers, data=json.dumps(data))
        submission_id = resp.json()['submission_id']

        self.check(refer=refer, submission_id=submission_id)

    def check(self, refer: str, submission_id: int):
        """check submission"""

        headers = {'Referer': refer}

        while True:
            data = self.session.request(url=self.check_url.format(submission_id=submission_id), headers=headers).json()
            stat = data['state']
            self.logger.info(stat)

            if stat == 'STARTED':
                continue
            if stat == 'SUCCESS':
                s, r, p, m, n = data['status_msg'], data['status_runtime'], \
                                data['runtime_percentile'] or 'N/A', data.get('memory', 'N/A'), data['pretty_lang']
                self.logger.info(f'Status: {s}, runtime: {r}, memory: {m} bytes, '
                                 f'faster than {p}% of {n} online submissions for Two Sum.')
                if s != 'Accepted':
                    self.logger.error(
                        data.get('full_compile_error') or
                        data.get('full_runtime_error') or
                        data.get('last_testcase')
                    )

            break

    def content(self):
        """visit content page"""

        resp = self.session.request(url=f'{self.content_url}/{self.slug}/')
        return resp.url + 'submissions/', self.session.get_cookies()['csrftoken']


push = Push.run
if __name__ == '__main__':
    Fire(push)
