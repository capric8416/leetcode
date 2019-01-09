# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import random
import re
import time
from typing import Dict, Generator, Union

from fire import Fire
from lxml import html

from .common import DATA_DIR, PKG_PATH, PullConf, QueryConf, Session, logger


class Pull:
    def __init__(
            self,
            toc_url: str,
            content_url: str,
            graph_ql_url: str,
            graph_ql_query: str,
            toc_file: str,
            content_dir: str,
            source_dir: str,
            toc_keys: Dict[str, str],
            content_keys: dict,
            languages: dict,
            delimiter: str,
    ):
        """
        Initial
        :param toc_url: toc json url
        :param content_url: content url
        :param graph_ql_url: GraphQL url
        :param graph_ql_query: content query
        :param toc_file: toc json file
        :param content_dir: content dir
        :param source_dir: algorithms dir
        :param toc_keys: toc json keys
        :param content_keys: content json keys
        :param languages: languages conf
        :param delimiter: delimiter line
        """

        self.toc_url = toc_url
        self.graph_ql_url = graph_ql_url
        self.content_url = content_url

        self.graph_ql_query = graph_ql_query

        self.toc_file = toc_file
        self.content_dir = content_dir
        self.source_dir = source_dir

        self.toc_keys = toc_keys
        self.content_keys = content_keys

        self.languages = languages
        self.delimiter = delimiter

        self.session = Session()

        self.logger = logger(name=self.__class__.__name__)

    @classmethod
    def run(cls, method: str):
        """
        launch entry
        :param method: target method
        """

        logger_ = logger(cls.__name__)

        conf, graph_ql_query = cls.config()

        toc_file = conf['path']['toc']
        content_dir = conf['path']['content']
        source_dir = conf['path']['source']
        os.makedirs(content_dir, exist_ok=True)

        obj = cls(
            toc_url=conf['url']['toc'],
            content_url=conf['url']['content'],
            graph_ql_url=conf['url']['graph_ql'],
            graph_ql_query=graph_ql_query,
            toc_file=toc_file,
            content_dir=content_dir,
            source_dir=source_dir,
            toc_keys=conf['keys']['toc'],
            content_keys=conf['keys']['content'],
            languages=conf['languages'],
            delimiter=conf['source']['delimiter'],
        )

        if isinstance(method, str):
            method = [method]
        for m in method:
            if m not in conf['methods']:
                logger_.info('Available methods: %s', conf['methods'])
                continue

            getattr(obj, m)()

    @staticmethod
    def config() -> tuple:
        """read configuration"""

        conf = PullConf().value
        query = QueryConf().value

        for k in tuple(conf['path'].keys()):
            v = conf['path'][k]
            conf['path'][k] = v.format(path=PKG_PATH, data_dir=DATA_DIR)

        return conf, query

    def toc(self) -> None:
        """download toc"""

        data = self.session.request(url=self.toc_url).json()
        self.dump_toc(data)

    def content(self) -> None:
        """download content"""

        toc = self.load_toc()
        for index, slug in self.walk_toc(toc):
            self.logger.info(f'{index}. {slug}')

            path = self.content_path(slug)
            if self.load_content(path):
                continue

            resp = self.session.request(url=f'{self.content_url}/{slug}/')
            token = self.session.get_cookies()['csrftoken']

            data = {'query': self.graph_ql_query, 'operationName': 'questionData', 'variables': {'titleSlug': slug}}
            headers = {'x-csrftoken': token, 'referer': resp.url, 'content-type': 'application/json'}
            content = self.session.request(
                method='post', url=self.graph_ql_url, headers=headers, data=json.dumps(data)
            ).json()

            self.dump_content(path=path, data=content)

            self.wait()

    def source(self) -> None:
        """generate source snippets"""

        types = set(self.languages.keys())

        for lang in types:
            os.makedirs(self.source_path(lang=lang, slug='', ext=''), exist_ok=True)

        toc = self.load_toc()
        for index, slug in self.walk_toc(toc):
            self.logger.info(f'{index}. {slug}')

            path = self.content_path(slug)
            content = self.load_content(path)
            if not content:
                self.logger.info('  all ignored')
                continue

            d, q, c = self.content_keys['data'], self.content_keys['question'], self.content_keys['content']
            s = content[d][q][c]
            if not s:
                self.logger.info('  all locked')
                continue

            doc = html.document_fromstring(s)
            question = re.sub(r'([.?!]) ', '\g<0>\n', ''.join(doc.itertext())).strip()
            question = re.sub(r'[\r\n|\n]{3,}', '\n\n', question)

            snippets = content[d][q][self.content_keys['snippets']]
            for lang, code in self.filter_snippets(items=snippets, types=types):
                conf = self.languages[lang]
                self.dump_source(slug, lang, conf, question, code)

    def filter_snippets(self, items: list, types: set) -> Generator:
        """filter source snippets"""

        for item in items:
            lang = item[self.content_keys['lang']]
            if lang in types:
                yield lang, item[self.content_keys['code']].strip()

    def walk_toc(self, data: dict):
        """iter toc"""

        for index, item in enumerate(data):
            stat, question_slug = self.toc_keys['stat'], self.toc_keys['question_slug']
            yield index, item[stat][question_slug]

    def dump_toc(self, data: dict) -> None:
        """write toc"""

        with open(file=self.toc_file, mode='w') as fp:
            stat, frontend_id = self.toc_keys['stat'], self.toc_keys['frontend_id']
            obj = sorted(data[self.toc_keys['items']], key=lambda x: x[stat][frontend_id])
            json.dump(obj=obj, fp=fp, ensure_ascii=False, indent='\t', sort_keys=True)

    def load_toc(self):
        """read toc"""

        with open(file=self.toc_file) as fp:
            return json.load(fp=fp)

    @staticmethod
    def dump_content(path: str, data: Union[list, dict]) -> None:
        """write content"""

        with open(file=path, mode='w') as fp:
            json.dump(obj=data, fp=fp, ensure_ascii=False, indent='\t', sort_keys=True)

    def load_content(self, path: str) -> Union[None, list, dict]:
        """read content"""

        return self.load_json(path)

    def content_path(self, slug: str) -> str:
        """path of content"""

        return f'{self.content_dir}/{slug}.json'

    def dump_source(self, slug: str, lang: str, conf: dict, question: str, code: str) -> None:
        """write source"""

        path = self.source_path(slug=slug, lang=lang, ext=conf['ext'])
        source = self.load_source(path)
        if len(source) > 200:
            self.logger.info(f'  {lang} skipped')
            return

        source = []
        if conf['header']:
            source.extend(['\n'.join(conf['header']), ''])

        cs, ce = conf['comment']
        source.extend([cs, question, ce])

        delimiter = f'{cs} {self.delimiter} {ce}'
        source.extend(['\n', delimiter, '\n', code, '\n', delimiter, ''])

        with open(path, mode='w') as fp:
            fp.write('\n'.join(source).replace('\t', '    ').replace('\r\n', '\n'))

        self.logger.info(f'  {lang} updated')

    @staticmethod
    def load_source(path: str) -> Union[None, str]:
        """read source"""

        if not os.path.exists(path):
            return ''

        with open(path) as fp:
            return fp.read()

    def source_path(self, slug: str, lang: str, ext: str) -> str:
        """path of source"""

        if slug and lang and ext:
            return f'{self.source_dir}/{lang}/{slug.replace("-", "_")}.{ext}'

        return f'{self.source_dir}/{lang}'

    @staticmethod
    def load_json(path: str) -> Union[None, list, dict]:
        """read json"""

        if not os.path.exists(path):
            return

        try:
            with open(path) as fp:
                return json.load(fp)
        except ValueError:
            pass

    @staticmethod
    def wait(low: float = 0.2, up: float = 0.7, ratio: float = 2) -> None:
        """sleep"""

        time.sleep(ratio * random.uniform(low, up))


pull = Pull.run

if __name__ == '__main__':
    Fire(pull)
