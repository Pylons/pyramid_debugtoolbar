from pyramid.decorator import reify
from pyramid.i18n import get_localizer
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request


class DebugPanel(object):
    """
    Base class for debug panels. A new instance of this class is created
    for every request.

    A panel is notified of events throughout the request lifecycle. It
    is then persisted and used later by the toolbar to render its results
    as a tab on the interface. The lifecycle hooks are available in the
    following order:

    - :meth:`.__init__`
    - :meth:`.wrap_handler`
    - :meth:`.process_beforerender`
    - :meth:`.process_response`

    Each of these hooks is overridable by a subclass to gleen information
    from the request and other events for later display.

    The panel is later used to render its results. This is done on-demand
    and in the lifecycle of a request to the debug toolbar by invoking
    :meth:`.render_content`. Any data stored within :attr:`.data` is
    injected into the template prior to rendering and is thus a common
    location to store the contents of previous events.
    """

    #: A unique identifier for the name of the panel. This **must** be
    #: defined by a subclass and be a valid Python variable name
    #: (something like ``[a-zA-Z0-9_-]+``).
    name = NotImplemented

    #: If ``False`` then the panel's tab will be disabled and
    #: :meth:`.render_content` will not be invoked. Most subclasses will
    #: want to set this to ``True``.
    has_content = False

    #: If the client is able to activate/de-activate the panel then this
    #: should be ``True``.
    user_activate = False

    #: This property will be set by the toolbar, indicating the user's
    #: decision to activate or deactivate the panel. If ``user_activate``
    #: is ``False`` then ``is_active`` will always be set to ``True``.
    is_active = False

    #: Must be overridden by subclasses that are using the default
    #: implementation of ``render_content``. This is an
    #: :term:`asset specification` pointing at the template to be rendered
    #: for the panel. Usually of the format
    #: ``'mylib:templates/panel.dbtmako'``.
    template = NotImplemented

    #: Title showing in toolbar. Must be overridden.
    nav_title = NotImplemented

    #: Subtitle showing until title in toolbar.
    nav_subtitle = ''

    #: CSS class used to give the subtitle a background color.
    nav_subtitle_style = ''

    #: Title showing in panel. Must be overridden.
    title = NotImplemented

    #: The URL invoked when the panel's tab is cliked. May be overridden to
    #: define an arbitrary URL for the panel or do some other custom action
    #: when the user clicks on the panel's tab in the toolbar.
    url = ''

    @reify
    def data(self):
        """A dictionary of data, updated during the request lifecycle, and
        later used to render the panel's HTML."""
        return {}

    # Panel methods
    def __init__(self, request):
        """Configure the panel for a request.

        :param request: The instance of :class:`pyramid.request.Request` that
                        this object is wrapping.
        """
        pass

    def render_content(self, request):
        """Return a string containing the HTML to be rendered for the panel.

        By default this will render the template defined by the
        :attr:`.template` attribute with a rendering context defined by
        :attr:`.data` combined with the ``dict`` returned from
        :meth:`.render_vars`.

        The ``request`` here is the active request in the toolbar. Not the
        original request that this panel represents.
        """
        data = self.data.copy()
        data.update(self.render_vars(request))
        return render(self.template, data, request=request)

    @property
    def dom_id(self):
        """The ``id`` tag of the panel's tab. May be used by CSS and
        Javascript to implement custom styles and actions.

        By default, the :attr:`.dom_id` for a panel with a :attr:`.name` of
        ``'performance'`` will be ``'pDebugPanel-performance'``.

        """
        return 'pDebugPanel-%s' % self.name

    def pluralize(self, singular, plural, n, domain=None, mapping=None):
        request = get_current_request()
        localizer = get_localizer(request)
        return localizer.pluralize(
            singular, plural, n, domain=domain, mapping=mapping
        )

    # Standard middleware methods
    def process_response(self, response):
        """Receives the response generated by the request.

        Override this method to track properties of the response."""
        pass

    def process_beforerender(self, event):
        """Receives every :class:`pyramid.events.BeforeRender`
        event invoked during the request/response lifecycle of the request.

        Override this method to track properties of the rendering events.
        """
        pass

    def wrap_handler(self, handler):
        """May be overridden to monitor the entire lifecycle of the request.

        A handler receives a request and returns a response. An example
        implementation may be:

        .. code-block:: python

           def wrap_handler(self, handler):
               def wrapper(request):
                   start_time = time.monotonic()
                   response = handler(request)
                   end_time = time.monotonic()
                   self.data['duration'] = end_time - start_time
                   return response
               return wrapper
        """
        return handler

    def render_vars(self, request):
        """Invoked by the default implementation of :meth:`.render_content`
        and should return a ``dict`` of values to use when rendering the
        panel's HTML content. This value is usually injected into templates
        as the rendering context.

        The ``request`` here is the active request in the toolbar. Not the
        original request that this panel represents.
        """
        return {}
