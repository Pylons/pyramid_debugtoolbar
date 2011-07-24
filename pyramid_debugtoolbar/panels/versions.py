import sys
import pkg_resources
from operator import itemgetter
import platform

from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x

pyramid_version = pkg_resources.get_distribution('pyramid').version

class VersionDebugPanel(DebugPanel):
    """
    Panel that displays the Pyramid version.
    """
    name = 'Version'
    has_content = True

    def nav_title(self):
        return _('Versions')

    def url(self):
        return ''

    def title(self):
        return _('Versions')

    def content(self):
        packages = []
        for distribution in pkg_resources.working_set:
            name = distribution.project_name
            packages.append({'version':distribution.version,
                             'lowername':name.lower(),
                             'name':name})
        plat = 'Python %s on %s' % (sys.version, platform.platform())
        vars = {'platform':plat,
                'packages':sorted(packages, key=itemgetter('lowername'))}
        return self.render(
            'pyramid_debugtoolbar.panels:templates/versions.jinja2',
            vars, self.request)


