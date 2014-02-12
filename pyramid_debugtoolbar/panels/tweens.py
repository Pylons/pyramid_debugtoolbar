from pyramid.interfaces import ITweens

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import STATIC_PATH

_ = lambda x: x


class TweensDebugPanel(DebugPanel):
    """
    A panel to display the tweens used by your Pyramid application.
    """
    name = 'Tweens'
    has_content = True
    template = 'pyramid_debugtoolbar.panels:templates/tweens.dbtmako'

    def __init__(self, request):
        self.request = request
        self.tweens = request.registry.queryUtility(ITweens)
        if self.tweens is None:
            self.has_content = False
            self.is_active = False
        else:
            self.populate(request)

    def nav_title(self):
        return _('Tweens')

    def title(self):
        return _('Tweens')

    def url(self):
        return ''

    def populate(self, request):
        definition = 'Explicit'
        tweens = self.tweens.explicit
        if not tweens:
            tweens = self.tweens.implicit()
            definition = 'Implicit'
        self.data = {
            'tweens': tweens,
            'definition': definition,
            }

    def render_vars(self, request):
        return {'static_path': request.static_url(STATIC_PATH)}

