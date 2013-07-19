"""Base DebugPanel class"""

from pyramid.i18n import get_localizer
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request


class DebugPanel(object):
    """
    Base class for debug panels.
    """
    # name = Base
    has_content = False # If content returns something, set to true in subclass

    # If the client is able to activate/de-activate the panel
    user_activate = False

    # Default to is_active = False
    is_active = False

    # Must be overridden
    template = NotImplemented

    # Panel methods
    def __init__(self, request):
        pass

    def render_content(self, request):
        data = self.data.copy()
        data.update(self.render_vars(request))
        return render(self.template, data, request=request)

    def dom_id(self):
        return 'pDebug%sPanel' % (self.name.replace(' ', ''))

    def nav_title(self):
        """Title showing in toolbar"""
        raise NotImplementedError

    def nav_subtitle(self):
        """Subtitle showing until title in toolbar"""
        return ''

    def title(self):
        """Title showing in panel"""
        raise NotImplementedError

    def url(self):
        raise NotImplementedError

    def pluralize(self, singular, plural, n, domain=None, mapping=None):
        request = get_current_request()
        localizer = get_localizer(request)
        return localizer.pluralize(singular, plural, n, domain=domain,
                                   mapping=mapping)

    # Standard middleware methods
    def process_response(self, response):
        pass

    def process_beforerender(self, event):
        pass

    def wrap_handler(self, handler):
        return handler

    def render_vars(self, request):
        return {}
