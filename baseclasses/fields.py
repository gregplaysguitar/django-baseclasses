import re

from django.db.models.fields.files import ImageField
from django.core.exceptions import ImproperlyConfigured
from django.db.models import signals, SlugField
from django.template.defaultfilters import slugify


class ConstrainedImageField(ImageField):
    """
    Resizes the image on upload and overwrites the original.
    Example:
    
    class MyModel(models.Model):
        image = ConstrainedImageField(u'image file', upload_to=settings.UPLOAD_PATH, max_dimensions=(1024, 768))
    
    """
    
    def __init__(self, *args, **kwargs):
        self.max_dimensions = kwargs.pop('max_dimensions', None)
        super(ConstrainedImageField, self).__init__(*args, **kwargs)

    def _resize_image(self, filename, size):
        WIDTH, HEIGHT = 0, 1
        from PIL import Image, ImageOps
        Image.MAXBLOCK = 1024 * 1024 * 20 # Attempt to fix the "Suspension not allowed here" error
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

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.files.ImageField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
        
    def deconstruct(self):
        name, path, args, kwargs = \
            super(ConstrainedImageField, self).deconstruct()
        
        # Only include kwarg if it's not the default
        if self.max_dimensions != None:
            kwargs['max_dimensions'] = self.max_dimensions

        return name, path, args, kwargs
