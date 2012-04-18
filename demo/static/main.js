
require.config({
  paths: {
    "jquery": "jquery-1.7.2.min",
    "toolbar": "/_debug_toolbar/static/js/toolbar"
  }
});

require(["jquery", "toolbar"], function($, toolbar) {
  $(function() {
    console.log('TEST REQUIREJS');
  });
});

define("main", function(){});
