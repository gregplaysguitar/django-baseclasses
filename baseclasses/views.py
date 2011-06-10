from django.views.generic.base import TemplateView


class ExtraContextView(TemplateView):
    extra_context = {}
    
    def get_context_data(self, **kwargs):
        context = super(ExtraContextView, self).get_context_data()
        context.update(self.extra_context)
        return context

    