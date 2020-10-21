# flake8: noqa F401
import sys
import types

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3:  # pragma: no cover
    string_types = (str,)
    integer_types = (int,)
    class_types = (type,)
    text_type = str
    binary_type = bytes
    long = int
else:
    string_types = (basestring,)
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str
    long = long

# TODO check if errors is ever used


def text_(s, encoding='latin-1', errors='strict'):
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    return s  # pragma: no cover


def bytes_(s, encoding='latin-1', errors='strict'):
    if isinstance(s, text_type):  # pragma: no cover
        return s.encode(encoding, errors)
    return s


if PY3:  # pragma: no cover

    def native_(s, encoding='latin-1', errors='strict'):
        if isinstance(s, text_type):
            return s
        return str(s, encoding, errors)


else:

    def native_(s, encoding='latin-1', errors='strict'):
        if isinstance(s, text_type):  # pragma: no cover
            return s.encode(encoding, errors)
        return str(s)


if PY3:  # pragma: no cover
    import builtins

    exec_ = getattr(builtins, "exec")

    def reraise(exc_info):
        etype, exc, tb = exc_info
        if exc.__traceback__ is not tb:
            raise exc.with_traceback(tb)
        raise exc


else:  # pragma: no cover

    def exec_(code, globs=None, locs=None):
        """Execute code in a namespace."""
        if globs is None:
            frame = sys._getframe(1)
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec("""exec code in globs, locs""")

    exec_(
        """def reraise(exc_info):
    raise exc_info[0], exc_info[1], exc_info[2]
"""
    )

if PY3:  # pragma: no cover
    from io import BytesIO, StringIO
else:
    from StringIO import StringIO

    BytesIO = StringIO

if PY3:  # pragma: no cover
    import builtins

    exec_ = getattr(builtins, "exec")

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    del builtins

else:  # pragma: no cover

    def exec_(code, globs=None, locs=None):
        """Execute code in a namespace."""
        if globs is None:
            frame = sys._getframe(1)
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec("""exec code in globs, locs""")

    exec_(
        """def reraise(tp, value, tb=None):
    raise tp, value, tb
"""
    )

if PY3:  # pragma: no cover
    from urllib import parse

    urlparse = parse
    from urllib.parse import (
        quote as url_quote,
        quote_plus as url_quote_plus,
        unquote as url_unquote,
        urlencode as url_encode,
    )
    from urllib.request import urlopen as url_open
else:
    from urllib2 import urlopen as url_open
    from urllib import (
        quote as url_quote,
        quote_plus as url_quote_plus,
        unquote as url_unquote,
        urlencode as url_encode,
    )
    import urlparse

if PY3:  # pragma: no cover
    xrange_ = range
else:
    xrange_ = xrange


if PY3:  # pragma: no cover

    def iteritems_(d):
        return d.items()


else:

    def iteritems_(d):
        return d.iteritems()


try:
    import json
except ImportError:  # pragma: no cover
    try:
        import simplejson as json
    except NotImplementedError:
        from django.utils import simplejson as json  # GAE
