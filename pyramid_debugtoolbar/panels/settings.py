from operator import itemgetter

from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x


class SettingsDebugPanel(DebugPanel):
    """
    A panel to display Pyramid deployment settings for your application (the
    values in ``registry.settings``).
    """
    name = 'Settings'
    has_content = True

    filter_old_settings = [
        'debug_authorization',
        'debug_notfound',
        'debug_routematch',
        'debug_templates',
        'reload_templates',
        'reload_resources',
        'reload_assets',
        'default_locale_name',
        'prevent_http_cache',
    ]

    def __init__(self, request):
        self.request = request
        settings = request.registry.settings

        # filter out non-pyramid prefixed settings to avoid duplication
        if 'pyramid.default_locale_name' in settings:
            self.settings = sorted([
                (k, v) for k, v in request.registry.settings.items()
                if k not in self.filter_old_settings
            ], key=itemgetter(0))
        else:
            self.settings = sorted(request.registry.settings.items(),
                                   key=itemgetter(0))

    def nav_title(self):
        return _('Settings')

    def title(self):
        return _('Settings')

    def url(self):
        return ''

    def content(self):
        vars = {
            'settings': self.settings
        }
        return self.render(
            'pyramid_debugtoolbar.panels:templates/settings.jinja2',
            vars, self.request)
