import json
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime
from pprint import pprint
import logging
from threading import Lock

import requests
from prequests.proxy import Proxy
from prequests.utils import context

from .singleton import SingletonMixin

log = logging.getLogger(__name__)

ALL_TYPES = dict.fromkeys(['HTTP', 'HTTPS', 'CONNECT:80', 'CONNECT:25', 'SOCKS4', 'SOCKS5'])

class NoProxiesLeftException(Exception): pass


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

        return deque([Proxy.from_dict(d) for d in proxies if {'type': 'HTTPS', 'level': ''} in d['types']])

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
                log.warn(f'good: {len(self.proxies)} < 10, retreiving more')
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
