from unittest import TestCase

import requests
import responses

from remocker import Remocker, RemockerResponse, join_path

BASE_URL = 'https://test.com/base'
mocker_app = Remocker(BASE_URL)

def _check_header(request):
    assert request.headers['x-test'] == 'test-header'

@mocker_app.mock(method='GET', path='products')
def get_products_mocker(request):
    _check_header(request)
    response = RemockerResponse({
        'success': True,
        'given_params': request.params,
    })
    return response


@mocker_app.mock(method='POST', path='products')
def create_product_mocker(request):
    _check_header(request)
    response = RemockerResponse({
        'success': True,
        'given_data': request.data,
    })
    return response


@mocker_app.mock(method='GET', path=r'products/(?P<product_id>\d+)', regex=True)
def get_product_mocker(request):
    _check_header(request)
    response = RemockerResponse({
        'success': True,
        'given_product_id': request.url_params['product_id'],
    })
    return response


class RemockerTestCase(TestCase):
    def test_my_api(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://twitter.com/api/1/foobar",
                body="{}",
                status=200,
                content_type="application/json",
            )
            resp = requests.get("http://twitter.com/api/1/foobar")

            assert resp.status_code == 200


    def test_mocking(self):
        headers = {
            'x-test': 'test-header'
        }

        with mocker_app.mocking():
            requests.get(join_path(BASE_URL, 'products'), params={
                'foo': 'var',
                'foos': [
                    'var', 'var', 'var'
                ],
            }, headers=headers)
            requests.post(join_path(BASE_URL, 'products'), json={
                'foo': 'var'
            }, headers=headers)
            requests.get(join_path(BASE_URL, 'products/1'), headers=headers)
