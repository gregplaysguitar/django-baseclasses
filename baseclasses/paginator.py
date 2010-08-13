from django.core.paginator import EmptyPage, InvalidPage, Paginator
#from pagination.paginator import InfinitePaginator



class CustomPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        self.raise_errors = kwargs.pop('raise_errors', True)
        super(CustomPaginator, self).__init__(*args, **kwargs) 

    def page(self, p, *args, **kwargs):
        # Make sure page request is an int. If not, deliver first page.
        try:
            p = int(p)
        except ValueError:
            p = 1
        
        # If page request (9999) is out of range, deliver last page of results.
        try:
            return super(CustomPaginator, self).page(p, *args, **kwargs)
        except (EmptyPage, InvalidPage):
            if self.raise_errors:
                raise
            else:
                return super(CustomPaginator, self).page(self.num_pages, *args, **kwargs)

   