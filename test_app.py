import unittest
from unittest.mock import patch, MagicMock
from app import app
from flask import session


class FlaskAppTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app
        self.client = self.app.test_client()

    @patch('app.mysql')
    def test_login_success(self, mock_mysql):
        with self.app.app_context():
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                'idusers': 1,
                'login': 'testuser',
                'password': 'testpass'
            }
            mock_mysql.connection.cursor.return_value.__enter__.return_value = mock_cursor

            response = self.client.post('/login', data={
                'login': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Календарь', response.data.decode('utf-8'))  # Или другой реальный текст

    @patch('app.mysql')
    def test_login_fail(self, mock_mysql):
        with self.app.app_context():
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_mysql.connection.cursor.return_value.__enter__.return_value = mock_cursor

            response = self.client.post('/login', data={
                'login': 'wronguser',
                'password': 'wrongpass'
            }, follow_redirects=True)

            self.assertIn('Неправильный логин или пароль!', response.data.decode('utf-8'))

    @patch('app.mysql')
    def test_add_event(self, mock_mysql):
        with self.app.app_context():
            mock_cursor = MagicMock()
            mock_mysql.connection.cursor.return_value.__enter__.return_value = mock_cursor

            with self.client.session_transaction() as sess:
                sess['loggedin'] = True
                sess['idusers'] = 1

            response = self.client.post('/add_event', data={
                'event_name': 'Test Event',
                'event_date': '2025-04-20',
                'description': 'Test description',
                'location': 'Test location'
            })

            self.assertEqual(response.status_code, 302)
            self.assertIn('/calendar', response.location)

    @patch('smtplib.SMTP')
    def test_send_email(self, mock_smtp):
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                sess['loggedin'] = True
                sess['idusers'] = 1
                sess['login'] = 'testuser'

            response = self.client.post('/send_email', data={
                'subject': 'Тест',
                'message': 'Сообщение',
                'recipient': 'test@example.com'
            }, follow_redirects=True)

            self.assertTrue(mock_smtp.return_value.sendmail.called)
            self.assertIn('Письмо успешно отправлено!', response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
