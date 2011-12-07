"""XML-RPC methods of Gstudio metaWeblog API"""
import os
from datetime import datetime
from xmlrpclib import Fault
from xmlrpclib import DateTime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.translation import gettext as _
from django.utils.html import strip_tags
from django.utils.text import truncate_words
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.defaultfilters import slugify

from gstudio.models import Nodetype
from gstudio.models import Metatype
from gstudio.settings import PROTOCOL
from gstudio.settings import UPLOAD_TO
from gstudio.managers import DRAFT, PUBLISHED
from django_xmlrpc.decorators import xmlrpc_func

# http://docs.nucleuscms.org/blog/12#errorcodes
LOGIN_ERROR = 801
PERMISSION_DENIED = 803


def authenticate(username, password, permission=None):
    """Authenticate staff_user with permission"""
    try:
        user = User.objects.get(username__exact=username)
    except User.DoesNotExist:
        raise Fault(LOGIN_ERROR, _('Username is incorrect.'))
    if not user.check_password(password):
        raise Fault(LOGIN_ERROR, _('Password is invalid.'))
    if not user.is_staff or not user.is_active:
        raise Fault(PERMISSION_DENIED, _('User account unavailable.'))
    if permission:
        if not user.has_perm(permission):
            raise Fault(PERMISSION_DENIED, _('User cannot %s.') % permission)
    return user


def blog_structure(site):
    """A blog structure"""
    return {'url': '%s://%s%s' % (
        PROTOCOL, site.domain, reverse('gstudio_nodetype_archive_index')),
            'blogid': settings.SITE_ID,
            'blogName': site.name}


def user_structure(user, site):
    """An user structure"""
    return {'userid': user.pk,
            'email': user.email,
            'nickname': user.username,
            'lastname': user.last_name,
            'firstname': user.first_name,
            'url': '%s://%s%s' % (
                PROTOCOL, site.domain,
                reverse('gstudio_author_detail', args=[user.username]))}


def author_structure(user):
    """An author structure"""
    return {'user_id': user.pk,
            'user_login': user.username,
            'display_name': user.username,
            'user_email': user.email}


def metatype_structure(metatype, site):
    """A metatype structure"""
    return {'description': metatype.title,
            'htmlUrl': '%s://%s%s' % (
                PROTOCOL, site.domain,
                metatype.get_absolute_url()),
            'rssUrl': '%s://%s%s' % (
                PROTOCOL, site.domain,
                reverse('gstudio_metatype_feed', args=[metatype.tree_path])),
            # Useful Wordpress Extensions
            'metatypeId': metatype.pk,
            'parentId': metatype.parent and metatype.parent.pk or 0,
            'metatypeDescription': metatype.description,
            'metatypeName': metatype.title}


def post_structure(nodetype, site):
    """A post structure with extensions"""
    author = nodetype.authors.all()[0]
    return {'title': nodetype.title,
            'description': unicode(nodetype.html_content),
            'link': '%s://%s%s' % (PROTOCOL, site.domain,
                                   nodetype.get_absolute_url()),
            # Basic Extensions
            'permaLink': '%s://%s%s' % (PROTOCOL, site.domain,
                                        nodetype.get_absolute_url()),
            'metatypes': [cat.title for cat in nodetype.metatypes.all()],
            'dateCreated': DateTime(nodetype.creation_date.isoformat()),
            'postid': nodetype.pk,
            'userid': author.username,
            # Useful Movable Type Extensions
            'mt_excerpt': nodetype.excerpt,
            'mt_allow_comments': int(nodetype.comment_enabled),
            'mt_allow_pings': int(nodetype.pingback_enabled),
            'mt_keywords': nodetype.tags,
            # Useful Wordpress Extensions
            'wp_author': author.username,
            'wp_author_id': author.pk,
            'wp_author_display_name': author.username,
            'wp_password': nodetype.password,
            'wp_slug': nodetype.slug,
            'sticky': nodetype.featured}


@xmlrpc_func(returns='struct[]', args=['string', 'string', 'string'])
def get_users_blogs(apikey, username, password):
    """blogger.getUsersBlogs(api_key, username, password)
    => blog structure[]"""
    authenticate(username, password)
    site = Site.objects.get_current()
    return [blog_structure(site)]


@xmlrpc_func(returns='struct', args=['string', 'string', 'string'])
def get_user_info(apikey, username, password):
    """blogger.getUserInfo(api_key, username, password)
    => user structure"""
    user = authenticate(username, password)
    site = Site.objects.get_current()
    return user_structure(user, site)


@xmlrpc_func(returns='struct[]', args=['string', 'string', 'string'])
def get_authors(apikey, username, password):
    """wp.getAuthors(api_key, username, password)
    => author structure[]"""
    authenticate(username, password)
    return [author_structure(author)
            for author in User.objects.filter(is_staff=True)]


@xmlrpc_func(returns='boolean', args=['string', 'string',
                                      'string', 'string', 'string'])
def delete_post(apikey, post_id, username, password, publish):
    """blogger.deletePost(api_key, post_id, username, password, 'publish')
    => boolean"""
    user = authenticate(username, password, 'gstudio.delete_nodetype')
    nodetype = Nodetype.objects.get(id=post_id, authors=user)
    nodetype.delete()
    return True


@xmlrpc_func(returns='struct', args=['string', 'string', 'string'])
def get_post(post_id, username, password):
    """metaWeblog.getPost(post_id, username, password)
    => post structure"""
    user = authenticate(username, password)
    site = Site.objects.get_current()
    return post_structure(Nodetype.objects.get(id=post_id, authors=user), site)


@xmlrpc_func(returns='struct[]',
             args=['string', 'string', 'string', 'integer'])
