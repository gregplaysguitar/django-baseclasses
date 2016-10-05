django-baseclasses is a small set of helpers and abstract base model classes
for django.

## Installation

    python ./setup.py install

Or with pip:

    pip install django-baseclasses

## Abstract classes provided in `baseclasses.models`

#### `DateAuditModel`

Stores a record of when the model was created and last changed, in the `creation_date` and `last_updated` fields, orders on `creation_date`, and 
provides `get_next` and `get_prev` methods respecting the ordering.

#### `BaseContentModel`

Extends `DateAuditModel`, adding `is_live` and `pub_date` fields, and provides
a `live` method on the default manager which returns only objects with 
`is_live` set and a non-future `pub_date`. Also orders by `pub_date`, and
provides `next_live` and `prev_live` methods which only cycle through "live"
objects.

#### `BaseImageModel`

Provides `caption`, `image` and `sort_order` fields. Orders on `sort_order`.

#### `BaseModelWithImages`

Parent model for use with a `BaseImageModel` with a ForeignKey to this model. 
Provides `primary_image` property which returns the first related image object, 
or `None`. The ForeignKey's `related_name` must be "image_set"

#### `BaseHierarchyModel`

Provides `parent` field to create a simple hierarchy system, i.e. categories 
and subcategories. Provides get_hierarchy method, which returns a list of 
objects in the tree, from the top level to the current.


## Model fields

#### `baseclasses.fields.ConstrainedImageField`

Resizes the image on upload and overwrites the original. Use `max_dimensions`
argument to determine the resize behaviour.


## Helpers

#### `baseclasses.util.next_or_prev_in_order`

Arguments: `(instance, prev=False, qs=None, loop=False)`

Get the next (or previous with prev=True) item for an instance, from the given
queryset (which is assumed to contain instance), respecting queryset ordering.
If loop is True, return the first/last item when the end/start is reached.

#### `baseclasses.admin.ContentModelAdminMixin`

Enables (cache-safe) admin preview of non-live objects. Example

    @admin.register(MyModel)
    class MyModelAdmin(ContentModelAdminMixin, admin.ModelAdmin):
        ...

Pass the request to the model's `live` manager method to enable preview:

    def my_model_view(request, slug)
        instance = get_object_or_404(MyModel.objects.live(request), slug=slug)
        ...

## Example:
   
    # models.py
    
    from django.db import models
    from baseclasses.models import BaseContentModel, BaseModelWithImages, \
                                   BaseImageModel
    
    
    class Article(BaseContentModel, BaseModelWithImages):
        title = models.CharField(max_length=190) 
        text = models.TextField()
        
     
    class ArticleImage(BaseImageModel):
        article = models.ForeignKey(Article, related_name='image_set')
        
    
With the above model definition, you can do the following:

    articles = Article.objects.live() # get queryset of all live articles
    article = articles[0]
    article.primary_image # get primary image (model instance) for the article
    article.next_live # get next live article
