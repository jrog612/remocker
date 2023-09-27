import json as _json
import re
from contextlib import contextmanager
from functools import cached_property

import httpretty


def join_path(str1, str2):
    if str1[-1] == '/':
        if str2[0] == '/':
            return str1 + str2[1:]
        else:
            return str1 + str2
    else:
        if str2[0] == '/':
            return str1 + str2
        else:
            return str1 + '/' + str2


class Remocker:
    def __init__(self, base_url, ):
        self.storages = []
        self.mockers = []
        if callable(base_url):
            self.base_url = base_url()
        else:
            self.base_url = base_url

    def get_full_uri(self, uri):
        if not uri.startswith('http'):
            return join_path(self.base_url, uri)
        return uri

    def get_uri_params(self, uri, pattern):
        if type(pattern) in (str, bytes):
            pattern = re.compile(pattern)
        return re.search(pattern, uri)

    def _append_mocker(self, method, uri, body, regex=False, **kwargs):
        if not callable(body):
            body = _json.dumps(body)

        if type(uri) is str:
            uri = self.get_full_uri(uri)

        if regex:
            uri = re.compile(uri)

        self.mockers.append({
            'method': method.upper(),
            'uri': uri,
            'body': body,
            'regex': regex,
            **kwargs,
        })

    def mock(self, method, path, regex=False, **kwargs):
        def decorator(func):
            def inner(request, uri, response_headers):
                remocker_request = RemockerRequest(
                    request,
                    uri,
                    method,
                    response_headers,
                    uri_pattern=path if regex else None,
                )
                response = func(remocker_request)
                self.storages.append(
                    RemockerLog(request=remocker_request, response=response)
                )
                if response.headers is None:
                    response.headers = response_headers
                return response.to_tuple()

            self._append_mocker(method, path, inner, regex=regex, **kwargs)
            return inner

        return decorator

    def apply_mockers(self):
        for m in self.mockers:
            httpretty.register_uri(**m)
        return True

    @contextmanager
    def mocking(self, allow_net_connect=False, verbose=False):
        with mocking(self, allow_net_connect=allow_net_connect, verbose=verbose) as app:
            yield app


@contextmanager
def mocking(mocker_app: Remocker, allow_net_connect=False, verbose=False):
    httpretty.reset()
    httpretty.enable(allow_net_connect=allow_net_connect, verbose=verbose)
    mocker_app.apply_mockers()
    yield mocker_app
    httpretty.disable()
    httpretty.reset()


class RemockerResponse:
    def __init__(
            self,
            body,
            status_code=200,
            headers=None
    ):
        self.body = body
        self.status_code = status_code or 200
        self.headers = headers

    @property
    def string_body(self):
        if type(self.body) is str:
            return self.body
        return _json.dumps(self.body)

    def to_tuple(self):
        return self.status_code, self.headers, self.string_body


class RemockerRequest:
    def __init__(
            self,
            request,
            uri,
            method,
            response_headers,
            uri_pattern=None,
    ):
        self.origin_request = request
        self.uri = uri
        self.method = method
        self.response_headers = response_headers
        self.uri_pattern = uri_pattern

    @cached_property
    def url_params(self):
        if self.uri_pattern is not None:
            matched = re.search(self.uri_pattern, self.uri)
            return matched.groupdict()
        else:
            return {}

    @cached_property
    def data(self):
        return _json.loads(self.origin_request.body)

    @cached_property
    def query_params(self):
        result = {}
        for key, value in self.origin_request.querystring.items():
            if not value:
                result[key] = None

            if type(value) is list and len(value) == 1:
                result[key] = value[0]
            else:
                result[key] = value
        return result


class RemockerLog:
    def __init__(self, request, response):
        self.request = request
        self.response = response