def get_recent_posts(blog_id, username, password, number):
    """metaWeblog.getRecentPosts(blog_id, username, password, number)
    => post structure[]"""
    user = authenticate(username, password)
    site = Site.objects.get_current()
    return [post_structure(nodetype, site) \
            for nodetype in Nodetype.objects.filter(authors=user)[:number]]


@xmlrpc_func(returns='struct[]', args=['string', 'string', 'string'])
def get_metatypes(blog_id, username, password):
    """metaWeblog.getMetatypes(blog_id, username, password)
    => metatype structure[]"""
    authenticate(username, password)
    site = Site.objects.get_current()
    return [metatype_structure(metatype, site) \
            for metatype in Metatype.objects.all()]


@xmlrpc_func(returns='string', args=['string', 'string', 'string', 'struct'])
def new_metatype(blog_id, username, password, metatype_struct):
    """wp.newMetatype(blog_id, username, password, metatype)
    => metatype_id"""
    authenticate(username, password, 'gstudio.add_metatype')
    metatype_dict = {'title': metatype_struct['name'],
                     'description': metatype_struct['description'],
                     'slug': metatype_struct['slug']}
    if int(metatype_struct['parent_id']):
        metatype_dict['parent'] = Metatype.objects.get(
            pk=metatype_struct['parent_id'])
    metatype = Metatype.objects.create(**metatype_dict)

    return metatype.pk


@xmlrpc_func(returns='string', args=['string', 'string', 'string',
                                     'struct', 'boolean'])
def new_post(blog_id, username, password, post, publish):
    """metaWeblog.newPost(blog_id, username, password, post, publish)
    => post_id"""
    user = authenticate(username, password, 'gstudio.add_nodetype')
    if post.get('dateCreated'):
        creation_date = datetime.strptime(
            post['dateCreated'].value.replace('Z', '').replace('-', ''),
            '%Y%m%dT%H:%M:%S')
    else:
        creation_date = datetime.now()

    nodetype_dict = {'title': post['title'],
                  'content': post['description'],
                  'excerpt': post.get('mt_excerpt', truncate_words(
                      strip_tags(post['description']), 50)),
                  'creation_date': creation_date,
                  'last_update': creation_date,
                  'comment_enabled': post.get('mt_allow_comments', 1) == 1,
                  'pingback_enabled': post.get('mt_allow_pings', 1) == 1,
                  'featured': post.get('sticky', 0) == 1,
                  'tags': 'mt_keywords' in post and post['mt_keywords'] or '',
                  'slug': 'wp_slug' in post and post['wp_slug'] or slugify(
                      post['title']),
                  'password': post.get('wp_password', ''),
                  'status': publish and PUBLISHED or DRAFT}
    nodetype = Nodetype.objects.create(**nodetype_dict)

    author = user
    if 'wp_author_id' in post and user.has_perm('gstudio.can_change_author'):
        if int(post['wp_author_id']) != user.pk:
            author = User.objects.get(pk=post['wp_author_id'])
    nodetype.authors.add(author)

    nodetype.sites.add(Site.objects.get_current())
    if 'metatypes' in post:
        nodetype.metatypes.add(*[Metatype.objects.get_or_create(
            title=cat, slug=slugify(cat))[0]
                               for cat in post['metatypes']])

    return nodetype.pk


@xmlrpc_func(returns='boolean', args=['string', 'string', 'string',
                                      'struct', 'boolean'])
def edit_post(post_id, username, password, post, publish):
    """metaWeblog.editPost(post_id, username, password, post, publish)
    => boolean"""
    user = authenticate(username, password, 'gstudio.change_nodetype')
    nodetype = Nodetype.objects.get(id=post_id, authors=user)
    if post.get('dateCreated'):
        creation_date = datetime.strptime(
            post['dateCreated'].value.replace('Z', '').replace('-', ''),
            '%Y%m%dT%H:%M:%S')
    else:
        creation_date = nodetype.creation_date

    nodetype.title = post['title']
    nodetype.content = post['description']
    nodetype.excerpt = post.get('mt_excerpt', truncate_words(
        strip_tags(post['description']), 50))
    nodetype.creation_date = creation_date
    nodetype.last_update = datetime.now()
    nodetype.comment_enabled = post.get('mt_allow_comments', 1) == 1
    nodetype.pingback_enabled = post.get('mt_allow_pings', 1) == 1
    nodetype.featured = post.get('sticky', 0) == 1
    nodetype.tags = 'mt_keywords' in post and post['mt_keywords'] or ''
    nodetype.slug = 'wp_slug' in post and post['wp_slug'] or slugify(
        post['title'])
    nodetype.status = publish and PUBLISHED or DRAFT
    nodetype.password = post.get('wp_password', '')
    nodetype.save()

    if 'wp_author_id' in post and user.has_perm('gstudio.can_change_author'):
        if int(post['wp_author_id']) != user.pk:
            author = User.objects.get(pk=post['wp_author_id'])
            nodetype.authors.clear()
            nodetype.authors.add(author)

    if 'metatypes' in post:
        nodetype.metatypes.clear()
        nodetype.metatypes.add(*[Metatype.objects.get_or_create(
            title=cat, slug=slugify(cat))[0]
                               for cat in post['metatypes']])
    return True


@xmlrpc_func(returns='struct', args=['string', 'string', 'string', 'struct'])
def new_media_object(blog_id, username, password, media):
    """metaWeblog.newMediaObject(blog_id, username, password, media)
    => media structure"""
    authenticate(username, password)
    path = default_storage.save(os.path.join(UPLOAD_TO, media['name']),
                                ContentFile(media['bits'].data))
    return {'url': default_storage.url(path)}
