pyramid_debugtoolbar_require.config({
  paths: {
    "jquery": "jquery-1.7.2.min",
    "tablesorter": "jquery.tablesorter.min",
  }
});

pyramid_debugtoolbar_require([
    "jquery",
    "tablesorter"], function($, tablesorter) {

      $(function() {

      var pdtb = {

          events: {
            ready: []
          },

      init: function() {

      $("#pDebugPanels li a").click( function() {
          $("#pDebugPanels li ").removeClass("active");
          parent_ = $(this).parent();
          pdtb.toggle_active(parent_);

          $(".panelContent").hide();
          $("#pDebugWindow").show();
          current = $('#pDebugWindow #' + parent_.attr('id') + '-content');
          current.show();
      });

      },

      toggle_content: function(elem) {
        if (elem.is(':visible')) {
          elem.hide();
        } else {
          elem.show();
        }
      },

      toggle_active: function(elem) {
          elem.toggleClass('active');
      },

      };
        $(document).ready(function() {
          pdtb.init();
          $(".pDebugSortable").tablesorter();

          current = $('#pDebugWindow #' + 'pDebugVersionPanel' + '-content');
          current.show();
          $('li#pDebugVersionPanel').addClass('active');

        });
      });

      $.noConflict(true);
    });
