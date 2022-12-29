from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.v1.routes import router
from db.pg_core_connect import CustomDbError

client = TestClient(router)


def connect_error(*args):
    raise CustomDbError('hoho')


def create_link_mock(*args, **kwargs):
    return 1


def get_short_url_mock(*args, **kwargs):
    return [{'url_id': 'ab12', 'original_url': 'https://prakticum.yandex.ru', 'active': 1}]


def get_short_url_not_active_mock(*args, **kwargs):
    return [{'url_id': 'ab12', 'original_url': 'https://prakticum.yandex.ru', 'active': 0}]


def get_stats_mock(*args, **kwargs):
    return [{'ulr_id': 'ab12', 'count': 123}]


class TestApi(TestCase):

    def test_health(self):
        resp_ = client.get('/health')
        resp_data: dict = resp_.json()

        self.assertEqual('up', resp_data.get('status'))

    def test_ping(self):
        with patch('api.v1.routes.DbService._execute') as mock:
            mock.return_value = ['one_shcema', 'other_schema']

            resp_ = client.get('/ping')
            resp_data: dict = resp_.json()
            self.assertEqual(200, resp_.status_code)
            self.assertTrue('true', resp_data.get('db_connection'))

    def test_ping_not_connect(self):
        with patch('api.v1.routes.DbService._execute') as db_mock:
            db_mock.side_effect = connect_error

            resp_ = client.get('/ping')
            resp_data: dict = resp_.json()

            self.assertTrue('false', resp_data.get('db_connection'))

    def test_create_short_link(self):
        with patch('api.v1.routes.DbService._execute') as db_mock:
            db_mock.side_effect = create_link_mock
            resp_ = client.post('/', json={'original_link': 'https://prakticum.yandex.ru'})

            self.assertEqual(201, resp_.status_code)

    def test_redirect_by_short_url(self):
        with patch('api.v1.routes.DbService._execute') as db_mock:
            db_mock.side_effect = get_short_url_mock
            resp_ = client.get('/ab12', allow_redirects=False)

            self.assertEqual(307, resp_.status_code)

    def test_redicrtect_not_acitve(self):
        with patch('api.v1.routes.DbService._execute') as db_mock:
            with self.assertRaises(HTTPException):
                db_mock.side_effect = get_short_url_not_active_mock
                client.get('/ab12', allow_redirects=False)

    def test_deactivate_url(self):
        with patch('api.v1.routes.DbService._execute') as db_mock:
            db_mock.side_effect = create_link_mock
            resp_ = client.delete('/ab12')

            self.assertEqual(200, resp_.status_code)

    def test_statistics(self):
        with patch('api.v1.routes.DbService._execute') as db_mock:
            db_mock.side_effect = get_stats_mock
            resp_ = client.get('/ab12/status')
            resp_data: dict = resp_.json()

            self.assertEqual(200, resp_.status_code)
            self.assertEqual('ab12', resp_data.get('url_id'))
