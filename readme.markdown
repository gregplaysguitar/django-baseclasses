`baseclasses` is a set of tools I find useful and have used on numerous projects. 

#### 30/3/2011 update:
Currently I'm working on getting this ready for public consumption - the
springcleaning branch has had all of the experimental cruft removed, and 
docstrings etc added. Once I'm satisfied that it's useful and usable, this
will become the master branch. 


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

