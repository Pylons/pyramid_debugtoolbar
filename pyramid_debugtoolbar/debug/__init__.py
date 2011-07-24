# -*- coding: utf-8 -*-
"""
    werkzeug.debug
    ~~~~~~~~~~~~~~

    WSGI application traceback debugger.

    :copyright: (c) 2011 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from pyramid_debugtoolbar.debug.tbtools import (get_traceback,
                                                render_console_html)
from pyramid_debugtoolbar.debug.console import Console

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

class _ConsoleFrame(object):
    """Helper class so that we can reuse the frame console code for the
    standalone console.
    """

    def __init__(self, namespace):
        self.console = Console(namespace)
        self.id = 0


class DebuggedApplication(object):
    """Enables debugging support for a given application::

        from werkzeug.debug import DebuggedApplication
        from myapp import app
        app = DebuggedApplication(app, evalex=True)

    The `evalex` keyword argument allows evaluating expressions in a
    traceback's frame context.

    .. versionadded:: 0.7
       The `lodgeit_url` parameter was added.

    :param app: the WSGI application to run debugged.
    :param evalex: enable exception evaluation feature (interactive
                   debugging).  This requires a non-forking server.
    :param console_path: the URL for a general purpose console.
    :param console_init_func: the function that is executed before starting
                              the general purpose console.  The return value
                              is used as initial namespace.
    :param show_hidden_frames: by default hidden traceback frames are skipped.
                               You can show them by setting this parameter
                               to `True`.
    :param lodgeit_url: the base URL of the LodgeIt instance to use for
                        pasting tracebacks.
    """

    def __init__(self, evalex=False,  console_path='/console',
                 console_init_func=None, show_hidden_frames=False):
        if not console_init_func:
            console_init_func = dict
        self.evalex = evalex
        self.frames = {}
        self.tracebacks = {}
        self.console_path = console_path
        self.console_init_func = console_init_func
        self.show_hidden_frames = show_hidden_frames

    def debug_exception(self, info):
        traceback = get_traceback(info=info,
                                  skip=1, show_hidden_frames=
                                  self.show_hidden_frames,
                                  ignore_system_exceptions=True)
        for frame in traceback.frames:
            self.frames[frame.id] = frame
        self.tracebacks[traceback.id] = traceback
        yield traceback.render_full(evalex=self.evalex,
                                    lodgeit_url='').encode('utf-8', 'replace')

    def __call__(self, environ, start_response):
        """Dispatch the requests."""
        # important: don't ever access a function here that reads the incoming
        # form data!  Otherwise the application won't have access to that data
        # any more!
        request = Request(environ)
        response = self.debug_application
        if request.args.get('__debugger__') == 'yes':
            cmd = request.args.get('cmd')
            traceback = self.tracebacks.get(request.args.get('tb', type=int))
            frame = self.frames.get(request.args.get('frm', type=int))
            if cmd == 'paste' and traceback is not None:
                response = self.paste_traceback(request, traceback)
            elif cmd == 'source' and frame:
                response = self.get_source(request, frame)
            elif self.evalex and cmd is not None and frame is not None:
                response = self.execute_command(request, cmd, frame)
        elif self.evalex and self.console_path is not None and \
           request.path == self.console_path:
            response = self.display_console(request)
        return response(environ, start_response)

