from pprint import saferepr

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import dictrepr


_ = lambda x: x


# extractable_request_attributes allow us to programmatically pull data
# the format is...
#                                 ( attr_, is_show_dict, is_execute_method )
extractable_request_attributes = (
                                  ('accept_charset', None, None),
                                  ('accept_encoding', None, None),
                                  ('accept_language', None, None),
                                  ('application_url', None, None),
                                  ('authenticated_userid', None, None),
                                  ('authorization', None, None),
                                  ('cache_control', None, None),
                                  ('context', None, None),
                                  ('current_route_path', None, True),
                                  ('current_route_url', None, True),
                                  ('effective_principals', None, None),
                                  ('exc_info', None, None),
                                  ('exception', None, None),
                                  ('locale_name', None, None),
                                  ('matchdict', None, None),
                                  ('matched_route', True, None),
                                  # ('registry', None, None),  # see "Note1"
                                  ('root', None, None),
                                  ('subpath', None, None),
                                  ('traversed', None, None),
                                  ('unauthenticated_userid', None, None),
                                  ('view_name', None, None),
                                  ('virtual_root_path', None, None),
                                  ('virtual_root', None, None),
                                  )
# Note1: accessed as a 'string', `registry` be the python package name;
#                 as a dict, will be the contents of the registry


def extract_request_attributes(request):
    """
    Extracts useful request attributes from the ``request`` object into a dict.
    Data is serialized into a dict so that the original request is not longer
    needed.
    """
    extracted_attributes = {}
    for (attr_,
         is_show_dict,
         is_execute_method,
         ) in extractable_request_attributes:
        # earlier versions of pyramid may not have newer attrs
        # (ie, authenticated_userid)
        if not hasattr(request, attr_):
            continue
        value = None
        if is_show_dict and getattr(request, attr_):
            value = getattr(request, attr_).__dict__
        elif is_execute_method:
            value = getattr(request, attr_)()
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

    def process_beforerender(self, event):
        if 'req' in event:
            request = event['req']
            extracted_attributes = extract_request_attributes(request)
            self.data['extracted_attributes'] = extracted_attributes
