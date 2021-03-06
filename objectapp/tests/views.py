"""Test cases for Objectapp's views"""
from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template import TemplateDoesNotExist
from django.utils.translation import ugettext_lazy as _

from objectapp.models import Gbobject
from objectapp.models import Objecttype
from objectapp.managers import PUBLISHED
from objectapp.settings import PAGINATION


class ViewsBaseCase(TestCase):
    """
    Setup and utility function base case.
    """

    def setUp(self):
        self.old_CONTEXT_PROCESSORS = settings.TEMPLATE_CONTEXT_PROCESSORS
        self.old_TEMPLATE_LOADERS = settings.TEMPLATE_LOADERS
        settings.TEMPLATE_LOADERS = (
            ('django.template.loaders.cached.Loader', (
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader',
                )
             ),
            )
        settings.TEMPLATE_CONTEXT_PROCESSORS = (
            'django.core.context_processors.request',
            )

        self.site = Site.objects.get_current()
        self.author = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='password')
        self.Objecttype = Objecttype.objects.create(title='Tests', slug='tests')
        params = {'title': 'Test 1',
                  'content': 'First test gbobject published',
                  'slug': 'test-1',
                  'tags': 'tests',
                  'creation_date': datetime(2010, 1, 1),
                  'status': PUBLISHED}
        gbobject = Gbobject.objects.create(**params)
        gbobject.sites.add(self.site)
        gbobject.objecttypes.add(self.Objecttype)
        gbobject.authors.add(self.author)

        params = {'title': 'Test 2',
                  'content': 'Second test gbobject published',
                  'slug': 'test-2',
                  'tags': 'tests',
                  'creation_date': datetime(2010, 6, 1),
                  'status': PUBLISHED}
        gbobject = Gbobject.objects.create(**params)
        gbobject.sites.add(self.site)
        gbobject.objecttypes.add(self.Objecttype)
        gbobject.authors.add(self.author)

    def tearDown(self):
        settings.TEMPLATE_CONTEXT_PROCESSORS = self.old_CONTEXT_PROCESSORS
        settings.TEMPLATE_LOADERS = self.old_TEMPLATE_LOADERS

    def create_published_gbobject(self):
        params = {'title': 'My test gbobject',
                  'content': 'My test content',
                  'slug': 'my-test-gbobject',
                  'tags': 'tests',
                  'creation_date': datetime(2010, 1, 1),
                  'status': PUBLISHED}
        gbobject = Gbobject.objects.create(**params)
        gbobject.sites.add(self.site)
        gbobject.objecttypes.add(self.Objecttype)
        gbobject.authors.add(self.author)
        return gbobject

    def check_publishing_context(self, url, first_expected,
                                 second_expected=None):
        """Test the numbers of gbobjects in context of an url,"""
        response = self.client.get(url)
        self.assertEquals(len(response.context['object_list']), first_expected)
        if second_expected:
            self.create_published_gbobject()
            response = self.client.get(url)
            self.assertEquals(
                len(response.context['object_list']), second_expected)
        return response


