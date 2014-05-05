from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import dictrepr
from pyramid_debugtoolbar.compat import text_

_ = lambda x: x

class RenderingsDebugPanel(DebugPanel):
    """
    Panel that displays the renderers (templates and 'static' renderers such
    as JSON) used during a request.
    """
    name = 'Template'
    renderings = ()
    template = 'pyramid_debugtoolbar.panels:templates/renderings.dbtmako'
    title = _('Renderers')
    nav_title = title

    @property
    def has_content(self):
        return bool(self.renderings)

    def process_beforerender(self, event):
        if not self.renderings:
            self.renderings = []
        name = event['renderer_info'].name
        if name and name.startswith('pyramid_debugtoolbar'):
            return
        val = getattr(event, 'rendering_val', '<unknown>')
        try:
            val = repr(val)
        except:
            # crazyass code raises an exception during __repr__ (formish)
            val = '<unknown>'
        self.renderings.append(
            dict(name=name, system=dictrepr(event), val=text_(val, 'utf-8'))
            )

    @property
    def nav_subtitle(self):
        num = len(self.renderings)
        return '%d' % (num)

    def process_response(self, response):
        self.data = {'renderings': self.renderings}

