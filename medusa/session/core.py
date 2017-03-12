# coding=utf-8

from __future__ import unicode_literals

import certifi
import errno
import logging
import requests
import traceback

from . import hooks
from .. import app
import medusa.common
import factory

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class BaseSession(requests.Session):
    """Base Session object.

    This is a Medusa base session, used to create and configure a session object with Medusa specific base
    values.
    """
    default_headers = {
        'User-Agent': medusa.common.USER_AGENT,
        'Accept-Encoding': 'gzip,deflate',
    }


class MedusaSession(BaseSession):
    """Base Session object.

    This is a Medusa base session, used to create and configure a session object with Medusa specific base
    values.

    :param verify: Enable/Disable SSL certificate verification.
    :param proxies: Provide a proxy configuration in the form of a dict: {
        "http": address,
        "https": address,
    }
    Optional arguments:
    :param hooks: Provide additional 'response' hooks, provided as a list of functions.
    :cache_control: Provide a cache control dict of cache_control options.
    :example: {'cache_etags': True, 'serializer': None, 'heuristic': None}
    :return: The response as text or False.
    """

    def __init__(self, verify=True, proxies=factory.add_proxies(), **kwargs):
        """Create base Medusa session instance."""
        # Add response hooks
        self.my_hooks = kwargs.pop('hooks', [])

        # Pop the cache_control config
        cache_control = kwargs.pop('cache_control', None)

        # Initialize request.session
        super(MedusaSession, self).__init__()

        # Add cache control of provided as a dict. Needs to be attached after super init.
        if cache_control:
            factory.add_cache_control(self, cache_control)

        # add proxies
        self.proxies = proxies

        # Configure global session hooks
        self.hooks['response'].append(hooks.log_url)

        # Extend the hooks with kwargs provided session hooks
        self.hooks['response'].extend(self.my_hooks)

        # Set default headers.
        for header, value in self.default_headers.items():
            # Use `setdefault` to avoid clobbering existing headers
            self.headers.setdefault(header, value)

        # Set default ssl verify
        self.verify = certifi.old_where() if all([app.SSL_VERIFY, verify]) else False

    def request(self, method, url, data=None, params=None, headers=None, timeout=30, **kwargs):

        try:
            resp = super(MedusaSession, self).request(method, url, params=params, data=data, headers=headers,
                                                      timeout=30, **kwargs)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log.debug(u'The response returned a non-200 response while requestion url {url}. Error: {err_msg}',
                      url=url, err_msg=e)
            return None
        except requests.exceptions.RequestException as e:
            log.debug(u'Error requesting url {url}. Error: {err_msg}', url=url, err_msg=e)
            return None
        except Exception as e:
            if u'ECONNRESET' in e or (hasattr(e, u'errno') and e.errno == errno.ECONNRESET):
                log.warning(
                    u'Connection reset by peer accessing url {url}. Error: {err_msg}'.format(url=url, err_msg=e)
                )
            else:
                log.info(u'Unknown exception in url {url}. Error: {err_msg}', url=url, err_msg=e)
                log.debug(traceback.format_exc())
            return None
        return resp


class TextSession(MedusaSession):
    """Text Session class.

    This is a Medusa text session, used to create and configure a session object that's tailored to requesting and
    retunring text. It includes the basic request and response exception handling. Making it easy to use, and not
    needing to implement this in the requester.

    :param verify: Enable/Disable SSL certificate verification.

    Optional arguments:
    :param hooks: Provide additional 'response' hooks, provided as a list of functions.
    :cache_control: Provide a cache control dict of cache_control options.
    :example: {'cache_etags': True, 'serializer': None, 'heuristic': None}
    """

    def __init__(self, verify=True, **kwargs):
        """Initialize the TextSession object."""
        # Initialize request.session
        super(TextSession, self).__init__(verify, **kwargs)

    def request(self, method, url, data=None, headers=None, timeout=30, **kwargs):
        resp = super(TextSession, self).request(method, url, data=None, params=None, headers=None, timeout=30, **kwargs)
        return resp.text if resp else False


class ContentSession(MedusaSession):
    """Text Session class.

    This is a Medusa content session, used to create and configure a session object that's tailored to requesting and
    returning content. It includes the basic request and response exception handling. Making it easy to use, and not
    needing to implement this in the requester.

    :param verify: Enable/Disable SSL certificate verification.

    Optional arguments:
    :param hooks: Provide additional 'response' hooks, provided as a list of functions.
    :cache_control: Provide a cache control dict of cache_control options.
    :example: {'cache_etags': True, 'serializer': None, 'heuristic': None}
    :return: The response as content or False.
    """

    def __init__(self, verify=True, **kwargs):
        """Initialize the TextSession object."""
        # Initialize request.session
        super(ContentSession, self).__init__(verify, **kwargs)

    def request(self, method, url, data=None, headers=None, timeout=30, **kwargs):
        resp = super(ContentSession, self).request(method, url, data=None, params=None, headers=None,
                                                   timeout=30, **kwargs)
        return resp.content if resp else False


class JsonSession(MedusaSession):
    """Text Session class.

    This is a Medusa content session, used to create and configure a session object that's tailored to requesting and
    returning content. It includes the basic request and response exception handling. Making it easy to use, and not
    needing to implement this in the requester.

    :param verify: Enable/Disable SSL certificate verification.

    Optional arguments:
    :param hooks: Provide additional 'response' hooks, provided as a list of functions.
    :cache_control: Provide a cache control dict of cache_control options.
    :example: {'cache_etags': True, 'serializer': None, 'heuristic': None}
    :return: The response as dict or False.
    """

    def __init__(self, verify=True, **kwargs):
        """Initialize the TextSession object."""
        # Initialize request.session
        super(JsonSession, self).__init__(verify, **kwargs)

    def request(self, method, url, data=None, headers=None, timeout=30, **kwargs):
        resp = super(JsonSession, self).request(method, url, data=None, params=None, headers=None,
                                                timeout=30, **kwargs)
        try:
            return resp.json() if resp else False
        except ValueError as e:
            log.debug(u'Could not decode the response as json for url {url} with error {err_msg}', url=url, err_mesg=e)
            return False