from collections import deque
import ipaddress
from itertools import islice
from logging import getLogger
import os.path
from pyramid.exceptions import ConfigurationError
from pyramid.path import DottedNameResolver
from pyramid.settings import asbool
import sys

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import SqlLexer
    from pygments.styles import get_style_by_name

    PYGMENT_STYLE = get_style_by_name('colorful')
    HAVE_PYGMENTS = True
except ImportError:  # pragma: no cover
    HAVE_PYGMENTS = False

SETTINGS_PREFIX = 'debugtoolbar.'
STATIC_PATH = 'pyramid_debugtoolbar:static/'
ROOT_ROUTE_NAME = 'debugtoolbar.root'
EXC_ROUTE_NAME = 'debugtoolbar.exception'

_marker = object()


class ToolbarStorage(deque):
    """Deque for storing Toolbar objects."""

    def __init__(self, max_elem):
        super(ToolbarStorage, self).__init__([], max_elem)

    def get(self, request_id, default=None):
        dict_ = dict(self)
        return dict_.get(request_id, default)

    def put(self, request_id, request):
        self.appendleft((request_id, request))

    def last(self, num_items):
        """Returns the last `num_items` Toolbar objects"""
        return list(islice(self, 0, num_items))


def format_fname(value, _sys_path=None):
    if _sys_path is None:
        _sys_path = sys.path  # dependency injection
    # If the value is not an absolute path, the it is a builtin or
    # a relative file (thus a project file).
    if not os.path.isabs(value):
        if value.startswith(('{', '<')):
            return value
        if value.startswith('.' + os.path.sep):
            return value
        return '.' + os.path.sep + value

    # Loop through sys.path to find the longest match and return
    # the relative path from there.
    prefix_len = 0
    value_segs = value.split(os.path.sep)
    for path in _sys_path:
        count = common_segment_count(path.split(os.path.sep), value_segs)
        if count > prefix_len:
            prefix_len = count
    return '<%s>' % os.path.sep.join(value_segs[prefix_len:])


def common_segment_count(path, value):
    """Return the number of path segments common to both"""
    i = 0
    if len(path) <= len(value):
        for x1, x2 in zip(path, value):
            if x1 == x2:
                i += 1
            else:
                return 0
    return i


def format_sql(query):
    if not HAVE_PYGMENTS:  # pragma: no cover
        return query

    return highlight(
        query,
        SqlLexer(encoding='utf-8'),
        HtmlFormatter(noclasses=True, style=PYGMENT_STYLE),
    )


def escape(s, quote=False):
    """Replace special characters "&", "<" and ">" to HTML-safe sequences.  If
    the optional flag `quote` is `True`, the quotation mark character is
    also translated.

    There is a special handling for `None` which escapes to an empty string.

    :param s: the string to escape.
    :param quote: set to true to also escape double quotes.
    """
    if s is None:
        return ''
    if hasattr(s, '__html__'):
        return s.__html__()
    if not isinstance(s, (str, bytes)):
        s = str(s)
    if isinstance(s, bytes):
        try:
            s.decode('ascii')
        except Exception:
            s = s.decode('utf-8', 'replace')
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    if quote:
        s = s.replace('"', "&quot;")
    return s


# http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
def replace_insensitive(string, target, replacement):
    """Similar to string.replace() but is case insensitive."""
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target) :]
    else:  # no results so return the original string
        return string


resolver = DottedNameResolver(None)


def as_cr_separated_list(value):
    if isinstance(value, str):
        value = list(filter(None, [x.strip() for x in value.splitlines()]))
    return value


def as_int(value):
    if isinstance(value, str):
        value = int(value)
    return value


def as_list(value):
    values = as_cr_separated_list(value)
    result = []
    for value in values:
        if isinstance(value, str):
            subvalues = value.split()
            result.extend(subvalues)
        else:
            result.append(value)
    return result


