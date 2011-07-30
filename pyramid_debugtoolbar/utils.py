import os.path
import sys
from pyramid.util import DottedNameResolver

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import SqlLexer
    from pygments.styles import get_style_by_name
    PYGMENT_STYLE = get_style_by_name('colorful')
    HAVE_PYGMENTS = True
except ImportError: # pragma: no cover
    HAVE_PYGMENTS = False

SETTINGS_PREFIX = 'debugtoolbar.'
STATIC_PATH = 'pyramid_debugtoolbar:static/'
ROOT_ROUTE_NAME = 'debugtoolbar.root'

def format_fname(value, _sys_path=None):
    if _sys_path is None:
        _sys_path = sys.path # dependency injection
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
    if not HAVE_PYGMENTS: # pragma: no cover
        return query

    return highlight(
        query,
        SqlLexer(encoding='utf-8'),
        HtmlFormatter(encoding='utf-8', noclasses=True, style=PYGMENT_STYLE))

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
    elif hasattr(s, '__html__'):
        return s.__html__()
    elif not isinstance(s, basestring):
        s = unicode(s)
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    if quote:
        s = s.replace('"', "&quot;")
    return s

def replace_insensitive(string, target, replacement):
    """Similar to string.replace() but is case insensitive
    Code borrowed from: http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else: # no results so return the original string
        return string

resolver = DottedNameResolver(None)

def as_globals_list(value):
    L = []
    if isinstance(value, basestring):
        value = filter(None, [x.strip() for x in value.splitlines()])
    for dottedname in value:
        obj = resolver.resolve(dottedname)
        L.append(obj)
    return L

def get_setting(settings, name, default=None):
    return settings.get('%s%s' % (SETTINGS_PREFIX, name), default)
