from pyramid.renderers import render

class DebugToolbar(object):
    def __init__(self, request):
        self.request = request
        self.panels = []
        panel_classes = self.request.settings['debugtoolbar.classes']
        activated = self.request.cookies.get('fldt_active', '').split(';')
        for panel_class in panel_classes:
            panel_instance = panel_class(context={})
            if panel_instance.dom_id() in activated:
                panel_instance.is_active = True
            self.panels.append(panel_instance)

    def render_toolbar(self):
        request = self.request
        static_path = request.static_url('pyramid_debugtoolbar:static',
                                         request)
        vars = {'panels': self.panels,
                'static_path':static_path}
        return render('base.html', vars)


