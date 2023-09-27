# remocker

mocking http request more easy

## installing

```shell
pip install remocker
```

## How to use

First, you define Remocker app.

```python
from remocker import Remocker, RemockerRequest, RemockerResponse

mocker_app = Remocker('https://api.test.com')

@mocker_app.mock(method='GET', path='products')
def get_products_mocker(request: RemockerRequest):
    return RemockerResponse({
        'success': True,
        'given_params': request.query_params,
    })

@mocker_app.mock(method='POST', path='products')
def create_product_mocker(request: RemockerRequest):
    return RemockerResponse({
        'success': True,
        'given_data': request.data,
    })

@mocker_app.mock(method='GET', path=r'products/(?P<product_id>\d+)', regex=True)
def get_product_mocker(request: RemockerRequest):
    return RemockerResponse({
        'success': True,
        'given_product_id': request.url_params['product_id'],
    })
```

Next, you can use `mocking` context manager.

```python
import requests

with mocker_app.mocking():
    requests.get('https://api.test.com/products', params={'foo': 'var'})
    # Remocker only allow json request. Not form data
    requests.post('https://api.test.com/products', json={'foo': 'var'})
    requests.get('https://api.test.com/products/1')


# Also can
import remocker

with remocker.mocking(mocker_app):
    ...
```
