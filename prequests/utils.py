import logging
from contextlib import contextmanager

log = logging.getLogger(__name__)


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
