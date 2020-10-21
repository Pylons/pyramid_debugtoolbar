from pprint import saferepr

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import dictrepr

_ = lambda x: x

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
lazy_request_attributes = (
    ('authenticated_userid', False),
    ('effective_principals', False),
)
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
        attrs = request.__dict__.copy()
        # environ is displayed separately
        del attrs['environ']

        if 'response' in attrs:
            attrs['response'] = repr(attrs['response'])

        if 'session' in attrs:
            self.process_session_attr(attrs['session'])
            del attrs['session']
        else:
            # only process the session if it's accessed
            wrap_load(
                request,
                'session',
                self.process_session_attr,
                reify=True,
            )

        for attr_, is_dict in lazy_request_attributes:
            wrap_load(
                request,
                attr_,
                lambda v: self.process_lazy_attr(attr_, is_dict, v),
            )

        data.update(
            {
                'get': [(k, request.GET.getall(k)) for k in request.GET],
                'post': [(k, saferepr(v)) for k, v in request.POST.items()],
                'cookies': [
                    (k, request.cookies.get(k)) for k in request.cookies
                ],
                'environ': dictrepr(request.environ),
                'extracted_attributes': {},
                'attrs': dictrepr(attrs),
                'session': None,
            }
        )

    def process_session_attr(self, session):
        self.data.update(
            {
                'session': dictrepr(session),
            }
        )
        return session

    def process_lazy_attr(self, attr, is_dict, val_):
        if is_dict:
            val = val_.__dict__
        else:
            val = val_
        self.data['extracted_attributes'][attr] = val
        return val_

    def process_response(self, response):
        extracted_attributes = extract_request_attributes(self.request)
        self.data['extracted_attributes'].update(extracted_attributes)

        # stop hanging onto the request after the response is processed
        del self.request


def wrap_load(obj, name, cb, reify=False):
    """Callback when a property is accessed.

    This currently only works for reified properties that are called once.

    """
    orig_property = getattr(obj.__class__, name, None)
    if orig_property is None:
        # earlier versions of pyramid may not have newer attrs
        # (ie, authenticated_userid)
        return

    def wrapper(self):
        val = orig_property.__get__(obj)
        return cb(val)

    obj.set_property(wrapper, name=name, reify=reify)


def includeme(config):
    config.add_debugtoolbar_panel(RequestVarsDebugPanel)
