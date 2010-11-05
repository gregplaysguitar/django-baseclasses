from haystack.forms import SearchForm
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from haystack.sites import site
import haystack
from django import forms
from django.db import models
from django.utils.text import capfirst



class CustomSearchForm(SearchForm):
    
    class Meta:
        abstract = True
        load_all = False
        custom_sqs = None
    
        
    def get_filter_kwargs(self, extra_data):
        kwargs = {}
        
        non_search_fields = getattr(self.Meta, 'non_search_fields', [])
        
        for f in extra_data:
            if extra_data[f] and f not in non_search_fields:
                kwargs[f] = extra_data[f] 
                            
        return kwargs
        
        
    def search(self, *args, **kwargs):
        if self.is_valid():
            extra_data = dict(self.cleaned_data).copy()
            extra_data.pop('q')
            
            sqs = self.Meta.custom_sqs or self.searchqueryset
            
            if self.Meta.allowed_models:
                sqs = sqs.models(*self.Meta.allowed_models)
            
            sqs = sqs.filter(**self.get_filter_kwargs(extra_data))
            
            sqs = sqs.auto_query(self.cleaned_data['q'])
            
            if self.Meta.load_all:
                sqs = sqs.load_all()            
            
            return sqs
        
        else:
            return EmptySearchQuerySet()





def searchform_factory(*args, **kwargs):
    sqs = kwargs.get('sqs', SearchQuerySet())

    class _SearchForm(CustomSearchForm):
        class Meta(CustomSearchForm.Meta):
            custom_sqs = sqs
            allowed_models = args
        
    return _SearchForm
    
    



class CustomModelSearchForm(CustomSearchForm):
    
    
    class Meta(CustomSearchForm.Meta):
        abstract = True
        allowed_models = None # defaults to all, if None specified
        custom_app_names = {}
        custom_sqs = None
        
    
    def __init__(self, *args, **kwargs):
        super(CustomModelSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.ChoiceField(choices=self.models_choices(), required=False, label='Search In', widget=forms.Select)
    
    def models_choices(self, site=None):
        if site is None:
            site = haystack.site
        model_dict = {}
        for m in site.get_indexed_models():
            if not m._meta.app_label in model_dict:
                model_dict[m._meta.app_label] = []
            model_dict[m._meta.app_label].append(m._meta.module_name)
        
        
        choices = [(','.join(("%s.%s" % (app_label, model_name) for model_name in model_dict[app_label])), capfirst(self.Meta.custom_app_names.get(app_label, app_label))) for app_label in model_dict]
        
        return [('', 'The Entire Site')] + sorted(choices, key=lambda x: x[1])

    
    def get_models(self):
        if self.cleaned_data['models']:
            return [models.get_model(*m.split('.')) for m in self.cleaned_data['models'].split(',')]
        else:
            return None
    
    def models_display_value(self):
        return dict(self.models_choices()).get(self.cleaned_data['models'], 'The Entire Site')
    
    
    def search(self, *args, **kwargs):
    
        if self.is_valid():
            if self.Meta.custom_sqs == None:
                sqs = self.searchqueryset
            else:
                sqs = self.Meta.custom_sqs
        
            model_list = self.get_models()
            if model_list:
                sqs = sqs.models(*model_list)

            extra_data = dict(self.cleaned_data).copy()
            extra_data.pop('q')
            extra_data.pop('models')
            sqs = sqs.filter(**self.get_filter_kwargs(extra_data))
            
            
            sqs = sqs.auto_query(self.cleaned_data['q'])

            if self.Meta.load_all:
                sqs = sqs.load_all()            
            
            return sqs 
        
        else:
            return EmptySearchQuerySet()

   

def modelsearchform_factory(models=None):
    sqs = SearchQuerySet()
    
    class _SearchForm(CustomModelSearchForm):
        class Meta(CustomModelSearchForm.Meta):
            custom_sqs = sqs
            allowed_models = models
        
    return _SearchForm
    
    
    
    
    
    
