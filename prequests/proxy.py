import json
import time
from datetime import datetime

from prequests.utils import context


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
        time_left = time.time() - self.start_time
        self.log.append(Request(time=time_left, exception=exc_val))
        if exc_type:
            self.errors += 1
            self.seq_errors += 1
        else:
            self.seq_errors = 0
        self.dump(exc=exc_type, time_left=time_left)

    def dump(self, exc, time_left):
        with context(verbose=False):
            with open('prequests_stats.json', 'a') as fp:
                data = dict(proxy=self.host_port, exc=str(exc), datetm=str(datetime.now()),
                            requests=self.requests, errors=self.errors, seq_errors=self.seq_errors,
                            time_left=time_left)
                fp.write(f'{json.dumps(data)}\n')

    def __str__(self):
        return f'{self.host_port} req:{self.requests} err:{self.errors} seq_err:{self.seq_errors}'

    __repr__ = __str__

    @property
    def host_port(self):
        return f'{self.host}:{self.port}'
