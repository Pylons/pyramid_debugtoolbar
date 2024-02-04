from operator import itemgetter
import platform
import sys

from pyramid_debugtoolbar.panels import DebugPanel

try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata

_ = lambda x: x

packages = []
for distribution in metadata.distributions():
    name = distribution.metadata['Name']
    packages.append(
        {
            'version': distribution.version,
            'summary': distribution.metadata.get('Summary'),
            'lowername': name.lower(),
            'name': name,
        }
    )

packages = sorted(packages, key=itemgetter('lowername'))
pyramid_version = metadata.distribution('pyramid').version


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
        return 'Python %s on %s' % (sys.version, self._get_platform_name())


def includeme(config):
    config.add_debugtoolbar_panel(VersionDebugPanel, is_global=True)
