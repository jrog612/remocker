from unittest import TestCase

import requests

from remocker import Remocker, RemockerResponse, join_path

BASE_URL = 'https://test.com/base'
mocker_app = Remocker(BASE_URL)


@mocker_app.mock(method='GET', path='products')
def get_products_mocker(request):
    response = RemockerResponse({
        'success': True,
        'given_params': request.query_params,
    })
    return response


@mocker_app.mock(method='POST', path='products')
def create_product_mocker(request):
    response = RemockerResponse({
        'success': True,
        'given_data': request.data,
    })
    return response


@mocker_app.mock(method='GET', path=r'products/(?P<product_id>\d+)', regex=True)
def get_product_mocker(request):
    response = RemockerResponse({
        'success': True,
        'given_product_id': request.url_params['product_id'],
    })
    return response


class RemockerTestCase(TestCase):
    def test_mocking(self):
        with mocker_app.mocking():
            response = requests.get(join_path(BASE_URL, 'products'), params={
                'foo': 'var',
                'foos': [
                    'var', 'var', 'var'
                ],
            })
            response = requests.post(join_path(BASE_URL, 'products'), json={
                'foo': 'var'
            })
            response = requests.get(join_path(BASE_URL, 'products/1'))
