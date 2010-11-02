from haystack.forms import SearchForm
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from haystack.sites import site
import haystack
from django import forms
from django.db import models
from django.utils.text import capfirst



class CustomSearchForm(SearchForm):
    load_all = False
    custom_sqs = None
    
    class Meta:
        abstract = True
          
        
    def get_filter_kwargs(self, extra_data, allowed_models=False):
        kwargs = {}
        
        if allowed_models == False:
            allowed_models = self.allowed_models
            
        if allowed_models:
            allowed_apps = [m._meta.app_label for m in allowed_models]
        else:
            allowed_apps = None
        
        all_apps = [m._meta.app_label for m in site.get_indexed_models()]
        
        for f in extra_data:
            if extra_data[f]:
                app = f.split('_')[0]
                if app not in all_apps:
                    # assume a generic field common to all indexes
                    kwargs[f] = extra_data[f] 
                elif allowed_apps and (app in allowed_apps):
                    # assume an app-specific field - include only if app is being searched
                    kwargs['_'.join(f.split('_')[1:])] = extra_data[f] 
        #print kwargs               
        return kwargs
        
        
    def search(self, *args, **kwargs):
        if self.is_valid():
            extra_data = dict(self.cleaned_data).copy()
            extra_data.pop('q')
            
            sqs = self.custom_sqs or self.searchqueryset
            
            if self.allowed_models:
                sqs = sqs.models(*self.allowed_models)
            
            
            sqs = sqs.filter(**self.get_filter_kwargs(extra_data))
            
            #print extra_data, self.get_filter_kwargs(extra_data)
            
            sqs = sqs.auto_query(self.cleaned_data['q'])
            
            if self.load_all:
                sqs = sqs.load_all()            
            
            return sqs
        
        else:
            return EmptySearchQuerySet()





def searchform_factory(*args, **kwargs):
    sqs = kwargs.get('sqs', SearchQuerySet())

    class _SearchForm(CustomSearchForm):
        custom_sqs = sqs
        allowed_models = args
        
    return _SearchForm
    
    



class CustomModelSearchForm(CustomSearchForm):
    allowed_models = None # defaults to all, if None specified
    custom_app_names = {}
    custom_sqs = None
    
    class Meta:
        abstract = True
    
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
        
        choices = [(','.join(("%s.%s" % (app_label, model_name) for model_name in model_dict[app_label])), capfirst(self.custom_app_names.get(app_label, app_label))) for app_label in model_dict]
        
        #choices = [("%s.%s" % (m._meta.app_label, m._meta.module_name), capfirst(unicode(m._meta.verbose_name_plural))) for m in model_list]
        return [('', 'The Entire Site')] + sorted(choices, key=lambda x: x[1])

    
    def get_models(self):
        if self.cleaned_data['models']:
            return [models.get_model(*m.split('.')) for m in self.cleaned_data['models'].split(',')]
        else:
            return None
    
    def models_display_value(self):
        return dict(self.models_choices()).get(self.cleaned_data['models'], 'The Entire Site')
    
    
    def search(self, *args, **kwargs):
        #print "valid", self.is_valid()
    
        if self.is_valid():
            if self.custom_sqs == None:
                sqs = self.searchqueryset
            else:
                sqs = self.custom_sqs
        
            model_list = self.get_models()
            if model_list:
                sqs = sqs.models(*model_list)

            extra_data = dict(self.cleaned_data).copy()
            extra_data.pop('q')
            extra_data.pop('models')
            sqs = sqs.filter(**self.get_filter_kwargs(extra_data, model_list))
            
            
            sqs = sqs.auto_query(self.cleaned_data['q'])

            if self.load_all:
                sqs = sqs.load_all()            
            
            return sqs 
        
        else:
            return EmptySearchQuerySet()

   

def modelsearchform_factory(models=None):
    sqs = SearchQuerySet()
    
    class _SearchForm(CustomModelSearchForm):
        custom_sqs = sqs
        allowed_models = models
        
    return _SearchForm
    
    
    
    
    
    
