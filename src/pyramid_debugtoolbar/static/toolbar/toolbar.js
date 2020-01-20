var COOKIE_NAME_ACTIVE = 'pdtb_active';

function toggle_content(elem) {
  if (elem.is(':visible')) {
    elem.hide();
  } else {
    elem.show();
  }
}

function toggle_active(elem) {
  elem.toggleClass('active');
}

$(function() {
  // When clicked on the panels menu
  $(".pDebugPanels li:not(.disabled) a").click( function(event_) {
    event_.stopPropagation();
    $(".pDebugPanels li").removeClass("active");
    parent_ = $(this).parent();
    toggle_active(parent_);

    $(".panelContent").hide();
    $(".pDebugWindow").show();
    current = $('.pDebugWindow #' + parent_.attr('id') + '-content');
    current.show();
  });


  $('#settings .switchable').click(function() {
    var $panel = $(this).parent();
    var $this = $(this);
    var name = $this.attr('data-pdtb-panel');
    // Turn cookie content into an array of active panels
    var active_str = $.cookie(COOKIE_NAME_ACTIVE);
    var active = (active_str) ? active_str.split(' ') : [];
    active = $.grep(active, function(n,i) { return n != name; });
    if ($this.hasClass('active')) {
      $this.removeClass('active');
      $this.addClass('inactive');
    }
    else {
      active.push(name);
      $this.removeClass('inactive');
      $this.addClass('active');
    }
    if (active.length > 0) {
      $.cookie(COOKIE_NAME_ACTIVE, active.join(','), {
        path: '/', expires: 10
      });
    }
    else {
      $.cookie(COOKIE_NAME_ACTIVE, null, {
        path: '/', expires: -1
      });
    }
  });

  $(".pDebugSortable").tablesorter({
    theme: "bootstrap",
    widgets: ["uitheme"],
    headerTemplate: '{content} {icon}'
  });

  bootstrap_panels = ['pDebugVersionPanel', 'pDebugHeaderPanel'];

  for (var i = 0; i < bootstrap_panels.length; i++) {
    $('.pDebugWindow #' + bootstrap_panels[i] + '-content').show();
    $('li#' + bootstrap_panels[i]).addClass('active');
  }
});

$(function () {
  var source;
  function new_request(e) {
    $('ul#requests li a').tooltip('hide');
    var html = '<li><h4>Requests</strong></h4></li>';
    var requests = $('ul#requests');
    var data = JSON.parse(e.data);
    data.forEach(function (item) {
      var details = item[1];
      var request_id = item[0];
      var active = item[2];

      var title = details.host + details.path;
      html += '<li class="'+active+'"><a href="'+window.DEBUG_TOOLBAR_ROOT_PATH+request_id+'" title="'+title+'">';
      html += '<span class="badge pull-right _'+details.status_code+'">'+details.status_code+'</span>';
      html += details.method;
      if (details.scheme == 'https'){
        html += '&nbsp;<span class="badge"><span class="glyphicon glyphicon-lock" aria-hidden="true"></span></span>';
      }
      html += '<br>' + details.path;
      html += '</a></li>';
    });

    requests.html(html);
    $('ul#requests li a').tooltip({
      placement: 'right',
      container: 'body'
    });
  }

  function connectEventSource() {
    if (source) {
      source.close();
    }

    source = new EventSource(window.DEBUG_TOOLBAR_ROOT_PATH+'sse?request_id='+window.DEBUG_TOOLBAR_CURRENT_REQUEST_ID);
    source.addEventListener('new_request', new_request);
  }

  if (!!window.EventSource) {
    connectEventSource();
  }
});


