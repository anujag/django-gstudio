"""Test cases for Objectapp's url_shortener"""
from __future__ import with_statement
import warnings

from django.test import TestCase

from objectapp.url_shortener import get_url_shortener
from objectapp import url_shortener as us_settings
from objectapp.url_shortener.backends.default import backend as default_backend


class URLShortenerTestCase(TestCase):
    """Test cases for objectapp.url_shortener"""

    def setUp(self):
        self.original_backend = us_settings.URL_SHORTENER_BACKEND

    def tearDown(self):
        us_settings.URL_SHORTENER_BACKEND = self.original_backend

    def test_get_url_shortener(self):
        us_settings.URL_SHORTENER_BACKEND = 'mymodule.myclass'
        try:
            with warnings.catch_warnings(record=True) as w:
                self.assertEquals(get_url_shortener(), default_backend)
                self.assertTrue(issubclass(w[-1].Objecttype, RuntimeWarning))
                self.assertEquals(
                    str(w[-1].message),
                    'mymodule.myclass backend cannot be imported')
        except AttributeError:
            # Fail under Python2.5, because of'warnings.catch_warnings'
            pass

        us_settings.URL_SHORTENER_BACKEND = 'objectapp.tests.custom_url_shortener'
        try:
            with warnings.catch_warnings(record=True) as w:
                self.assertEquals(get_url_shortener(), default_backend)
                self.assertTrue(issubclass(w[-1].Objecttype, RuntimeWarning))
                self.assertEquals(
                    str(w[-1].message),
                    'This backend only exists for testing')
        except AttributeError:
            # Fail under Python2.5, because of'warnings.catch_warnings'
            pass

        us_settings.URL_SHORTENER_BACKEND = 'objectapp.url_shortener'\
                                            '.backends.default'
        self.assertEquals(get_url_shortener(), default_backend)
