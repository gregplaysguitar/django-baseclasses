`baseclasses` is a set of tools I find useful and have used on numerous projects. 

#### 10/6/2011 update:
The master branch has been in use on several live sites for a few months now,
so I'm confident it's ready for public use. Old cruft is in the legacy branch.


#### An example:
    
    from django.db import models
    from baseclasses.models import BaseContentModelWithImages, BaseNamedModel, BaseImageModel
    
    
    class Article(BaseContentModelWithImages, BaseNamedModel):
        text = models.TextField()
            
    class ArticleImage(BaseImageModel):
        article = models.ForeignKey(Article, related_name='image_set')
        
    
With the above model definition, you can do the following:

    Article.live.all() # get all live articles
    Article.featured.all() # get all featured articles
    article = Article.featured.get_first() # get first featured article, or first live if none featured

    article.primary_image # get primary image for the article
    article.next # get next article
    article.next_live # get next live article
    article.next_featured # get next featured article
    

If you don't have an attached Image model, then use `BaseContentModel` instead
of `BaseContentModelWithImages`

