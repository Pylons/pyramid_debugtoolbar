from pyramid.interfaces import ITweens

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import STATIC_PATH

_ = lambda x: x


class TweensDebugPanel(DebugPanel):
    """
    A panel to display the tweens used by your Pyramid application.
    """

    name = 'tweens'
    has_content = True
    template = 'pyramid_debugtoolbar.panels:templates/tweens.dbtmako'
    title = _('Tweens')
    nav_title = title

    def __init__(self, request):
        self.tweens = request.registry.queryUtility(ITweens)
        if self.tweens is None:
            self.has_content = False
            self.is_active = False
        else:
            self.populate(request)

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


def includeme(config):
    config.add_debugtoolbar_panel(TweensDebugPanel, is_global=True)