def as_display_debug_or_false(value):
    if isinstance(value, str):
        val = value.lower().strip()
        if val in ('display', 'debug'):
            return val
    b = asbool(value)
    if b:  # bw compat for dbt <=0.9
        return 'debug'
    return False


def get_setting(settings, name, default=None):
    return settings.get('%s%s' % (SETTINGS_PREFIX, name), default)


def dictrepr(d):
    out = {}
    for val in d:
        try:
            out[val] = repr(d[val])
        except Exception:
            # defensive
            out[val] = '<unknown>'
    try:
        return sorted(out.items())
    except TypeError:
        # Sorting can fail under Python3 if Types are not comparable.
        # For example `sorted(["a", float(0.1)])` will sort on Python2 but will
        # raise TypeError on Python3. As a fallback, try a second sort in which
        # keys are cast to a string when normal sorting fails with a TypeError.
        return sorted(out.items(), key=lambda k: str(k))


logger = getLogger('pyramid_debugtoolbar')


def addr_in(addr, hosts):
    addr = addr.split('%')[0]
    for host in hosts:
        if ipaddress.ip_address(u'' + addr) in ipaddress.ip_network(
            u'' + host
        ):
            return True
    return False


def debug_toolbar_url(request, *elements, **kw):
    return request.route_url('debugtoolbar', subpath=elements, **kw)


def make_subrequest(request, root_path, path, params=None):
    # we know root_path will have a trailing slash and
    # path will need one
    subrequest = type(request).blank(
        '/' + path,
        base_url=request.application_url + root_path[:-1],
    )
    if params is not None:
        subrequest.GET.update(params)
    return subrequest


def resolve_panel_classes(panels, is_global, panel_map):
    classes = []
    for panel in panels:
        if isinstance(panel, str):
            panel_class = panel_map.get((panel, is_global))
            if panel_class is None:
                panel_class = resolver.maybe_resolve(panel)

        else:
            panel_class = panel

        if panel_class is None:
            raise ConfigurationError(
                'failed to load debugtoolbar panel named %s' % panel
            )

        if panel_class not in classes:
            classes.append(panel_class)
    return classes


def get_exc_name(exc):
    cls = exc.__class__
    module = cls.__module__
    name = getattr(cls, '__qualname__', None)
    if name is None:
        name = cls.__name__
    if module == 'exceptions' or module == 'builtins':
        return name
    return '%s.%s' % (module, name)


def wrap_load(obj, name, cb, reify=False):
    """Callback when a property is accessed.

    This currently only works for reified properties that are called once.

    Originally written for the `Request Vars` panel.
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


# copied from pyramid.utils.InstancePropertyHelper but without any support
# for extra wrapping in properties, we want to keep that logic out of here
# so we can do crazy things like define magic methods (__getattribute__)
def patch_attrs(target, attrs):
    parent = target.__class__
    # fix the module name so it appears to still be the parent
    # e.g. pyramid.request instead of pyramid.util
    attrs.setdefault('__module__', parent.__module__)
    newcls = type(parent.__name__, (parent, object), attrs)
    # We assign __provides__ and __implemented__ below to prevent a
    # memory leak that results from from the usage of this instance's
    # eventual use in an adapter lookup.  Adapter lookup results in
    # ``zope.interface.implementedBy`` being called with the
    # newly-created class as an argument.  Because the newly-created
    # class has no interface specification data of its own, lookup
    # causes new ClassProvides and Implements instances related to our
    # just-generated class to be created and set into the newly-created
    # class' __dict__.  We don't want these instances to be created; we
    # want this new class to behave exactly like it is the parent class
    # instead.  See Pyramid GitHub issues #1212, #1529 and #1568 for more
    # information.
    for name in ('__implemented__', '__provides__'):
        # we assign these attributes conditionally to make it possible
        # to test this class in isolation without having any interfaces
        # attached to it
        val = getattr(parent, name, _marker)
        if val is not _marker:
            setattr(newcls, name, val)
    target.__class__ = newcls
