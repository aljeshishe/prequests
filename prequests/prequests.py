import logging
import string
from contextlib import contextmanager

import requests as _requests
from requests import ConnectTimeout
from requests.exceptions import ProxyError, SSLError, ConnectionError, ReadTimeout
from .proxies import Proxies, NoProxiesLeftException

log = logging.getLogger(__name__)


class NeedToRetryException(Exception): pass

class TooMuchTries(Exception): pass


def _raise_if_need_retry(response, retry_on):
    if retry_on is None:
        return

    # TODO implement here
    # if response.headers['content-type'] == 'application/json':
    #     response.json()  # avoiding incorrect json even if 200
    codes = as_tuple(retry_on)

    if response.status_code in codes:
        raise NeedToRetryException('Need to retry request')


def save(self, proxy):
    url_last_part = self.url.split('/')[-1]
    name = f'{url_last_part}_{proxy.host_port}.html'
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    name = ''.join(c for c in name if c in valid_chars)
    with open(name, 'w', encoding=self.encoding) as f:
        f.write(self.text)
    return self


def as_tuple(list_tuple_item_or_none):
    if list_tuple_item_or_none is None:
        return ()
    if not isinstance(list_tuple_item_or_none, (list, tuple)):
        return (list_tuple_item_or_none,)

    return list_tuple_item_or_none

@contextmanager
def context(verbose=True, ignore_exceptions=None, raise_exceptions=None, **kwargs):
    ignore_exceptions = as_tuple(ignore_exceptions)
    raise_exceptions = as_tuple(raise_exceptions)

    to_str = lambda d:  ' '.join(map(lambda i: f'{i[0]}={i[1]}', d.items()))
    kwargs_str = to_str(kwargs)
    if verbose:
        log.info(f'Processing {kwargs_str}')
    try:
        yield kwargs
        if verbose:
            log.info(f'Finished processing {to_str(kwargs)}')
    except Exception as e:
        no_traceback = any([isinstance(e, exc) for exc in ignore_exceptions])
        exc_type = e.__class__.__name__ if no_traceback else ''
        log.exception(f'Exception {exc_type} while processing {to_str(kwargs)}', exc_info=not no_traceback)
        if any([isinstance(e, exc) for exc in raise_exceptions]):
            raise e


def request(method, url, retry_on=None, **kwargs):
    proxies = Proxies.instance()
    exception = None
    TRIES = 100
    for i in range(TRIES):
        with context(method=method, url=url, tries=TRIES, try_num=i,
                     ignore_exceptions=(ConnectTimeout, ProxyError, NeedToRetryException, SSLError,
                                        ConnectionError, ReadTimeout),
                     raise_exceptions=NoProxiesLeftException) as ctx:
            with proxies.borrow() as proxy:
                ctx['proxy'] = proxy.host_port
                kwargs['proxies'] = dict(http=proxy.host_port, https=proxy.host_port)
                kwargs['timeout'] = (10, 20)
                kwargs['headers'] = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}
                response = _requests.request(method=method, url=url, **kwargs)
                ctx['status_code'] = response.status_code
                _raise_if_need_retry(response=response, retry_on=retry_on)
                return response
    raise TooMuchTries()


def get(url, params=None, **kwargs):
    r"""Sends a GET request.

    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary, list of tuples or bytes to send
        in the query string for the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    kwargs.setdefault('allow_redirects', True)
    return request('get', url, params=params, **kwargs)


def options(url, **kwargs):
    r"""Sends an OPTIONS request.

    :param url: URL for the new :class:`Request` object.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    kwargs.setdefault('allow_redirects', True)
    return request('options', url, **kwargs)


def head(url, **kwargs):
    r"""Sends a HEAD request.

    :param url: URL for the new :class:`Request` object.
    :param \*\*kwargs: Optional arguments that ``request`` takes. If
        `allow_redirects` is not provided, it will be set to `False` (as
        opposed to the default :meth:`request` behavior).
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    kwargs.setdefault('allow_redirects', False)
    return request('head', url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    r"""Sends a POST request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) json data to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request('post', url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    r"""Sends a PUT request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) json data to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request('put', url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    r"""Sends a PATCH request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) json data to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request('patch', url, data=data, **kwargs)


def delete(url, **kwargs):
    r"""Sends a DELETE request.

    :param url: URL for the new :class:`Request` object.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request('delete', url, **kwargs)

if __name__=='__main__':
    response = get('https://ya.ru')
    print(response, response.content)
