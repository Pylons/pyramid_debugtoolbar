from pprint import saferepr

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import dictrepr, patch_attrs

_ = lambda x: x

_marker = object()

# extractable_request_attributes allow us to programmatically pull data
# the format is (attr, is_dict)
extractable_request_attributes = (
    ('accept_charset', False),
    ('accept_encoding', False),
    ('accept_language', False),
    ('application_url', False),
    ('authorization', False),
    ('cache_control', False),
    ('context', False),
    ('exc_info', False),
    ('exception', False),
    ('locale_name', False),
    ('matchdict', False),
    ('matched_route', True),
    ('path', False),
    # ('registry', False),  # see "Note1"
    ('root', False),
    ('subpath', False),
    ('traversed', False),
    ('url', False),
    ('view_name', False),
    ('virtual_root_path', False),
    ('virtual_root', False),
)
# Avoid touching these attributes until they are explicitly loaded in the
# request lifecycle. They can have some nasty side-effects otherwise.
lazy_request_attributes = {
    'authenticated_userid': False,
    'effective_principals': False,
}
# Note1: accessed as a 'string', `registry` be the python package name;
#        accessed as a dict, will be the contents of the registry

# Note2: only request attributes and properties are supported.  all known
#        'read' methods have properties that show the same info
#        For example `request.current_url()` is essentially `request.url`


def extract_request_attributes(request):
    """
    Extracts useful request attributes from the ``request`` object into a dict.
    Data is serialized into a dict so that the original request is no longer
    needed.
    """
    extracted_attributes = {}
    for attr_, is_dict in extractable_request_attributes:
        value = getattr(request, attr_, _marker)
        # earlier versions of pyramid may not have newer attrs
        # (ie, authenticated_userid)
        if value is _marker:
            continue
        if is_dict and value:
            value = value.__dict__
        extracted_attributes[attr_] = value
    return extracted_attributes


class RequestVarsDebugPanel(DebugPanel):
    """
    A panel to display request variables (POST/GET, cookies, and
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
        attrs = request.__dict__.copy()
        # environ is displayed separately
        del attrs['environ']

        if 'response' in attrs:
            attrs['response'] = repr(attrs['response'])

        install_attribute_listener(request, self.save_lazy_attribute)

        # safely displaying the POST information is a bit tedious
        post_variables = None
        post_body_info = {
            'size': len(request.body),
            'preview_bytes': None,
        }
        try:
            post_variables = [
                (saferepr(k), saferepr(v)) for k, v in request.POST.items()
            ]
        except Exception:
            pass
        if not post_variables and request.body:
            # try to convert the POST data if it is text...
            try:
                _post_converted = request.text
            except Exception:
                _post_converted = "[... %s bytes (%s) ...]" % (
                    request.content_length,
                    request.content_type,
                )
            _post_preview_bytes = (
                _post_converted[:4096] if _post_converted else None
            )
            post_body_info['preview_bytes'] = _post_preview_bytes

        data.update(
            {
                'get': [(k, request.GET.getall(k)) for k in request.GET],
                'post': post_variables,
                'post_body_info': post_body_info,
                'cookies': [
                    (k, request.cookies.get(k)) for k in request.cookies
                ],
                'environ': dictrepr(request.environ),
                'extracted_attributes': {},
                'attrs': dictrepr(attrs),
            }
        )

    def save_lazy_attribute(self, item, value):
        is_dict = lazy_request_attributes.get(item, _marker)
        if is_dict is _marker:
            return
        if is_dict and value:
            value = value.__dict__
        self.data['extracted_attributes'][item] = value

    def process_response(self, response):
        extracted_attributes = extract_request_attributes(self.request)
        self.data['extracted_attributes'].update(extracted_attributes)

        # stop hanging onto the request after the response is processed
        del self.request


def install_attribute_listener(target, cb):
    orig_getattribute = target.__class__.__getattribute__

    def patched_getattribute(self, item):
        value = orig_getattribute(self, item)
        cb(item, value)
        return value

    patch_attrs(target, {'__getattribute__': patched_getattribute})


def includeme(config):
    config.add_debugtoolbar_panel(RequestVarsDebugPanel)
