from operator import itemgetter
import pkg_resources
import platform
import sys

from pyramid_debugtoolbar.compat import text_
from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x

packages = []
for distribution in pkg_resources.working_set:
    name = distribution.project_name
    packages.append(
        {
            'version': distribution.version,
            'location': distribution.location,
            'lowername': name.lower(),
            'name': name,
        }
    )

packages = sorted(packages, key=itemgetter('lowername'))
pyramid_version = pkg_resources.get_distribution('pyramid').version


class VersionDebugPanel(DebugPanel):
    """
    Panel that displays the Python version, the Pyramid version, and the
    versions of other software on your PYTHONPATH.
    """

    name = 'versions'
    has_content = True
    template = 'pyramid_debugtoolbar.panels:templates/versions.dbtmako'
    title = _('Versions')
    nav_title = title

    def __init__(self, request):
        self.data = {
            'platform': self.get_platform(),
            'packages': packages,
        }

    def _get_platform_name(self):
        return platform.platform()

    def get_platform(self):
        return 'Python %s on %s' % (
            sys.version,
            text_(self._get_platform_name(), 'utf8'),
        )


def includeme(config):
    config.add_debugtoolbar_panel(VersionDebugPanel, is_global=True)
