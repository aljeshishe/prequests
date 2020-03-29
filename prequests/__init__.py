"""
Copyright © 2020 aljeshishe <aljeshishe@gmail.com>. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__title__ = 'prequests'
__package__ = 'prequests'
__version__ = '0.0.1'
__short_description__ = 'Requests with automatic proxy crawler.'  # noqa
__author__ = 'aljeshishe'
__author_email__ = 'aljeshishe@gmail.com'
__url__ = 'https://github.com/aljeshishe/prequests'
__license__ = 'Apache License, Version 2.0'
__copyright__ = 'Copyright 2020 aljeshishe'


from .prequests import Proxies, request, get, head, post, patch, put, delete, options  # noqa

from requests import utils
from requests import packages
from requests.models import Request, Response, PreparedRequest
from requests.sessions import session, Session
from requests.status_codes import codes
from requests.exceptions import (
    RequestException, Timeout, URLRequired,
    TooManyRedirects, HTTPError, ConnectionError,
    FileModeWarning, ConnectTimeout, ReadTimeout
)