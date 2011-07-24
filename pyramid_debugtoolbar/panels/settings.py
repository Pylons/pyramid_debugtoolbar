from operator import itemgetter

from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x


class SettingsDebugPanel(DebugPanel):
    """
    A panel to display application settings.
    """
    name = 'Settings'
    has_content = True

    def nav_title(self):
        return _('Settings')

    def title(self):
        return _('Settings')

    def url(self):
        return ''

    def process_request(self, request):
        self.request = request
        self.settings = sorted(self.request.registry.settings.items(),
                               key=itemgetter(0))

    def content(self):
        vars = {
            'settings': self.settings
        }
        return self.render(
            'pyramid_debugtoolbar.panels:templates/settings.jinja2',
            vars, self.request)
