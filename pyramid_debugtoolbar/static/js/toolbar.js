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

$(document).ready(function() {


$("#pDebugPanels li a").click( function(event_) {
    event_.stopPropagation();
    $("#pDebugPanels li ").removeClass("active");
    parent_ = $(this).parent();
    toggle_active(parent_);

    $(".panelContent").hide();
    $("#pDebugWindow").show();
    current = $('#pDebugWindow #' + parent_.attr('id') + '-content');
    current.show();
});


$('#pDebugPanels li a .switch').click(function() {
  console.log("borg click");
  var $panel = $(this).parent();
  var $this = $(this);
  var dom_id = $panel.attr('id');
  // Turn cookie content into an array of active panels
  var active_str = $.cookie(COOKIE_NAME_ACTIVE);
  var active = (active_str) ? active_str.split(';') : [];
  active = $.grep(active, function(n,i) { return n != dom_id; });
  if ($this.hasClass('active')) {
    $this.removeClass('active');
    $this.addClass('inactive');
  }
  else {
    active.push(dom_id);
    $this.removeClass('inactive');
    $this.addClass('active');
  }
  if (active.length > 0) {
    $.cookie(COOKIE_NAME_ACTIVE, active.join(';'), {
        path: '/', expires: 10
    });
  }
  else {
    $.cookie(COOKIE_NAME_ACTIVE, null, {
      path: '/', expires: -1
    });
  }
});

$(".pDebugSortable").tablesorter();

current = $('#pDebugWindow #' + 'pDebugVersionPanel' + '-content');
current.show();
$('li#pDebugVersionPanel').addClass('active');

});

