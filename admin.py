from django.contrib import admin


class BaseNamedContentAdmin(admin.ModelAdmin):
    class Meta:
        abstract = True
    
    list_display = ['name', 'slug', 'publication_date', 'is_live', 'is_featured']
    list_filter = ['publication_date', 'last_updated', 'is_live', 'is_featured']
    search_fields = ['name',]

def tabularinline_factory(model_cls, **kwargs):
    class InlineOptions(admin.TabularInline):
        max_num = kwargs.pop('max_num', 1)
        extra = kwargs.pop('extra', 1)
        model = model_cls
        
    for option in kwargs:
        setattr(InlineOptions, option, kwargs[option])
        
    return InlineOptions


def admin_factory(base_cls=None, **kwargs):
    """
    inline_models = kwargs.pop('inline_models', [])
    generated_inlines = []
    for model_cls in inline_models:
    """ 
    
    if not base_cls:
        base_cls = BaseNamedContentAdmin
    class AdminOptions(base_cls):
        pass
    
    for key in kwargs:
        try:
            setattr(AdminOptions, key, getattr(AdminOptions, key) + kwargs[key])
        except TypeError:
            setattr(AdminOptions, key, kwargs[key])
    return AdminOptions
    

class BaseMediaAdmin(admin.ModelAdmin):
    class Meta:
        abstract = True
    
    list_display = ['caption', 'file', 'sort_order']
    search_fields = ['caption', 'file']


class BasePDFAdmin(BaseMediaAdmin):
    class Meta:
        abstract = True
    
    search_fields = ['caption', 'file', 'text']


