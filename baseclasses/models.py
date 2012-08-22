"""A collection of mixins and associated utilities for django models.

BaseContentModel
BaseNamedModel
DateAuditModel
BaseSortedModel
BaseContentModelWithImages
BaseImageModel
BaseSortedModeL
BaseHierarchyModel
"""

from django.db import models
import datetime
from django.conf import settings
from fields import ConstrainedImageField
from util import next_or_prev_in_order

__all__ = (
    'BaseContentModel',
    'BaseNamedModel',
    'DateAuditModel',
    'BaseContentModelWithImages',
    'BaseImageModel',
    'BaseSortedModel',
    'BaseHierarchyModel',
)


class DateAuditModel(models.Model):
    """Extend this class to get a record of when your model was created and last changed."""
    
    creation_date = models.DateTimeField(editable=False)
    last_updated = models.DateTimeField(editable=False)
    
    def get_creation_date_display(self):
        return self.creation_date.strftime("%Y-%m-%d %H:%M:%S")
    get_creation_date_display.admin_order_field = 'creation_date'
    get_creation_date_display.short_description = "Creation date"
    
    def get_last_updated_display(self):
        return self.last_updated.strftime("%Y-%m-%d %H:%M:%S")
    get_last_updated_display.admin_order_field = 'last_updated'
    get_last_updated_display.short_description = "Last updated"
    
    def prev(self):
        return next_or_prev_in_order(self, True, self.__class__.objects)
    def next(self):
        return next_or_prev_in_order(self, False, self.__class__.objects)
    
    class Meta:
        abstract = True
        ordering = ('-creation_date',)



def date_set(*args, **kwargs):
    if isinstance(kwargs['instance'], DateAuditModel):
        if not kwargs['instance'].creation_date:
            kwargs['instance'].creation_date = datetime.datetime.now()
        kwargs['instance'].last_updated = datetime.datetime.now()
models.signals.pre_save.connect(date_set)



class LiveManager(models.Manager):
    """Used to get objects that have is_live on, and a non-future publication_date."""
    
    def get_query_set(self):
        return super(LiveManager, self).get_query_set() \
                                       .filter(is_live=True, 
                                               publication_date__lte=datetime.datetime.now())



class FeaturedManager(LiveManager):
    """Used to get live objects that also have is_featured on."""
    
    def get_query_set(self):
        return super(FeaturedManager, self).get_query_set().filter(is_featured=True)
        
    def get_first(self):
        # gets first featured item, but falls back to first live item if none featured
        try:
            return self.get_query_set()[0]
        except IndexError:
            return super(FeaturedManager, self).get_query_set()[0]



class BaseContentModel(DateAuditModel):
    """Provides managers for 'live' instances, based on the is_live & 
    publication_date fields. Also provides next/prev instance methods 
    for all objects and just live objects, respecting the value of 
    Meta.ordering.
    """
    
    publication_date = models.DateField(default=datetime.date.today, db_index=True)
    is_live = models.BooleanField(default=getattr(settings, 'IS_LIVE_DEFAULT', 1), 
                                  db_index=True, 
                                  help_text="This must be ticked, and 'publication date' must not be in the future, for the item to show on the site.")
    
    objects = models.Manager()
    live = LiveManager()
    
    class Meta(DateAuditModel.Meta):
        abstract = True
        ordering = ('-publication_date', '-creation_date',)

    def prev(self, qs=None):
        return next_or_prev_in_order(self, True, qs or self.__class__.objects)
        
    def next(self, qs=None):
        return next_or_prev_in_order(self, False, qs or self.__class__.objects)
    
    def prev_live(self):
        return self.prev(self.__class__.live)
        
    def next_live(self):
        return self.next(self.__class__.live)


def set_publication_date(sender, **kwargs):
    if not getattr(kwargs['instance'], 'publication_date', None):
        kwargs['instance'].publication_date = datetime.date.today()
models.signals.pre_save.connect(set_publication_date, sender=BaseContentModel)


