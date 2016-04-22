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

  bootstrap_panels = ['pDebugVersionPanel', 'pDebugHeaderPanel']

  for (var i = 0; i < bootstrap_panels.length; i++) {
    $('.pDebugWindow #' + bootstrap_panels[i] + '-content').show();
    $('li#' + bootstrap_panels[i]).addClass('active');
  }
});

$(function () {
  var source;
  function new_request(e) {
    $('ul#requests li a').tooltip('hide')
    var html = '<li><h4>Requests</strong></h4></li>';
    var requests = $('ul#requests');
    var data = JSON.parse(e.data);
    data.forEach(function (item) {
      var details = item[1];
      var request_id = item[0];
      var active = item[2];

      html += '<li class="'+active+'"><a href="'+window.DEBUG_TOOLBAR_ROOT_PATH+request_id+'" title="'+details.path+'">';
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
