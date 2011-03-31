from django.db import models


def get_model_attr(instance, attr):
    """Example usage: get_model_attr(instance, 'category__slug')"""
    for field in attr.split('__'):
        instance = getattr(instance, field)
    return instance



def next_or_prev_in_order(instance, prev=False, qs=None):
    """Used to implement prev() and next() methods in the base models classes below."""
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
        return None


