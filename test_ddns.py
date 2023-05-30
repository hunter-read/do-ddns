import unittest
from unittest.mock import patch, MagicMock
import requests
import os
import logging
from io import StringIO
from ddns import (
    get_ip,
    get_ipv4,
    get_ipv6,
    get_subdomain_data,
    update_record,
)


class TestDDNS(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("ddns")
        self.logger.setLevel(logging.DEBUG)
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(
            logging.Formatter(
                "%(levelname)s:%(asctime)s: %(message)s", "%Y-%m-%d %H:%M:%S"
            )
        )
        self.logger.addHandler(self.handler)
        self.api_key = "test_api_key"
        self.headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
        }
        self.domain = "test.com"
        self.subdomains = ["www.test.com", "mail.test.com"]
        self.current_dns = {
            "www.test.com": (
                {"id": 1, "type": "A", "name": "www", "data": "1.2.3.4"},
                {
                    "id": 2,
                    "type": "AAAA",
                    "name": "www",
                    "data": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
                },
            ),
            "mail.test.com": (
                {"id": 3, "type": "A", "name": "mail", "data": "1.2.3.5"},
                None,
            ),
        }

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        del self.handler
        del self.logger
        del self.stream

    def test_get_ip(self):
        # Test successful response
        with patch.object(requests, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "1.2.3.4"
            mock_get.return_value = mock_response
            self.assertEqual(get_ip("http://test.com"), "1.2.3.4")

        # Test unsuccessful response
        with patch.object(requests, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException
            self.assertIsNone(get_ip("http://test.com"))

    def test_get_ipv4(self):
        # Test successful response
        with patch.dict(os.environ, {"IPV4_SERVER": "http://test.com"}):
            with patch.object(requests, "get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = "1.2.3.4"
                mock_get.return_value = mock_response
                self.assertEqual(get_ipv4(), "1.2.3.4")

        # Test unsuccessful response
        with patch.dict(os.environ, {"IPV4_SERVER": "http://test.com"}):
            with patch.object(requests, "get") as mock_get:
                mock_get.side_effect = requests.exceptions.RequestException
                self.assertIsNone(get_ipv4())

    def test_get_ipv6(self):
        # Test successful response
        with patch.dict(os.environ, {"IPV6_SERVER": "http://test.com"}):
            with patch.object(requests, "get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
                mock_get.return_value = mock_response
                self.assertEqual(get_ipv6(), "2001:0db8:85a3:0000:0000:8a2e:0370:7334")

        # Test unsuccessful response
        with patch.dict(os.environ, {"IPV6_SERVER": "http://test.com"}):
            with patch.object(requests, "get") as mock_get:
                mock_get.side_effect = requests.exceptions.RequestException
                self.assertIsNone(get_ipv6())

    def test_get_subdomain_data(self):
        # Test successful response
        with patch.object(requests, "get") as mock_get:
            mock_response_www = MagicMock()
            mock_response_www.status_code = 200
            mock_response_www.json.return_value = {
                "domain_records": [
                    {"id": 1, "type": "A", "name": "www", "data": "1.2.3.4"},
                    {
                        "id": 2,
                        "type": "AAAA",
                        "name": "www",
                        "data": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
                    },
                ]
            }

            mock_response_mail = MagicMock()
            mock_response_mail.status_code = 200
            mock_response_mail.json.return_value = {
                "domain_records": [
                    {"id": 3, "type": "A", "name": "mail", "data": "1.2.3.5"},
                ]
            }

            mock_get.side_effect = [
                mock_response_www,
                mock_response_mail,
            ]

            self.assertEqual(
                get_subdomain_data(self.domain, self.subdomains, self.headers),
                self.current_dns,
            )

    def test_update_record(self):
        # Test successful create
        with patch.object(requests, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_post.return_value = mock_response
            self.assertTrue(
                update_record(
                    self.domain, "www.test.com", None, "1.2.3.4", "A", self.headers
                )
            )
            self.assertIn(
                "Successfully created A record for www.test.com with ip 1.2.3.4",
                self.stream.getvalue().strip(),
            )

        # Test unsuccessful create
        with patch.object(requests, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_post.return_value = mock_response
            self.assertFalse(
                update_record(
                    self.domain, "www.test.com", None, "1.2.3.4", "A", self.headers
                )
            )
            self.assertIn(
                "Unable to create A record for www.test.com",
                self.stream.getvalue().strip(),
            )

        # Test successful update
        with patch.object(requests, "patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_patch.return_value = mock_response
            self.assertTrue(
                update_record(
                    self.domain,
                    "www.test.com",
                    self.current_dns["www.test.com"][0],
                    "1.2.3.5",
                    "A",
                    self.headers,
                )
            )
            self.assertIn(
                "Successfully updated A record for www.test.com to 1.2.3.5",
                self.stream.getvalue().strip(),
            )

        # Test unsuccessful update
        with patch.object(requests, "patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_patch.return_value = mock_response
            self.assertFalse(
                update_record(
                    self.domain,
                    "www.test.com",
                    self.current_dns["www.test.com"][0],
                    "1.2.3.5",
                    "A",
                    self.headers,
                )
            )
            self.assertIn(
                "Unable to update A record for www.test.com",
                self.stream.getvalue().strip(),
            )

        # Test no update
        self.assertFalse(
            update_record(
                self.domain,
                "www.test.com",
                self.current_dns["www.test.com"][0],
                "1.2.3.4",
                "A",
                self.headers,
            )
        )


if __name__ == "__main__":
    unittest.main()
