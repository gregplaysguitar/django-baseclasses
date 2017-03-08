# coding: utf8

"""A collection of mixins and associated utilities for django models.

"""

import datetime

import django
from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property

from .util import next_or_prev_in_order


PREVIEW_FLAG = 'preview'


class DateAuditModel(models.Model):
    """Extend this class to get a record of when your model was created and
       last changed."""

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def get_prev(self, qs=None, loop=False):
        return next_or_prev_in_order(self, True, qs, loop)

    def get_next(self, qs=None, loop=False):
        return next_or_prev_in_order(self, False, qs, loop)

    class Meta:
        abstract = True
        ordering = ('-created',)


class ContentModelQuerySet(models.QuerySet):
    def live(self, request=None):
        """If request is passed, and a preview flag is in request.GET,
           then check if the user is a staff member, and return all objects
           if so. Otherwise, return only live objects.

           Note, django doesn't allow view caching on any request that accesses
           request.user, so this must ONLY happen if the preview flag is
           present. Otherwise, the view can never be cached. """

        if request and request.GET.get(PREVIEW_FLAG) and request.user.is_staff:
            return self

        return self.filter(is_live=True,
                           pub_date__lte=datetime.datetime.now())


def default_manager_from_qs(QuerySet, **kwargs):
    """Sets base manager in django < 1.10. This is obsolete in 1.10+ and will
       trigger a warning. """

    related = kwargs.pop('use_for_related_fields', True)

    class _Manager(models.Manager.from_queryset(QuerySet)):
        use_for_related_fields = related

    return _Manager


if django.VERSION < (1, 10):
    ContentModelManager = default_manager_from_qs(ContentModelQuerySet)
else:
    ContentModelManager = models.Manager.from_queryset(ContentModelQuerySet)


class BaseContentModel(DateAuditModel):
    """Provides managers for 'live' instances, based on the is_live &
       pub_date fields. Also provides next/prev instance methods
       for all objects and just live objects, respecting the value of
       Meta.ordering."""

    pub_date = models.DateField(u'publication date', db_index=True,
                                default=datetime.date.today)
    is_live = models.BooleanField(
        db_index=True,
        default=getattr(settings, 'IS_LIVE_DEFAULT', 1),
        help_text="This must be ticked, and 'publication date' must "
                  "not be in the future, for the item to show on the site.")

    objects = ContentModelManager()

    @property
    def live(self):
        return self.is_live and self.pub_date <= datetime.date.today()

    class Meta(DateAuditModel.Meta):
        abstract = True
        ordering = ('-pub_date', '-created',)

    def prev_live(self, loop=False):
        return self.get_prev(self.__class__.objects.live(), loop)

    def next_live(self, loop=False):
        return self.get_next(self.__class__.objects.live(), loop)


class BaseSortedModel(models.Model):
    """Provides a sort_order field and orders on it by default."""

    sort_order = models.IntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ('sort_order', 'id')


class BaseModelWithImages(models.Model):
    """Basic model for use with related images (needs a related Image model
       with the related_name 'image_set'). Provides primary_image method.

       Example implementation:

       class Article(BaseModelWithImages):
           ...

       class ArticleImage(BaseImageModel;):
           article = models.ForeignKey(Article, related_name='image_set', on_delete=models.CASCADE)

       >>> Article.objects.get(...).primary_image()"""

    class Meta:
        abstract = True

    @cached_property
    def primary_image(self):
        try:
            return self.image_set.all()[0]
        except IndexError:
            return None


@python_2_unicode_compatible
class BaseImageModel(BaseSortedModel):
    """Use this in conjunction with BaseModelWithImages or
       BaseContentModelWithImages.

       For an example see the BaseModelWithImages docstring."""

    image = models.ImageField(upload_to=settings.UPLOAD_PATH)
    caption = models.TextField(default='', blank=True)

    def __str__(self):
        return self.caption or (u'Image: %s' % self.image)

    class Meta(BaseSortedModel.Meta):
        abstract = True
        ordering = BaseSortedModel.Meta.ordering + ('caption',)


class BaseHierarchyModel(models.Model):
    """Provides a simple hierarchy system, useful when categories and
       subcategories are needed. Provides get_hierarchy method, which is
       primarily useful for getting the top level category for a given
       category, eg

       >>> category.get_hierarchy()[0]

       Currently only 2 levels are supported."""

    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children',
                               on_delete=models.CASCADE,
                               limit_choices_to={'parent__isnull': True})

    def get_parent_display(self):
        return self.parent or ''

    get_parent_display.short_description = 'parent'
    get_parent_display.admin_order_field = 'parent'

    def get_hierarchy(self, include_self=True):
        if self.parent:
            return self.parent.get_hierarchy() + \
                (include_self and [self] or [])
        else:
            return include_self and [self] or []

    class Meta:
        abstract = True


def check_tree(sender, **kwargs):
    if isinstance(kwargs['instance'], BaseHierarchyModel):
        if kwargs['instance'].pk and kwargs['instance'].children.all().count() \
                or kwargs['instance'].parent == kwargs['instance']:
            kwargs['instance'].parent = None
models.signals.pre_save.connect(check_tree)
