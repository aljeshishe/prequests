import json
import tempfile
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from pprint import pprint
import logging
from queue import PriorityQueue
from threading import Lock

import requests
from prequests.proxy import Proxy
from prequests.utils import context

from .singleton import SingletonMixin

log = logging.getLogger(__name__)

ALL_TYPES = dict.fromkeys(['HTTP', 'HTTPS', 'CONNECT:80', 'CONNECT:25', 'SOCKS4', 'SOCKS5'])


class NoProxiesLeftException(Exception): pass


class Proxies(SingletonMixin):

    def __init__(self, proxies=None, throttling_interval_secs=1, temp_dir=None):
        self.throttling_interval_secs = throttling_interval_secs
        self.lock = Lock()
        self.proxies = PriorityQueue()
        self.bad_proxies = 0
        self.used_proxies = 0
        self.temp_dir = Path(tempfile.gettempdir() if temp_dir is None else temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now().strftime('%y%m%d_%H%M%S')
        self.stats_fp = open(self.temp_dir / f'prequests_stats_{now}.json', 'a')
        self._populate_proxies()

        if not self.proxies:
            raise Exception('No proxies received from proxybroker')

    def _populate_proxies(self, proxies=None):
        with self.lock:
            if proxies:
                proxies = [Proxy.from_string(proxy_str) for proxy_str in proxies]
            else:
                proxies = requests.get('http://proxybroker.grachev.space/').json()
                now = datetime.now().strftime('%y%m%d_%H%M%S')
                with open(self.temp_dir / f'prequests_proxies_{now}.json', 'w') as fp:
                    json.dump(fp=fp, obj=proxies, indent=2)
                proxies = [Proxy.from_dict(proxy) for proxy in proxies if {'type': 'HTTPS', 'level': ''} in proxy['types']]

            for proxy in proxies:
                proxy.throttling_interval_secs = self.throttling_interval_secs
                proxy.temp_dir = self.temp_dir
                proxy.stats_fp = self.stats_fp
                self.proxies.put(proxy.as_tuple())

    @contextmanager
    def borrow(self):
        proxy = self.get()
        try:
            with proxy:
                yield proxy
        finally:
            self.put_back(proxy=proxy)

    def get(self):
        datetm, proxy = self.proxies.get()
        delta = (datetm - datetime.now()).total_seconds()
        self.used_proxies += 1
        log.info(msg=f'Got proxy {proxy} waiting {delta}')
        if delta > 30:
            log.warn(f'Waiting time > 30 seconds, retrieving more')
            self._populate_proxies()

        if delta < 0:
            delta = 0
        time.sleep(delta)
        log.info(f'{proxy} waiting done')
        return proxy

    def put_back(self, proxy):
        if proxy.errors == proxy.seq_errors >= 4:
            self.bad_proxies += 1
        else:
            self.proxies.put(proxy.as_tuple())
        self.used_proxies -= 1
        log.info(f'Putting back proxy {proxy} bad:{self.bad_proxies} good:{self.proxies.qsize()} used:{self.used_proxies}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    proxies = Proxies()
    a = proxies.get()
    print(a)
    proxies.close()
    time.sleep(1000)
