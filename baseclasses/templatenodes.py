from django import template



class QuerysetNode(template.Node):
    def __init__(self, model_cls, manager, method, varname):
        self.model_cls = model_cls
        self.manager = manager
        self.method = method
        self.varname = varname

    def render(self, context):
        manager_name = template.Variable(self.manager).resolve(context)
        method = template.Variable(self.method).resolve(context)
        manager = getattr(self.model_cls, manager_name, self.model_cls.live)
        context[self.varname] = getattr(manager, method, manager.all)()
        return ''
        