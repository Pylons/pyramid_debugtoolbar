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

    def content(self):
        vars = {}
        request = self.request
        attrs = sorted(request.__dict__.items())
        vars.update({
            'get': [(k, request.GET.getall(k)) for k in request.GET],
            'post': [(k, request.POST.getall(k)) for k in request.POST],
            'cookies': [(k, request.cookies.get(k)) for k in request.cookies],
            'attrs': attrs,
        })
        if hasattr(self.request, 'session'):
            vars.update({
                'session': [(k, self.request.session.get(k)) for k in
                            self.request.session.keys()]
            })

        return self.render(
            'pyramid_debugtoolbar.panels:templates/request_vars.jinja2',
            vars,
            request=self.request)