class BaseFeaturedContentModel(BaseContentModel):
    """Similar to BaseContentModel but provides additional manager
    for 'featured' instances, using the is_featured field. Also 
    provides next/prev instance methods for featured objects.
    """

    is_featured = models.BooleanField(default=0, db_index=True)
        
    objects = models.Manager()
    live = LiveManager()
    featured = FeaturedManager()

    class Meta(BaseContentModel.Meta):
        abstract = True

    def prev_featured(self):
        return self.prev(self.__class__.featured)
        
    def next_featured(self):
        return self.next(self.__class__.featured)


class BaseSortedModel(models.Model):
    """Provides a sort_order field and orders on it by default."""
    
    sort_order = models.IntegerField(default=0, blank=True)
        
    class Meta:
        abstract = True
        ordering = ('sort_order', 'id')


def set_sort_order(sender, **kwargs):
    if isinstance(kwargs['instance'], BaseSortedModel):
        if not getattr(kwargs['instance'], 'sort_order', None):
            kwargs['instance'].sort_order = 0
models.signals.pre_save.connect(set_sort_order)


class BaseModelWithImages(models.Model):
    """Basic model for use with related images (needs a related Image model
    with the related_name 'image_set').
    """

    class Meta:
        abstract = True
    
    @property
    def primary_image(self):
        try:
            return self.image_set.all()[0]
        except IndexError:
            return None
    
    @property
    def random_image(self):
        try:
            return self.image_set.all().order_by('?')[0]
        except IndexError:
            return None
    
    @property
    def image_count(self):
        return self.image_set.count()


class FeaturedManagerWithImages(FeaturedManager):
    """Manager for featured objects that requires the object to have an image."""
    
    def get_query_set(self):
        return super(FeaturedManagerWithImages, 
                     self).get_query_set().filter(image_set__isnull=False).distinct()
    


class BaseContentModelWithImages(BaseFeaturedContentModel, BaseModelWithImages):
    """The same as BaseContentModel, except it requires featured objects to have at least
    one inline image (needs a related Image model with related_name 'image_set').
    
    Provides primary_image and random_image methods
    
    Example implementation:
    
    class Article(BaseContentModelWithImages):
        ...
    
    class ArticleImage(BaseImageModel;):
        article = models.ForeignKey(Article, related_name='image_set')
        
    """

    class Meta(BaseFeaturedContentModel.Meta):
        abstract = True
    
    objects = models.Manager()
    live = LiveManager()
    featured = FeaturedManagerWithImages()



class BaseImageModel(BaseSortedModel):
    """Use this in conjunction with BaseModelWithImages or BaseContentModelWithImages.
    
    For an example see the BaseContentModelWithImages docstring."""

    caption = models.CharField(max_length=255, default='', blank=True)
    file = ConstrainedImageField(u'image file', upload_to=settings.UPLOAD_PATH, 
                                 max_dimensions=getattr(settings, 'MAX_IMAGE_DIMENSIONS',
                                                        None))
    
    def __unicode__(self):
        return self.caption or str(self.file)
        
    class Meta(BaseSortedModel.Meta):
        abstract = True
        ordering = BaseSortedModel.Meta.ordering + ('caption',)



class BaseHierarchyModel(models.Model):
    """Provides a simple hierarchy system.
    
    For example when categories and subcategories are needed. Provides get_hierarchy method, 
    which is primarily useful for getting the top level category for a given category, eg
    
    >>> category.get_hierarchy()[0]
    
    Currently only 2 levels are supported - in future this will be configurable.
    """
    
    parent = models.ForeignKey('self', null=True, blank=True, 
                               related_name='children', 
                               limit_choices_to={'parent__isnull': True})
    
    def __unicode__(self):
        return ' > '.join([c.name for c in self.get_hierarchy()])
    
    def get_parent_display(self):
        return self.parent or ''
        
    get_parent_display.short_description = 'parent'
    get_parent_display.admin_order_field = 'parent'
    
    def get_hierarchy(self, include_self=True):
        if self.parent:
            return self.parent.get_hierarchy() + (include_self and [self] or [])
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
    

