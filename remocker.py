import json as _json
import re
from contextlib import contextmanager
from functools import cached_property

import responses


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
    def __init__(self, base_url):
        self.storages = []
        self.mockers = []
        if callable(base_url):
            self.base_url = base_url()
        else:
            self.base_url = base_url

    def get_full_url(self, url):
        if not url.startswith('http'):
            return join_path(self.base_url, url)
        return url

    def _append_mocker(self, method, url, callback, regex=False, **kwargs):
        if type(url) is str:
            url = self.get_full_url(url)

        if regex:
            url = re.compile(url)

        self.mockers.append({
            'method': method.upper(),
            'url': url,
            'callback': callback,
            **kwargs,
        })

    def mock(self, method, path, regex=False, content_type="application/json", **kwargs):
        def decorator(func):
            def inner(request):
                mock_request = RemockerRequest(request, pattern=path if regex else None)

                response = func(mock_request)
                self.storages.append(
                    RemockerLog(request=mock_request, response=response)
                )
                return response.to_tuple()

            self._append_mocker(method, path, inner, regex=regex, content_type=content_type, **kwargs)
            return inner

        return decorator

    def apply_mockers(self, re_mock):
        for m in self.mockers:
            re_mock.add_callback(**m)
        return True

    @contextmanager
    def mocking(self):
        with responses.RequestsMock(assert_all_requests_are_fired=False) as r:
            self.apply_mockers(r)
            yield self


@contextmanager
def mocking(mocker_app: Remocker):
    with mocker_app.mocking() as app:
        yield app


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
            pattern=None,
    ):
        self.method = request.method
        self.url = request.url
        self.path = request.path_url
        self.params = request.params
        self.origin_request = request
        self.headers = request.headers
        self.pattern = pattern

    @cached_property
    def url_params(self):
        if not self.pattern:
            return {}
        matched = re.search(self.pattern, self.path)
        return matched.groupdict()

    @cached_property
    def data(self):
        return _json.loads(self.origin_request.body)


class RemockerLog:
    def __init__(self, request, response):
        self.request = request
        self.response = response
