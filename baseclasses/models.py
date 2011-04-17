from django.db import models
import datetime
from django.conf import settings
#from filefield_enhanced import RemovableFileField, RemovableImageField
#from helpers import pdf
from fields import ConstrainedImageField, AutoSlugField

def get_model_attr(instance, attr):
    for field in attr.split('__'):
        instance = getattr(instance, field)
    return instance
   
def next_or_prev_in_order(instance, prev=False, qs=None):
    if not qs:
        qs = instance.__class__.objects
    if prev:
        qs = qs.reverse()
        lookup = 'lt'
    else:
        lookup = 'gt'
    
  
    q_list = []
    prev_fields = []
    if qs.model._meta.ordering:
        ordering = list(qs.model._meta.ordering)
    else:
        ordering = []
    
    for field in (ordering + ['pk',]):
        if field[0] == '-':
            this_lookup = (lookup == 'gt' and 'lt' or 'gt')
            field = field[1:]
        else:
            this_lookup = lookup
        q_kwargs = dict([(f, get_model_attr(instance, f)) for f in prev_fields])
        q_kwargs["%s__%s" % (field, this_lookup)] = get_model_attr(instance, field)
        #print q_kwargs
        q_list.append(models.Q(**q_kwargs))
        prev_fields.append(field)
    try:
        #print q_list
        #print qs.filter(reduce(models.Q.__or__, q_list))
        return qs.filter(reduce(models.Q.__or__, q_list))[0]
    except IndexError:
        return None




class LiveManager(models.Manager):
    def get_query_set(self):
        return super(LiveManager, self).get_query_set().filter(is_live=True, publication_date__lte=datetime.datetime.now())

        
class FeaturedManager(LiveManager):
    def get_query_set(self):
        return super(FeaturedManager, self).get_query_set().filter(is_featured=True)
    def get_first(self):
        # gets first featured item, but falls back to first live item if none featured
        try:
            return self.get_query_set()[0]
        except IndexError:
            return super(FeaturedManager, self).get_query_set()[0]


class FeaturedManagerWithImages(FeaturedManager):
    def get_query_set(self):
        return super(FeaturedManagerWithImages, self).get_query_set().filter(image__isnull=False).distinct()
    


class DateAuditModel(models.Model):
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

class BaseContentModel(DateAuditModel):
    publication_date = models.DateField(default=datetime.date.today, db_index=True)#, help_text="This is the date from which the item will be shown on the site") # this field is required in order to use LiveManager
    is_live = models.BooleanField(default=getattr(settings, 'IS_LIVE_DEFAULT', 1), db_index=True, help_text="This must be ticked, and 'publication date' must be in the past, for the item to show on the site.")
    is_featured = models.BooleanField(default=0, db_index=True)
    
    objects = models.Manager()
    live = LiveManager()
    featured = FeaturedManager()
    
    class Meta(DateAuditModel.Meta):
        abstract = True
        ordering = ('-publication_date', '-creation_date',)

    def prev(self, qs=None):
        return next_or_prev_in_order(self, True, qs or self.__class__.objects)
    def next(self, qs=None):
        return next_or_prev_in_order(self, False, qs or self.__class__.objects)
    
    def prev_live(self):
        return next_or_prev_in_order(self, True, self.__class__.live)
    def next_live(self):
        return next_or_prev_in_order(self, False, self.__class__.live)

    def prev_featured(self):
        return next_or_prev_in_order(self, True, self.__class__.featured)
    def next_featured(self):
        return next_or_prev_in_order(self, False, self.__class__.featured)
    
    


def set_publication_date(sender, **kwargs):
    if not getattr(kwargs['instance'], 'publication_date', None):
        kwargs['instance'].publication_date = datetime.date.today()
models.signals.pre_save.connect(set_publication_date, sender=BaseContentModel)



class BaseNamedModel(models.Model):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from="name")
       
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)
        abstract = True


