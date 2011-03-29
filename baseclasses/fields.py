from django.db.models.fields.files import ImageField
from django.db.models import signals, SlugField
from django.template.defaultfilters import slugify
import re



"""
Resizes the image on upload and overwrites the original - example

class MyModel(models.Model):
    image = ConstrainedImageField(u'image file', upload_to=settings.UPLOAD_PATH, max_dimensions='1024x768')


"""
class ConstrainedImageField(ImageField):
    # image field that resizes if the file is too big
    def __init__(self, *args, **kwargs):
        self.max_dimensions = kwargs.pop('max_dimensions', None)
        super(ConstrainedImageField, self).__init__(*args, **kwargs)


    def _resize_image(self, filename, size):
        WIDTH, HEIGHT = 0, 1
        from PIL import Image, ImageOps
        img = Image.open(filename)
        if img.size[WIDTH] > size[WIDTH] or img.size[HEIGHT] > size[HEIGHT]:
            img.thumbnail((size[WIDTH], size[HEIGHT]), Image.ANTIALIAS)
            try:
                img.save(filename, optimize=1)
            except IOError:
                img.save(filename)


    def _constrain_image(self, instance=None, **kwargs):
        if getattr(instance, self.name) and self.max_dimensions:
            filename = getattr(instance, self.name).path
            self._resize_image(filename, self.max_dimensions)


    def contribute_to_class(self, cls, name):
        super(ConstrainedImageField, self).contribute_to_class(cls, name)
        signals.post_save.connect(self._constrain_image, sender=cls)





""" 
borrowed from django_extensions - see
https://github.com/django-extensions/django-extensions/blob/master/django_extensions/db/fields/__init__.py
"""
class AutoSlugField(SlugField):
    """ AutoSlugField

    By default, sets editable=False, blank=True.

    Required arguments:

    populate_from
        Specifies which field or list of fields the slug is populated from.

    Optional arguments:

    separator
        Defines the used separator (default: '-')

    overwrite
        If set to True, overwrites the slug on every save (default: False)

    Inspired by SmileyChris' Unique Slugify snippet:
    http://www.djangosnippets.org/snippets/690/
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('editable', False)

        populate_from = kwargs.pop('populate_from', None)
        if populate_from is None:
            raise ValueError("missing 'populate_from' argument")
        else:
            self._populate_from = populate_from
        self.separator = kwargs.pop('separator',  u'-')
        self.overwrite = kwargs.pop('overwrite', False)
        super(AutoSlugField, self).__init__(*args, **kwargs)

    def _slug_strip(self, value):
        """
        Cleans up a slug by removing slug separator characters that occur at
        the beginning or end of a slug.

        If an alternate separator is used, it will also replace any instances
        of the default '-' separator with the new separator.
        """
        re_sep = '(?:-|%s)' % re.escape(self.separator)
        value = re.sub('%s+' % re_sep, self.separator, value)
        return re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)

    def slugify_func(self, content):
        return slugify(content)

    def create_slug(self, model_instance, add):
        # get fields to populate from and slug field to set
        if not isinstance(self._populate_from, (list, tuple)):
            self._populate_from = (self._populate_from, )
        slug_field = model_instance._meta.get_field(self.attname)

        if add or self.overwrite:
            # slugify the original field content and set next step to 2
            slug_for_field = lambda field: self.slugify_func(getattr(model_instance, field))
            slug = self.separator.join(map(slug_for_field, self._populate_from))
            next = 2
        else:
            # get slug from the current model instance and calculate next
            # step from its number, clean-up
            slug = self._slug_strip(getattr(model_instance, self.attname))
            next = slug.split(self.separator)[-1]
            if next.isdigit():
                slug = self.separator.join(slug.split(self.separator)[:-1])
                next = int(next)
            else:
                next = 2

        # strip slug depending on max_length attribute of the slug field
        # and clean-up
        slug_len = slug_field.max_length
        if slug_len:
            slug = slug[:slug_len]
        slug = self._slug_strip(slug)
        original_slug = slug

        # exclude the current model instance from the queryset used in finding
        # the next valid slug
        queryset = model_instance.__class__._default_manager.all()
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to impliment any unique_together contraints
        kwargs = {}
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)
        kwargs[self.attname] = slug

        # increases the number while searching for the next valid slug
        # depending on the given slug, clean-up
        while not slug or queryset.filter(**kwargs):
            slug = original_slug
            end = '%s%s' % (self.separator, next)
            end_len = len(end)
            if slug_len and len(slug)+end_len > slug_len:
                slug = slug[:slug_len-end_len]
                slug = self._slug_strip(slug)
            slug = '%s%s' % (slug, end)
            kwargs[self.attname] = slug
            next += 1
        return slug

    def pre_save(self, model_instance, add):
        value = unicode(self.create_slug(model_instance, add))
        setattr(model_instance, self.attname, value)
        return value

    def get_internal_type(self):
        return "SlugField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.SlugField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
