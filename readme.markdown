`baseclasses` is a set of tools I find useful and have used on numerous projects. 

#### 10/6/2011 update:
The master branch has been in use on several live sites for a few months now,
so I'm confident it's ready for public use. Old cruft is in the legacy branch.


#### An example:
    
    from django.db import models
    from baseclasses.models import BaseContentModel, BaseModelWithImages, BaseImageModel
    
    
    class Article(BaseContentModel, BaseModelWithImages):
        text = models.TextField()
            
    class ArticleImage(BaseImageModel):
        article = models.ForeignKey(Article, related_name='image_set')
        
    
With the above model definition, you can do the following:

    Article.live.all() # get all live articles

    article.primary_image # get primary image for the article
    article.next # get next article
    article.next_live # get next live article


If you don't have an attached Image model, then just use `BaseContentModel`,
and not `BaseModelWithImages` as your base.