class BaseLongNamedModel(models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name")
       
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)
        abstract = True

"""
def populate_slug(sender, **kwargs):
    if isinstance(kwargs['instance'], BaseNamedModel):
        #print kwargs['instance'].name
        pass
models.signals.pre_save.connect(populate_slug)
"""

class BasePersonModel(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from=('first_name', 'last_name'))
       
    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)
    
    class Meta:
        ordering = ('last_name', 'first_name',)
        abstract = True
  



class BaseSortedModel(models.Model):
    sort_order = models.IntegerField(default=0, blank=True)
        
    class Meta:
        abstract = True
        ordering = ('sort_order', 'id')

   

def set_sort_order(sender, **kwargs):
    if isinstance(kwargs['instance'], BaseSortedModel):
        if not getattr(kwargs['instance'], 'sort_order', None):
            kwargs['instance'].sort_order = 0
models.signals.pre_save.connect(set_sort_order)


class BaseMediaModel(BaseSortedModel):
    caption = models.CharField(max_length=255, default='', blank=True)
    
    def __unicode__(self):
        return self.caption or str(self.file)
        
    class Meta:
        abstract = True
        ordering = BaseSortedModel.Meta.ordering + ('caption',)
   


class BaseImageModel(BaseMediaModel):
    file = ConstrainedImageField(u'image file', upload_to=settings.UPLOAD_PATH, max_dimensions=getattr(settings, 'MAX_IMAGE_DIMENSIONS', None))
        
    class Meta(BaseMediaModel.Meta):
        abstract = True



"""class BasePDFModel(BaseMediaModel):
    file = models.FileField(u'PDF file', upload_to=settings.UPLOAD_PATH)
    text = models.TextField(editable=False, default='')
        
    class Meta(BaseMediaModel.Meta):
        abstract = True
def pdf_text(sender, **kwargs):
    if isinstance(kwargs['instance'], BasePDFModel):
        kwargs['instance'].text = pdf.pdf_to_text(kwargs['instance'].file)
models.signals.pre_save.connect(pdf_text)
"""

class BaseVideoModel(BaseMediaModel):
    file = models.FileField(u'video file', upload_to=settings.UPLOAD_PATH)
        
    class Meta(BaseMediaModel.Meta):
        abstract = True


class BaseAudioModel(BaseMediaModel):
    file = models.FileField(u'audio file', upload_to=settings.UPLOAD_PATH)
        
    class Meta(BaseMediaModel.Meta):
        abstract = True






class BaseContentModelWithImages(BaseContentModel):
    @property
    def primary_image(self):
        try:
            return self.image_set.all()[0].file
        except IndexError:
            return None
    @property
    def primary_image_caption(self):
        try:
            return self.image_set.all()[0].caption
        except IndexError:
            return None
    def random_image(self):
        try:
            return self.image_set.all().order_by('?')[0].file
        except IndexError:
            return None
    class Meta(BaseContentModel.Meta):
        abstract = True
    
    @property
    def image_count(self):
        return self.image_set.count()
    
    objects = models.Manager()
    live = LiveManager()
    featured = FeaturedManagerWithImages()




class BaseHierarchyModel(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', limit_choices_to={'parent__isnull': True})
    
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
        or kwargs['instance'].parent_id == kwargs['instance'].pk:
            kwargs['instance'].parent = None
models.signals.pre_save.connect(check_tree)
    



""" 
class BaseVimeoModel(models.Model):
    vimeo_url = models.URLField(help_text="Should be of the form http://vimeo.com/1234567")
    caption = models.CharField(max_length=255, default='', blank=True)
    sort_order = models.IntegerField(default=0, blank=True)
    
    def __unicode__(self):
        return self.caption
        
    class Meta:
        abstract = True
        ordering = ('sort_order', 'caption')
    
    def vimeo_id(self):
        return self.vimeo_url.replace('http://vimeo.com/', '').replace('http://www.vimeo.com/', '')
"""
   

    
