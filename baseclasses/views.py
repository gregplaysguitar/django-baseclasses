from django.views.generic.base import TemplateView


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
        context = super(ExtraContextView, self).get_context_data()
        context.update(self.extra_context)
        return context

    