try:
    import cProfile as profile
except ImportError:
    import profile
import pstats
import threading

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import format_fname

lock = threading.Lock()

class ProfilerDebugPanel(DebugPanel):
    """
    Panel that displays the time a response took with cProfile output.
    """
    name = 'Profiler'

    user_activate = True
    stats = None
    function_calls = None

    def __init__(self, request):
        self.request = request
        self.profiler = profile.Profile()

    def has_content(self):
        return bool(self.profiler)

    def wrap_handler(self, handler):
        if not self.is_active:
            return handler

        def profile_handler(request):
            with lock:
                try:
                    result = self.profiler.runcall(handler, request)
                except:
                    raise
                finally:
                    stats = pstats.Stats(self.profiler)
                    function_calls = []
                    flist = stats.sort_stats('cumulative').fcn_list
                    for func in flist:
                        current = {}
                        info = stats.stats[func]

                        # Number of calls
                        if info[0] != info[1]:
                            current['ncalls'] = '%d/%d' % (info[1], info[0])
                        else:
                            current['ncalls'] = info[1]

                        # Total time
                        current['tottime'] = info[2] * 1000

                        # Quotient of total time divided by number of calls
                        if info[1]:
                            current['percall'] = info[2] * 1000 / info[1]
                        else:
                            current['percall'] = 0

                        # Cumulative time
                        current['cumtime'] = info[3] * 1000

                        # Quotient of the cumulative time divded by the number
                        # of primitive calls.
                        if info[0]:
                            current['percall_cum'] = info[3] * 1000 / info[0]
                        else:
                            current['percall_cum'] = 0

                        # Filename
                        filename = pstats.func_std_string(func)
                        current['filename_long'] = filename
                        current['filename'] = format_fname(filename)
                        function_calls.append(current)

                    self.stats = stats
                    self.function_calls = function_calls

                return result

        return profile_handler

    def title(self):
        if not self.is_active:
            return "Profiler not active"
        return 'Request: %.2fms' % (float(self.stats.total_tt)*1000,)

    def nav_title(self):
        return 'Profiler'

    def nav_subtitle(self):
        if not self.is_active:
            return "in-active"
        return '%.2fms' % (float(self.stats.total_tt)*1000,)

    def url(self):
        return ''

    def content(self):
        if not self.is_active:
            return "The profiler is not activated, activate it to use it"
        vars = {
            'stats': self.stats,
            'function_calls': self.function_calls,
            }
        return self.render(
            'pyramid_debugtoolbar.panels:templates/profiler.jinja2',
            vars, request=self.request)

