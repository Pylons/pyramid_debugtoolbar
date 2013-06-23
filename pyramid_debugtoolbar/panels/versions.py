import sys
import platform
import pkg_resources
from operator import itemgetter
from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.compat import text_

_ = lambda x: x

packages = []
for distribution in pkg_resources.working_set:
    name = distribution.project_name
    packages.append({'version': distribution.version,
                     'lowername': name.lower(),
                     'name': name})

packages = sorted(packages, key=itemgetter('lowername'))
pyramid_version = pkg_resources.get_distribution('pyramid').version


class VersionDebugPanel(DebugPanel):
    """
    Panel that displays the Python version, the Pyramid version, and the
    versions of other software on your PYTHONPATH.
    """
    name = 'Version'
    has_content = True

    def nav_title(self):
        return _('Versions')

    def url(self):
        return ''

    def title(self):
        return _('Versions')

    def _get_platform_name(self):
        return platform.platform()

    def get_platform(self):
        return 'Python %s on %s' % (sys.version,
                                    text_(self._get_platform_name(), 'utf8'))

    @property
    def properties(self):
        return {'platform': self.get_platform(), 'packages': packages}

    def content(self):
        return self.render(
            'pyramid_debugtoolbar.panels:templates/versions.dbtmako',
            self.properties, self.request)