/*
This provides for a global custom logging factory, somewhat similar to python's logging module.

A logger is instantiated with two arguments: label (string)  and debugging (boolean).

Log lines are prepended with a label and timestamp:

	[label timestamp] message

Example-

	The following custom logger:
		var logger = custom_logger_factory("debugtoolbar_stickypanel", 1);

	Will create this line:
		[debugtoolbar_stickypanel 1:13:54 PM] No cookied panel detected

	If the debugging is turned off
		var logger = custom_logger_factory("debugtoolbar_stickypanel", 0);

	There will be no output for this logger.

This factory allows authors to use verbose, partitioned, console logging during
development and troubleshooting, but suppress it on deployment.

*/
function CustomLoggerFactory(label, debugging_level) {
	if (!debugging_level){
		return(function() {return {log: function(){} }; }());
	}
	return (function () {
		var timestamp = function () {};
		timestamp.toString = function () {
			return "[" + label + ' ' + (new Date()).toLocaleTimeString() + "]";
		};
		return {log: console.log.bind(console, '%s', timestamp)};
	})();
}


/*
	Sticky Panel Functionality

	The functionality can be turned on/off via the global settings tab.
	A cookies is used to control this feature:
	* pdtb_sticky_panel_selected - the last selected panel
*/
$(function() {
	// custom logger
	var logger = CustomLoggerFactory("debugtoolbar_stickypanel", 0);

	// store active panel into this cookie
	var COOKIE_NAME_STICKYPANEL_SELECTED = 'pdtb_sticky_panel_selected';
	var cookied_panel = $.cookie(COOKIE_NAME_STICKYPANEL_SELECTED);

	// helper functions
	function show_panel(panel_tab_element, selected_panel_text){
		// show's the panel
		$(panel_tab_element).tab('show');
		// handle bootstrap incompatibility by invoking the content directly
		$("#"+selected_panel_text+'-content').show();
	}
	function get_displayable_panel(){
		// tries to find a displayable panel
		// returns a js object that contains the panel's tab element and text name
		logger.log('looking for an alternate panel...');
		var displayable = {"panel_tab_element": null,
						   "selected_panel_text": null
						   };
		var panel_tab_element = $('.pDebugPanels ul li').not('.disabled').first();
		if (panel_tab_element === undefined){
			return displayable;
		}
		var selected_panel_text = panel_tab_element.attr('id');
		displayable.panel_tab_element = panel_tab_element;
		displayable.selected_panel_text = selected_panel_text;
		return displayable;
	}
	function handle_alt_panel(do_cookie){
		// consolidates finding and showing an alternate panel
		// if do_cookie is ``true``, will set the new cookie as the default panel
		logger.log('handling alternate panel...');
		// set default value to false
		do_cookie = typeof do_cookie !== 'undefined' ? do_cookie : false;
		var displayable = get_displayable_panel();
		if (displayable.panel_tab_element && displayable.selected_panel_text) {
			show_panel(displayable.panel_tab_element, displayable.selected_panel_text);
			if (do_cookie){
				$.cookie(COOKIE_NAME_STICKYPANEL_SELECTED, displayable.selected_panel_text);
			}
		}
	}
	
	// only run the feature when activated, otherwise let bootstrap sort it out.
	if (cookied_panel){
		// activate the panel if it exists and is populated
		logger.log("Activating Debug Toolbar Panel : ", cookied_panel);
		// toolbar doesn't seem to use the normal bootstrap integration, so invoke two methods
		// the issue is that 2 identical #ids are generated : one on the `li`, one of the `li.a`
		var cookied_panel_tab = $("#"+cookied_panel);
		if (!cookied_panel_tab.length){
			logger.log('The toolbar panel is not on this screen');
			logger.log('I will set a new cookie value if possible...');
			handle_alt_panel(1);
		} else {
			if (cookied_panel_tab.hasClass('disabled')){
				logger.log('The toolbar panel is disabled on this view.');
				handle_alt_panel(0);
			} else {
				show_panel(cookied_panel_tab, cookied_panel);
			}
		}
	} else {
		logger.log('No cookied panel detected');
		handle_alt_panel(0);
	}

	// subscribe panels for recording the active panel in a cookie
	$(".pDebugPanels ul li a").click(function() {
		var selected_panel_text = $(this).parent().attr('id');
		if (selected_panel_text){
			$.cookie(COOKIE_NAME_STICKYPANEL_SELECTED, selected_panel_text);
		}
	});

});
