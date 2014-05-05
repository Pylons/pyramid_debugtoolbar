from pprint import saferepr

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import dictrepr


_ = lambda x: x

class RequestVarsDebugPanel(DebugPanel):
    """
    A panel to display request variables (POST/GET, session, cookies, and
    ad-hoc request attributes).
    """
    name = 'RequestVars'
    has_content = True
    template = 'pyramid_debugtoolbar.panels:templates/request_vars.dbtmako'
    title = _('Request Vars')
    nav_title = title

    def __init__(self, request):
        self.data = data = {}
        attr_dict = request.__dict__.copy()
        # environ is displayed separately
        del attr_dict['environ']
        if 'response' in attr_dict:
            attr_dict['response'] = repr(attr_dict['response'])
        data.update({
            'get': [(k, request.GET.getall(k)) for k in request.GET],
            'post': [(k, [saferepr(p) for p in request.POST.getall(k)])
                    for k in request.POST],
            'cookies': [(k, request.cookies.get(k)) for k in request.cookies],
            'attrs': dictrepr(attr_dict),
            'environ': dictrepr(request.environ),
        })
        if hasattr(request, 'session'):
            data.update({
                'session': dictrepr(request.session),
            })
