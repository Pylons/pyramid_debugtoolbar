from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x

class RequestVarsDebugPanel(DebugPanel):
    """
    A panel to display request variables (POST/GET, session, cookies).
    """
    name = 'RequestVars'
    has_content = True

    def nav_title(self):
        return _('Request Vars')

    def title(self):
        return _('Request Vars')

    def url(self):
        return ''

    def process_request(self, request):
        self.request = request

    def content(self):
        self.vars.update({
            'get': [(k, self.request.GET.getall(k)) for k in self.request.GET],
            'post': [(k, self.request.POST.all(k)) for k in self.request.POST],
            'cookies': [(k, self.request.cookies.get(k)) for k in
                        self.request.cookies],
            'view_func': '%s' % self.view_func,
            'view_args': self.view_args,
            'view_kwargs': self.view_kwargs or {}
        })
        if hasattr(self.request, 'session'):
            self.vars.update({
                'session': [(k, self.request.session.get(k)) for k in
                            self.request.session.keys()]
            })

        return self.render('panels/request_vars.jinja2', self.vars)

