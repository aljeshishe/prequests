import json
import logging
import os
import time
from datetime import datetime, timedelta

from prequests.utils import context


log = logging.getLogger(__name__)


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

    def __init__(self, host, port, ):
        self.throttling_interval_secs = 1
        self.stats_fp = open(os.devnull, 'w')
        self.host = host
        self.port = port
        self.log = []
        self.errors = 0
        self.seq_errors = 0
        self.requests = 0
        self.next_datetm = None
        self.interval = 0

    def as_tuple(self):
        self.interval = self.throttling_interval_secs * self.seq_errors
        if self.requests:
            self.interval += self.throttling_interval_secs
        self.next_datetm = datetime.now() + timedelta(seconds=self.interval)
        log.info(f'{self} will be used at {self.next_datetm} after {self.interval} seconds')
        return self.next_datetm, self

    def __enter__(self):
        self.start_time = time.time()
        self.requests += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = time.time() - self.start_time
        self.log.append(Request(time=elapsed_time, exception=exc_val))
        if exc_type:
            self.errors += 1
            self.seq_errors += 1
        else:
            self.seq_errors = 0
        self.dump(exc=exc_type, elapsed_time=elapsed_time)

    def dump(self, exc, elapsed_time):
        with context(verbose=False):
            data = dict(proxy=self.host_port,
                        exc='' if exc else exc.__name__,
                        datetm=str(datetime.now()),
                        requests=self.requests, errors=self.errors, seq_errors=self.seq_errors,
                        elapsed_time=f'{elapsed_time:.3f}', interval=self.interval)
            self.stats_fp.write(f'{json.dumps(data)}\n')
            self.stats_fp.flush()

    def __str__(self):
        return f'{self.host_port} req:{self.requests} err:{self.errors} seq_err:{self.seq_errors}'

    __repr__ = __str__

    @property
    def host_port(self):
        return f'{self.host}:{self.port}'
