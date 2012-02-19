from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.repr import debug_repr

try:
    from pyramid.interfaces import IIntrospector
    IIntrospector = IIntrospector # pyflakes
    from pyramid.util import object_description
except ImportError: # pragma: no cover
    has_content = False
else:
    has_content = True
    

_ = lambda x: x

class IntrospectionDebugPanel(DebugPanel):
    """
    A panel to display generic Pyramid introspection info.
    """
    name = 'Introspection'
    has_content = has_content
    is_active = not has_content

    def __init__(self, request):
        self.request = request

    def nav_title(self):
        return _('Introspection')

    def title(self):
        return _('Introspection')

    def url(self):
        return ''

    def content(self):
        introspector = self.request.registry.introspector
        categorized = introspector.categorized()
        static_path = self.request.static_url(STATIC_PATH)
        vars = {
            'categorized':categorized, 'debug_repr':debug_repr,
            'static_path':static_path, 'object_description':object_description,
            'nl2br':nl2br}
        return self.render(
            'pyramid_debugtoolbar.panels:templates/introspection.dbtmako',
            vars, self.request)

def nl2br(s):
    return s.replace('\n', '<br/>')
