import inspect
import json
import re

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


class RemockerClient:
    base_url = None

    GET = httpretty.GET
    PUT = httpretty.PUT
    POST = httpretty.POST
    DELETE = httpretty.DELETE
    HEAD = httpretty.HEAD
    PATCH = httpretty.PATCH
    OPTIONS = httpretty.OPTIONS

    request_log = []
    storages = {}

    def get_storage(self, key, default=None):
        return self.storages.get(key, default)

    def set_storage(self, key, value):
        self.storages[key] = value

    @staticmethod
    def dumps(body):
        return json.dumps(body)

    @staticmethod
    def loads(body):
        return json.loads(body)

    def register_uri(self, method, uri, body, regex=False, *args, **kwargs):
        if not callable(body):
            body = self.dumps(body)

        if type(uri) is str:
            uri = self.get_full_uri(uri)

        if regex:
            uri = re.compile(uri)

        return httpretty.register_uri(method, uri, body, *args, **kwargs)

    def get_base_url(self):
        return self.base_url

    def get_full_uri(self, uri):
        if not uri.startswith('http'):
            return join_path(self.get_base_url(), uri)
        return uri

    def get_uri_params(self, uri, pattern):
        if type(pattern) in (str, bytes):
            pattern = re.compile(pattern)
        return re.search(pattern, uri)

    def get_mocking_methods(self):
        results = []
        for key, value in inspect.getmembers(self):
            if not callable(value):
                continue
            if key.startswith('mock_'):
                results.append(value)

        return results

    @classmethod
    def clear(cls):
        cls.request_log = []
        cls.storages = {}

    @classmethod
    def mocking(cls):
        instance = cls()
        for mocker in instance.get_mocking_methods():
            mocker()
        cls.clear()
        return instance


def mocker_callback(instance):
    def decorator(func):
        def inner(request, uri, response_headers):
            instance.request_log.append(uri)
            results = func(request, uri, response_headers)

            if not results:
                return 200, response_headers, '{}'
            if type(results) is not tuple:
                return 200, response_headers, results
            result_len = len(results)

            if result_len == 1:
                return 200, response_headers, results[0]
            elif result_len == 2:
                return results[0], response_headers, results[1]
            elif result_len == 3:
                return results

        return inner

    return decorator


class mocking:
    def __init__(self, mocker, allow_net_connect=False, verbose=False):
        self.mocker_class = mocker
        self.mocker = mocker()
        self.allow_net_connect = allow_net_connect
        self.verbose = verbose

    def __enter__(self):
        httpretty.reset()
        httpretty.enable(allow_net_connect=self.allow_net_connect, verbose=self.verbose)
        self.mocker.mocking()
        return self.mocker

    def __exit__(self, exc_type, exc_val, exc_tb):
        httpretty.disable()
        httpretty.reset()
