from pprint import saferepr

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import dictrepr


_ = lambda x: x


# extractable_request_attributes allow us to programmatically pull data
# the format is ( attr_, is_dict)
extractable_request_attributes = (
    ('accept_charset', None),
    ('accept_encoding', None),
    ('accept_language', None),
    ('application_url', None),
    ('authenticated_userid', None),
    ('authorization', None),
    ('cache_control', None),
    ('context', None),
    ('effective_principals', None),
    ('exc_info', None),
    ('exception', None),
    ('locale_name', None),
    ('matchdict', None),
    ('matched_route', True),
    ('path', None),
    # ('registry', None),  # see "Note1"
    ('root', None),
    ('subpath', None),
    ('traversed', None),
    ('unauthenticated_userid', None),
    ('url', None),
    ('view_name', None),
    ('virtual_root_path', None),
    ('virtual_root', None),
)
# Note1: accessed as a 'string', `registry` be the python package name;
#        accessed as a dict, will be the contents of the registry

# Note2: only request attributes and properties are supported.  all known
#        'read' methods have properties that show the same info
#        For example `request.current_url()` is essentially `request.url`


def extract_request_attributes(request):
    """
    Extracts useful request attributes from the ``request`` object into a dict.
    Data is serialized into a dict so that the original request is not longer
    needed.
    """
    extracted_attributes = {}
    for attr_, is_dict in extractable_request_attributes:
        # earlier versions of pyramid may not have newer attrs
        # (ie, authenticated_userid)
        if not hasattr(request, attr_):
            continue
        value = None
        if is_dict and getattr(request, attr_):
            value = getattr(request, attr_).__dict__
        else:
            value = getattr(request, attr_)
        extracted_attributes[attr_] = value
    return extracted_attributes


class RequestVarsDebugPanel(DebugPanel):
    """
    A panel to display request variables (POST/GET, session, cookies, and
    ad-hoc request attributes).
    """
    name = 'request_vars'
    has_content = True
    template = 'pyramid_debugtoolbar.panels:templates/request_vars.dbtmako'
    title = _('Request Vars')
    nav_title = title

    def __init__(self, request):
        self.request = request
        self.data = data = {}
        attr_dict = request.__dict__.copy()
        # environ is displayed separately
        del attr_dict['environ']
        if 'response' in attr_dict:
            attr_dict['response'] = repr(attr_dict['response'])
        data.update({
            'get': [(k, request.GET.getall(k)) for k in request.GET],
            'post': [(k, saferepr(v)) for k, v in request.POST.items()],
            'cookies': [(k, request.cookies.get(k)) for k in request.cookies],
            'attrs': dictrepr(attr_dict),
            'environ': dictrepr(request.environ),
            'extracted_attributes': {},
        })
        if hasattr(request, 'session'):
            data.update({
                'session': dictrepr(request.session),
            })

    def process_response(self, response):
        extracted_attributes = extract_request_attributes(self.request)
        self.data['extracted_attributes'] = extracted_attributes

        # stop hanging onto the request after the response is processed
        del self.request