class ObjectappViewsTestCase(ViewsBaseCase):
    """
    Test cases for generic views used in the application,
    for reproducing and correcting issue :
    http://github.com/Fantomas42/django-blog-objectapp/issues#issue/3
    """
    urls = 'objectapp.tests.urls'

    def test_objectapp_gbobject_archive_index(self):
        self.check_publishing_context('/', 2, 3)

    def test_objectapp_gbobject_archive_year(self):
        self.check_publishing_context('/2010/', 2, 3)

    def test_objectapp_gbobject_archive_month(self):
        self.check_publishing_context('/2010/01/', 1, 2)

    def test_objectapp_gbobject_archive_day(self):
        self.check_publishing_context('/2010/01/01/', 1, 2)

    def test_objectapp_gbobject_shortlink(self):
        response = self.client.get('/1/', follow=True)
        self.assertEquals(response.redirect_chain,
                          [('http://testserver/2010/01/01/test-1/', 301)])

    def test_objectapp_gbobject_detail(self):
        gbobject = self.create_published_gbobject()
        gbobject.sites.clear()
        # Check a 404 error, but the 404.html may no exist
        try:
            self.assertRaises(TemplateDoesNotExist, self.client.get,
                              '/2010/01/01/my-test-gbobject/')
        except AssertionError:
            response = self.client.get('/2010/01/01/my-test-gbobject/')
            self.assertEquals(response.status_code, 404)

        gbobject.template = 'objectapp/_gbobject_detail.html'
        gbobject.save()
        gbobject.sites.add(Site.objects.get_current())
        response = self.client.get('/2010/01/01/my-test-gbobject/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'objectapp/_gbobject_detail.html')

    def test_objectapp_gbobject_detail_login(self):
        gbobject = self.create_published_gbobject()
        gbobject.login_required = True
        gbobject.save()
        response = self.client.get('/2010/01/01/my-test-gbobject/')
        self.assertTemplateUsed(response, 'objectapp/login.html')

    def test_objectapp_gbobject_detail_password(self):
        gbobject = self.create_published_gbobject()
        gbobject.password = 'password'
        gbobject.save()
        response = self.client.get('/2010/01/01/my-test-gbobject/')
        self.assertTemplateUsed(response, 'objectapp/password.html')
        self.assertEquals(response.context['error'], False)
        response = self.client.post('/2010/01/01/my-test-gbobject/',
                                    {'password': 'bad_password'})
        self.assertTemplateUsed(response, 'objectapp/password.html')
        self.assertEquals(response.context['error'], True)
        response = self.client.post('/2010/01/01/my-test-gbobject/',
                                    {'password': 'password'})
        self.assertEquals(response.status_code, 302)

    def test_objectapp_gbobject_channel(self):
        self.check_publishing_context('/channel-test/', 2, 3)

    def test_objectapp_Objecttype_list(self):
        self.check_publishing_context('/objecttypes/', 1)
        gbobject = Gbobject.objects.all()[0]
        gbobject.objecttypes.add(Objecttype.objects.create(title='New Objecttype',
                                                     slug='new-Objecttype'))
        self.check_publishing_context('/objecttypes/', 2)

    def test_objectapp_Objecttype_detail(self):
        response = self.check_publishing_context('/objecttypes/tests/', 2, 3)
        self.assertTemplateUsed(response, 'objectapp/Objecttype/gbobject_list.html')
        self.assertEquals(response.context['Objecttype'].slug, 'tests')

    def test_objectapp_Objecttype_detail_paginated(self):
        """Test case reproducing issue #42 on Objecttype
        detail view paginated"""
        for i in range(PAGINATION):
            params = {'title': 'My gbobject %i' % i,
                      'content': 'My content %i' % i,
                      'slug': 'my-gbobject-%i' % i,
                      'creation_date': datetime(2010, 1, 1),
                      'status': PUBLISHED}
            gbobject = Gbobject.objects.create(**params)
            gbobject.sites.add(self.site)
            gbobject.objecttypes.add(self.Objecttype)
            gbobject.authors.add(self.author)
        response = self.client.get('/objecttypes/tests/')
        self.assertEquals(len(response.context['object_list']), PAGINATION)
        response = self.client.get('/objecttypes/tests/?page=2')
        self.assertEquals(len(response.context['object_list']), 2)
        response = self.client.get('/objecttypes/tests/page/2/')
        self.assertEquals(len(response.context['object_list']), 2)
        self.assertEquals(response.context['Objecttype'].slug, 'tests')

    def test_objectapp_author_list(self):
        self.check_publishing_context('/authors/', 1)
        gbobject = Gbobject.objects.all()[0]
        gbobject.authors.add(User.objects.create(username='new-user',
                                              email='new_user@example.com'))
        self.check_publishing_context('/authors/', 2)

    def test_objectapp_author_detail(self):
        response = self.check_publishing_context('/authors/admin/', 2, 3)
        self.assertTemplateUsed(response, 'objectapp/author/gbobject_list.html')
        self.assertEquals(response.context['author'].username, 'admin')

    def test_objectapp_tag_list(self):
        self.check_publishing_context('/tags/', 1)
        gbobject = Gbobject.objects.all()[0]
        gbobject.tags = 'tests, tag'
        gbobject.save()
        self.check_publishing_context('/tags/', 2)

    def test_objectapp_tag_detail(self):
        response = self.check_publishing_context('/tags/tests/', 2, 3)
        self.assertTemplateUsed(response, 'objectapp/tag/gbobject_list.html')
        self.assertEquals(response.context['tag'].name, 'tests')

    def test_objectapp_gbobject_search(self):
        self.check_publishing_context('/search/?pattern=test', 2, 3)
        response = self.client.get('/search/?pattern=ab')
        self.assertEquals(len(response.context['object_list']), 0)
        self.assertEquals(response.context['error'],
                          _('The pattern is too short'))
        response = self.client.get('/search/')
        self.assertEquals(len(response.context['object_list']), 0)
        self.assertEquals(response.context['error'],
                          _('No pattern to search found'))

    def test_objectapp_sitemap(self):
        response = self.client.get('/sitemap/')
        self.assertEquals(len(response.context['gbobjects']), 2)
        self.assertEquals(len(response.context['objecttypes']), 1)
        gbobject = self.create_published_gbobject()
        gbobject.objecttypes.add(Objecttype.objects.create(title='New Objecttype',
                                                     slug='new-Objecttype'))
        response = self.client.get('/sitemap/')
        self.assertEquals(len(response.context['gbobjects']), 3)
        self.assertEquals(len(response.context['objecttypes']), 2)

    def test_objectapp_trackback(self):
        # Check a 404 error, but the 404.html may no exist
        try:
            self.assertRaises(TemplateDoesNotExist, self.client.post,
                              '/trackback/404/')
        except AssertionError:
            response = self.client.post('/trackback/404/')
            self.assertEquals(response.status_code, 404)
        self.assertEquals(
            self.client.post('/trackback/1/').status_code, 301)
        self.assertEquals(
            self.client.get('/trackback/1/').status_code, 301)
        gbobject = Gbobject.objects.get(slug='test-1')
        gbobject.pingback_enabled = False
        gbobject.save()
        self.assertEquals(
            self.client.post('/trackback/1/',
                             {'url': 'http://example.com'}).content,
            '<?xml version="1.0" encoding="utf-8"?>\n<response>\n  \n  '
            '<error>1</error>\n  <message>Trackback is not enabled for '
            'Test 1</message>\n  \n</response>\n')
        gbobject.pingback_enabled = True
        gbobject.save()
        self.assertEquals(
            self.client.post('/trackback/1/',
                             {'url': 'http://example.com'}).content,
            '<?xml version="1.0" encoding="utf-8"?>\n<response>\n  \n  '
            '<error>0</error>\n  \n</response>\n')
        self.assertEquals(
            self.client.post('/trackback/1/',
                             {'url': 'http://example.com'}).content,
            '<?xml version="1.0" encoding="utf-8"?>\n<response>\n  \n  '
            '<error>1</error>\n  <message>Trackback is already registered'
            '</message>\n  \n</response>\n')


class ObjectappCustomDetailViews(ViewsBaseCase):
    """
    Tests with an alternate urls.py that modifies how author_detail,
    tags_detail and objecttypes_detail views to be called with a custom
    template_name keyword argument and an extra_context.
    """
    urls = 'objectapp.tests.custom_views_detail_urls'

    def test_custom_Objecttype_detail(self):
        response = self.check_publishing_context('/objecttypes/tests/', 2, 3)
        self.assertTemplateUsed(response, 'objectapp/gbobject_list.html')
        self.assertEquals(response.context['Objecttype'].slug, 'tests')
        self.assertEquals(response.context['extra'], 'context')

    def test_custom_author_detail(self):
        response = self.check_publishing_context('/authors/admin/', 2, 3)
        self.assertTemplateUsed(response, 'objectapp/gbobject_list.html')
        self.assertEquals(response.context['author'].username, 'admin')
        self.assertEquals(response.context['extra'], 'context')

    def test_custom_tag_detail(self):
        response = self.check_publishing_context('/tags/tests/', 2, 3)
        self.assertTemplateUsed(response, 'objectapp/gbobject_list.html')
        self.assertEquals(response.context['tag'].name, 'tests')
        self.assertEquals(response.context['extra'], 'context')
