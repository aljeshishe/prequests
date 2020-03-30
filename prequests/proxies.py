import json
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime
from pprint import pprint
import logging

import requests

from .singleton import SingletonMixin

log = logging.getLogger(__name__)

ALL_TYPES = dict.fromkeys(['HTTP', 'HTTPS', 'CONNECT:80', 'CONNECT:25', 'SOCKS4', 'SOCKS5'])

class NoProxiesLeftException(Exception): pass

class Request:
    def __init__(self, time, exception):
        self.time = time
        self.exception = exception

    def __str__(self):
        return f'{self.time}: {self.exception}'

    __repr__ = __str__


class Proxy:
    @staticmethod
    def from_dict(d):
        return Proxy(host=d['host'], port=d['port'])

    @staticmethod
    def from_string(s):
        host, _, port = s.partition(':')
        return Proxy(host=host, port=port if port else '80')

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.log = []
        self.errors = 0
        self.requests = 0

    def __enter__(self):
        self.start_time = time.time()
        self.requests += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.append(Request(time=time.time() - self.start_time, exception=exc_val))
        if exc_type:
            self.errors += 1

    def __str__(self):
        return f'{self.host_port} req:{self.requests} err:{self.errors}'

    __repr__ = __str__

    @property
    def host_port(self):
        return f'{self.host}:{self.port}'


class Proxies(SingletonMixin):

    def __init__(self, proxies=None):
        if proxies:
            proxies = [Proxy.from_string(proxy_str) for proxy_str in proxies]
        else:
            proxies = [Proxy.from_dict(d) for d in self._get_proxies() if {'type': 'HTTPS', 'level': ''} in d['types']]

        self.proxies = deque(proxies[:300])
        self.bad_proxies = deque()
        if not self.proxies:
            raise Exception('No proxies received from proxybroker')

    def _get_proxies(self):
        proxies = requests.get('http://proxybroker.grachev.space/').json()
        with open('proxies_{}.json'.format(datetime.now().strftime('%y_%m_%d__%H_%M_%S')), 'w') as fp:
            json.dump(fp=fp, obj=proxies, indent=2)
        return proxies

    @contextmanager
    def borrow(self):
        proxy = self.get()
        try:
            with proxy:
                yield proxy
        finally:
            self.put_back(proxy=proxy)

    def get(self):
        if not self.proxies:
            raise NoProxiesLeftException()
        proxy = self.proxies.pop()
        log.info('Got proxy {}'.format(proxy))
        return proxy

    def put_back(self, proxy):
        if proxy.errors >= 3:
            self.bad_proxies.appendleft(proxy)
        else:
            self.proxies.appendleft(proxy)
        log.info(f'Putting back proxy {proxy} bad:{len(self.bad_proxies)} all:{len(self.proxies)}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    proxies = Proxies()
    a = proxies.get()
    print(a)
    proxies.close()
    time.sleep(1000)
