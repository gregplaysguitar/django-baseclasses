from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse


def reverse_and_redirect(view, *args, **kwargs):
    '''Returns a RedirectView which will redirect to a url determined by 
       reversing the given parameters. The reverse is lazy in that it won't 
       be evaluated until needed.'''
    
    class _Redirect(RedirectView):
        def get_redirect_url(self, **k):
            return reverse(view, args=args, kwargs=kwargs)

    return _Redirect.as_view()
