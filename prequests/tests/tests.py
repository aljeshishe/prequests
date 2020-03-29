import time
from contextlib import suppress
from datetime import datetime
from logging.handlers import RotatingFileHandler
from threading import Thread

import prequests
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d|%(levelname)-4.4s|%(thread)-6.6s|%(funcName)-10.10s|%(message)s',
                    handlers=[logging.StreamHandler(),
                              RotatingFileHandler("log.log", maxBytes=100000000, backupCount=4)
                              ])

def f():
    while True:
        try:
            # prequests.Proxies.instance(proxies=['39.137.95.70:80'])
            resp = prequests.get('https://www.avito.ru/sankt-peterburg/detskaya_odezhda_i_obuv/shapki_trikotazhnye_velyur_mei_molo_polarn_lindex_1917349145',
                                 retry_on=403)
        except Exception as e:
            logging.exception('Exception while getting avito.ru')

threads = [Thread(target=f) for i in range(2)]
[t.start() for t in threads]
time.sleep(10000)