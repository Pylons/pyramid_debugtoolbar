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
    template = 'pyramid_debugtoolbar.panels:templates/introspection.dbtmako'

    def __init__(self, request):
        introspector = request.registry.introspector
        categorized = introspector.categorized()
        self.data = {
            'categorized': categorized,
            'debug_repr': debug_repr,
            'object_description':object_description,
            'nl2br': nl2br}

    def nav_title(self):
        return _('Introspection')

    def title(self):
        return _('Introspection')

    def url(self):
        return ''

    def render_vars(self, request):
        return {'static_path': request.static_url(STATIC_PATH)}


def nl2br(s):
    return s.replace('\n', '<br/>')
