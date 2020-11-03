import pprint

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid.interfaces import ISession

_ = lambda x: x


class NotInSession(object):
    pass


class SessionDebugPanel(DebugPanel):
    """
    A panel to display Pyramid's ISession data.
    """

    name = 'session'
    template = 'pyramid_debugtoolbar.panels:templates/session.dbtmako'
    title = _('Session')
    nav_title = title
    user_activate = True

    @property
    def has_content(self):
        """
        This is too difficult to figure out under the following parameters:
        * Do not trigger the iSession interface
        * The toolbar consults this attibute relatively early in the lifecycle
          to determine if `.is_active` should be `True`
        """
        return True

    # used to store the request for processing
    _request = None

    def __init__(self, request):
        """
        initial setup of the `data` payload
        """
        self.data = {
            # "configuration": None,
            "session_accessed": {
                "pre": None,  # pre-processing (toolbar)
                "main": None,  # during request processing
                "post": None,  # post-processing (tooolbar)
                "panel_setup": None,  # did the panel setup?
            },
            "session_data": {
                "in": {},
                "out": {},
                "keys": set([]),
                "changed": set([]),
            },
            "NotInSession": NotInSession,
        }
        # we need this for processing in the response phase
        self._request = request

    def wrap_handler(self, handler):
        """
        `wrap_handler` allows us to monitor the entire lifecycle of the Request.

        Instead of using this hook to create a new wrapped handler, we can just
        do the required analysis right here, and then invoke the original
        handler.

        REQUEST | "in"
        Only process the REQUEST if the panel is active, or if the ``Session``
        has already been accessed, as the REQUEST requires activating the
        ``Session`` interface

        This is a two-phased analysis, because we may trigger a generic
        ``AttributeError`` when accessing the ``Session`` if no ``Session``
        was configured
        """
        if "session" in self._request.__dict__:
            # mark it as accessed
            self.data["session_accessed"]["pre"] = True

        _process_session = False
        session = {}
        if self.is_active or ("session" in self._request.__dict__):
            try:
                session = self._request.session
                _process_session = True
                self.data["session_accessed"]["panel_setup"] = True
            except AttributeError:
                # the session is not configured
                pass

        if _process_session:
            _data = self.data
            for k, v in session.items():
                v = pprint.pformat(v)
                _data["session_data"]["in"][k] = v
                _data["session_data"]["keys"].add(k)

            # If the ``Session`` was not already loaded, then we just
            # loaded it. This presents a problem for tracking, as we
            # will not know if the ``Session`` was accessed or not.
            # To handle this scenario, we use a variant of the ``wrap_load``
            # function from the request_vars tolbar:

            # This function just updates our information ``dict``,
            # and then returns the ``Session`` we just loaded
            def _session_wrapper(self):
                _data["session_accessed"]["main"] = True
                return session

            # delete the loaded session, and replace it with
            # the function above
            del self._request.__dict__["session"]
            self._request.set_property(
                _session_wrapper, name="session", reify=True
            )

        return handler

    def process_response(self, response):
        """
        RESPONSE | "out"
        only process the RESPONSE if the panel is active, OR if the session
        was accessed, as processing the RESPONSE requires opening the session
        """
        if self._request is None:
            # this scenario can happen if there is an error in the toolbar
            return

        if self.is_active or ("session" in self._request.__dict__):
            try:
                if "session" not in self._request.__dict__:
                    # the ``Session`` is not already loaded, so we should
                    # mark it as being loaded within the "post" phase.
                    self.data["session_accessed"]["post"] = True
                _session = self._request.session
                for k, v in _session.items():
                    v = pprint.pformat(v)
                    self.data["session_data"]["out"][k] = v
                    self.data["session_data"]["keys"].add(k)
                    if self.data["session_accessed"]["panel_setup"]:
                        # we can not detect `changed` values unless we process
                        # the ``Session`` during the "pre" hook.
                        if (k not in self.data["session_data"]["in"]) or (
                            self.data["session_data"]["in"][k] != v
                        ):
                            self.data["session_data"]["changed"].add(k)
            except AttributeError:
                # the session is not configured
                pass


def includeme(config):
    config.add_debugtoolbar_panel(SessionDebugPanel)
