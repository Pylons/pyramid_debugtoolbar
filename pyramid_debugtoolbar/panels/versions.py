import pkg_resources

from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x

pyramid_version = pkg_resources.get_distribution('pyramid').version

class VersionDebugPanel(DebugPanel):
    """
    Panel that displays the Pyramid version.
    """
    name = 'Version'
    has_content = False

    def nav_title(self):
        return _('Versions')

    def nav_subtitle(self):
        return 'Pyramid %s' % pyramid_version

    def url(self):
        return ''

    def title(self):
        return _('Versions')

    def content(self):
        return None


