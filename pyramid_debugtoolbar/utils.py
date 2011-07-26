import os.path
import sys
from pyramid.util import DottedNameResolver

SETTINGS_PREFIX = 'debugtoolbar.'
STATIC_PATH = 'pyramid_debugtoolbar:static/'

def format_fname(value):
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
    prefix = None
    prefix_len = 0
    for path in sys.path:
        new_prefix = os.path.commonprefix([path, value])
        if len(new_prefix) > prefix_len:
            prefix = new_prefix
            prefix_len = len(prefix)

    if not prefix.endswith(os.path.sep): # pragma: no cover
        prefix_len -= 1
    path = value[prefix_len:]
    return '<%s>' % path

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
