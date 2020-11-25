import binascii
from collections import deque
import ipaddress
from itertools import islice
from logging import getLogger
import os.path
from pyramid.exceptions import ConfigurationError
from pyramid.path import DottedNameResolver
from pyramid.settings import asbool
import sys

from pyramid_debugtoolbar.compat import (
    binary_type,
    bytes_,
    string_types,
    text_,
    text_type,
)

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
        return text_(query)

    return text_(
        highlight(
            query,
            SqlLexer(encoding='utf-8'),
            HtmlFormatter(
                encoding='utf-8', noclasses=True, style=PYGMENT_STYLE
            ),
        )
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
    if not isinstance(s, (text_type, binary_type)):
        s = text_type(s)
    if isinstance(s, binary_type):
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
    """ Similar to string.replace() but is case insensitive."""
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target) :]
    else:  # no results so return the original string
        return string


resolver = DottedNameResolver(None)


def as_cr_separated_list(value):
    if isinstance(value, string_types):
        value = list(filter(None, [x.strip() for x in value.splitlines()]))
    return value


def as_int(value):
    if isinstance(value, string_types):
        value = int(value)
    return value


def as_list(value):
    values = as_cr_separated_list(value)
    result = []
    for value in values:
        if isinstance(value, string_types):
            subvalues = value.split()
            result.extend(subvalues)
        else:
            result.append(value)
    return result


def as_display_debug_or_false(value):
    if isinstance(value, string_types):
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


def hexlify(value):
    """Hexlify int, str then returns native str type."""
    # If integer
    str_ = str(value)
    hexified = text_(binascii.hexlify(bytes_(str_)))
    return hexified


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
        if isinstance(panel, string_types):
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
