from haystack import indexes
from models import BaseImageModel
import datetime

class BaseIndex(indexes.RealTimeSearchIndex):
#class BaseIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
                
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
    
    def get_queryset(self):
        if hasattr(self.model, 'live'):
            return self.model.live
        else:
            return self.model.objects
    
    
    class Meta:
        abstract = True
