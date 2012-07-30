from django.views.generic.base import TemplateView, RedirectView
from django.core.urlresolvers import reverse

class ExtraContextView(TemplateView):
    """Like the built in Templateview, but compensates for the missing 
    extra_context argument which was available with the old-style generic views.
    
    Usage example:
    
        urlpatterns = patterns('',
            (r'^myurl/$', ExtraContextView.as_view(
                template_name='mytemplate.html',
                extra_context={
                    ...
                },
            )),
    
    """
    extra_context = {}
    
    def get_context_data(self, **kwargs):
        context = super(ExtraContextView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


def reverse_and_redirect(view, *args, **kwargs):
    '''Returns a RedirectView which will redirect to a url determined by reversing the 
       given parameters. The reverse is lazy in that it won't be evaluated until 
       needed.'''
    
    class _Redirect(RedirectView):
        def get_redirect_url(self, **k):
            return reverse(view, args=args, kwargs=kwargs)

    return _Redirect.as_view()
