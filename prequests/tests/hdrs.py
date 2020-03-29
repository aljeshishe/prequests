import json
from logging.handlers import RotatingFileHandler
from threading import Thread

import requests

import prequests
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d|%(levelname)-4.4s|%(thread)-6.6s|%(funcName)-10.10s|%(message)s',
                    handlers=[logging.StreamHandler(),
                              RotatingFileHandler("log.log", maxBytes=1024*1024*200, backupCount=4)
                              ])


urls = '''ya.ru
google.com
www.google.com/search?q=1234&oq=1234
www.google.com/searsdfch?q=1234&oq=1234
tox.readthedocs.io/en/latest/
tox.readthedocs.io/en/latsdfest/
www.avito.ru/sankt-peterburg
www.avito.ru/sankt-pesdfterburg
igooods.ru/products
igooods.ru/producsdfts'''


def func(url):
    print(url)
    while 1:
        try:
            r = prequests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'})
            data = dict(r.headers)
            data['url'] = url
            data['status_code'] = r.status_code
            data['proxy'] = False
            with open('reqs.json', 'a') as fp:
                fp.write('{}\n'.format(json.dumps(data)))
            return
        except Exception as e:
            pass

threads = []
for pre in ('http://', 'https://'):
    for url in urls.split('\n'):
        t = Thread(target=func, kwargs=dict(url=pre + url))
        t.start()
        threads.append(t)

[t.join() for r in threads]