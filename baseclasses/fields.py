# coding: utf8

from django.db.models import ImageField


class ConstrainedImageField(ImageField):
    """Keep a stub of this class around so it doesn't screw up the db migration
       history. """
    pass
