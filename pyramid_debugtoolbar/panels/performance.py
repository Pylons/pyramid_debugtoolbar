from __future__ import with_statement

try:
    import cProfile as profile
except ImportError: # pragma: no cover
    try:
        import profile
    except ImportError: # pragma: no cover
        profile = None
try:
    import resource
except ImportError: # pragma: no cover
    resource = None # Will fail on Win32 systems
try:
    import pstats
except ImportError: # pragma: no cover
    pstats = None # will fail on braindead Debian systems that package pstats
                  # separately from python for god-knows-what-reason

import threading
import time

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import format_fname

_ = lambda x: x

lock = threading.Lock()

class PerformanceDebugPanel(DebugPanel):
    """
    Panel that looks at the performance of a request.

    It will display the time a request took and, optionally, the
    cProfile output.
    """
    name = 'Performance'
    user_activate = True
    stats = None
    function_calls = None
    has_resource = bool(resource)
    has_content = bool(pstats and profile)
    template = 'pyramid_debugtoolbar.panels:templates/performance.dbtmako'

    def __init__(self, request):
        if profile is not None:
            self.profiler = profile.Profile()

    def _wrap_timer_handler(self, handler):
        if self.has_resource:
            def resource_timer_handler(request):
                _start_time = time.time()
                self._start_rusage = resource.getrusage(resource.RUSAGE_SELF)
                try:
                    result = handler(request)
                except:
                    raise
                finally:
                    self._end_rusage = resource.getrusage(resource.RUSAGE_SELF)
                    self.total_time = (time.time() - _start_time) * 1000

                return result

            return resource_timer_handler

        def noresource_timer_handler(request):
            _start_time = time.time()
            try:
                result = handler(request)
            except:
                raise
            finally:
                self.total_time = (time.time() - _start_time) * 1000
            return result

        return noresource_timer_handler

    def _wrap_profile_handler(self, handler):
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

    def wrap_handler(self, handler):
        handler = self._wrap_profile_handler(handler)
        handler = self._wrap_timer_handler(handler)
        return handler

    def title(self):
        return _('Performance')

    def nav_title(self):
        return _('Performance')

    def nav_subtitle(self):
        return '%0.2fms' % (self.total_time)

    def url(self):
        return ''

    def _elapsed_ru(self, name):
        return getattr(self._end_rusage, name) - getattr(self._start_rusage,
                                                         name)

    def process_response(self, response):
        vars = {'timing_rows':None, 'stats':None, 'function_calls':[]}
        if self.has_resource:
            utime = 1000 * self._elapsed_ru('ru_utime')
            stime = 1000 * self._elapsed_ru('ru_stime')
            vcsw = self._elapsed_ru('ru_nvcsw')
            ivcsw = self._elapsed_ru('ru_nivcsw')
            ## minflt = self._elapsed_ru('ru_minflt')
            ## majflt = self._elapsed_ru('ru_majflt')

# these are documented as not meaningful under Linux.  If you're running BSD
# feel free to enable them, and add any others that I hadn't gotten to before
# I noticed that I was getting nothing but zeroes and that the docs agreed. :-(
#
#            blkin = self._elapsed_ru('ru_inblock')
#            blkout = self._elapsed_ru('ru_oublock')
#            swap = self._elapsed_ru('ru_nswap')
#            rss = self._end_rusage.ru_maxrss
#            srss = self._end_rusage.ru_ixrss
#            urss = self._end_rusage.ru_idrss
#            usrss = self._end_rusage.ru_isrss

            # TODO l10n on values
            rows = (
                (_('User CPU time'), '%0.3f msec' % utime),
                (_('System CPU time'), '%0.3f msec' % stime),
                (_('Total CPU time'), '%0.3f msec' % (utime + stime)),
                (_('Elapsed time'), '%0.3f msec' % self.total_time),
                (_('Context switches'), '%d voluntary, %d involuntary' % (
                    vcsw, ivcsw)),
#                (_('Memory use'), '%d max RSS, %d shared, %d unshared' % (
#                    rss, srss, urss + usrss)),
#                (_('Page faults'), '%d no i/o, %d requiring i/o' % (
#                    minflt, majflt)),
#                (_('Disk operations'), '%d in, %d out, %d swapout' % (
#                    blkin, blkout, swap)),
            )
            vars['timing_rows'] = rows
        if self.is_active:
            vars['stats'] = self.stats
            vars['function_calls'] = self.function_calls
        self.data = vars
