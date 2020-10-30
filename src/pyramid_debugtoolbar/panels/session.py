import pprint

from pyramid_debugtoolbar.panels import DebugPanel

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

    @property
    def has_content(self):
        return self.__request and hasattr(self.__request, "session")

    # used to store the request for response processing
    __request = None

    def __init__(self, request):
        self.data = {
            "configuration": None,
            "session_data": {
                "in": {},
                "out": {},
                "keys": set([]),
                "changed": set([]),
            },
            "NotInSession": NotInSession,
        }
        if hasattr(request, "session"):
            # this collects all the incoming data without binding to the request
            for k, v in request.session.items():
                v = pprint.pformat(v)
                self.data["session_data"]["in"][k] = v
                self.data["session_data"]["keys"].add(k)

        # we need this for processing in the response phase
        self.__request = request

    def process_response(self, response):
        if self.__request:
            if hasattr(self.__request, "session"):
                for k, v in self.__request.session.items():
                    v = pprint.pformat(v)
                    self.data["session_data"]["out"][k] = v
                    self.data["session_data"]["keys"].add(k)
                    if (k not in self.data["session_data"]["in"]) or (
                        self.data["session_data"]["in"][k] != v
                    ):
                        self.data["session_data"]["changed"].add(k)


def includeme(config):
    config.add_debugtoolbar_panel(SessionDebugPanel)
