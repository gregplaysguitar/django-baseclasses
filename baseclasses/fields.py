from django.db.models.fields.files import ImageField
from django.db.models import signals


class ConstrainedImageField(ImageField):
    # image field that resizes if the file is too big
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

