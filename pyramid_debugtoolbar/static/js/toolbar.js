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


jQuery(document).ready(function($) {


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


/*
	This next area is wrapped in a try block, because the call to `$(FOO).tablesorter`
	can cause a fatal javascript crash in some browsers IF jquery is not loaded.

	The current debugtoolbar implementation loads this file `toolbar.js` on both
	the toolbar view AND the interactive traceback view.  jquery is not included on
	the interactive traceback view; the inclusion of the next line has the potential
	to break the javascript engine on that page, rendering it unusable.
*/
try {
	// see http://mottie.github.io/tablesorter/docs/example-widget-bootstrap-theme.html
	$(".pDebugSortable").tablesorter({theme: "bootstrap",
									  widgets: ["uitheme", ],
									  headerTemplate: '{content} {icon}'
									  });
} catch (err){
	console.log("there was an error on applying the `pDebugSortable`");
}

bootstrap_panels = ['pDebugVersionPanel', 'pDebugHeaderPanel']
for (var i = 0; i < bootstrap_panels.length; i++) {
    $('.pDebugWindow #' + bootstrap_panels[i] + '-content').show();
    $('li#' + bootstrap_panels[i]).addClass('active');
}


});
