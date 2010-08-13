from haystack import indexes
from models import BaseImageModel
import datetime

class BaseIndex(indexes.RealTimeSearchIndex):
#class BaseIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    is_live = indexes.BooleanField()
    def prepare_is_live(self, instance):
        if hasattr(instance, 'publication_date'):
            return instance.is_live and (getattr(instance, 'publication_date', None) <= datetime.date.today())
        else:
            return instance.is_live
            
    name = indexes.CharField(model_attr='name') 
    url = indexes.CharField(model_attr='get_absolute_url') 
    image = indexes.CharField()
    def prepare_image(self, instance):
        image = instance.primary_image()
        if image:
            if isinstance(image, BaseImageModel):
                return unicode(image.file)
            else:
                return unicode(image)
        else:
            return ''
    
    
    class Meta:
        abstract = True
