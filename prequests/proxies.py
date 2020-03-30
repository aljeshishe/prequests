import json
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime
from pprint import pprint
import logging
from threading import Lock

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
        self.seq_errors = 0
        self.requests = 0

    def __enter__(self):
        self.start_time = time.time()
        self.requests += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.append(Request(time=time.time() - self.start_time, exception=exc_val))
        if exc_type:
            self.errors += 1
            self.seq_errors += 1
        else:
            self.seq_errors = 0

    def __str__(self):
        return f'{self.host_port} req:{self.requests} err:{self.errors} seq_err:{self.seq_errors}'

    __repr__ = __str__

    @property
    def host_port(self):
        return f'{self.host}:{self.port}'


class Proxies(SingletonMixin):

    def __init__(self, proxies=None):
        self.lock = Lock()
        self.proxies = self._prepare_proxies(proxies)
        self.bad_proxies = deque()
        self.used_proxies = 0
        self.max_used_proxies = 0
        if not self.proxies:
            raise Exception('No proxies received from proxybroker')

    @staticmethod
    def _prepare_proxies(proxies=None):
        if proxies:
            proxies = [Proxy.from_string(proxy_str) for proxy_str in proxies]
        else:
            proxies = requests.get('http://proxybroker.grachev.space/').json()
            with open('proxies_{}.json'.format(datetime.now().strftime('%y_%m_%d__%H_%M_%S')), 'w') as fp:
                json.dump(fp=fp, obj=proxies, indent=2)

        return deque([Proxy.from_dict(d) for d in proxies if {'type': 'HTTPS', 'level': ''} in d['types']][:20])

    @contextmanager
    def borrow(self):
        proxy = self.get()
        try:
            with proxy:
                yield proxy
        finally:
            self.put_back(proxy=proxy)

    def get(self):
        with self.lock:
            if len(self.proxies) < 10:
                log.warn(f'good: {len(self.proxies)} < 10 >, retreiving more')
                self.proxies += self._prepare_proxies()
        proxy = self.proxies.pop()
        log.info('Got proxy {}'.format(proxy))
        self.used_proxies += 1
        self.max_used_proxies = max(self.used_proxies, self.max_used_proxies)
        return proxy

    def put_back(self, proxy):
        if proxy.seq_errors >= 4:
            self.bad_proxies.appendleft(proxy)
        else:
            self.proxies.appendleft(proxy)
        self.used_proxies -= 1
        log.info(f'Putting back proxy {proxy} bad:{len(self.bad_proxies)} good:{len(self.proxies)} used:{self.used_proxies}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    proxies = Proxies()
    a = proxies.get()
    print(a)
    proxies.close()
    time.sleep(1000)
