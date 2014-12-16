from django.db import models


def get_model_attr(instance, attr):
    """Example usage: get_model_attr(instance, 'category__slug')"""
    for field in attr.split('__'):
        instance = getattr(instance, field)
    return instance


def next_or_prev_in_order(instance, prev=False, qs=None, loop=False):
    """Get the next (or previous with prev=True) item for instance, from the 
       given queryset (which is assumed to contain instance) respecting 
       queryset ordering. If loop is True, return the first/last item when the
       end/start is reached. """
    
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
        q_list.append(models.Q(**q_kwargs))
        prev_fields.append(field)
    try:
        return qs.filter(reduce(models.Q.__or__, q_list))[0]
    except IndexError:
        length = qs.count()
        if loop and length > 1:
            return qs[(length - 1) if prev else 0]
    return None


class LambdaManager(models.Manager):
    """LambdaManager is a simple manager extension that is instantiated with a 
       callable, which performs additional transformations - such as
       filtering - on the queryset. """
    
    def __init__(self, f):
        super(LambdaManager, self).__init__()

        self.transform = f
    
    def get_queryset(self):
        return self.transform(super(LambdaManager, self).get_queryset())
    
    # backwards-compatibility
    def get_query_set(self):
        return self.transform(super(LambdaManager, self).get_query_set())

