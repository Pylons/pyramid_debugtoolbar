
require.config({
	paths: {
		"jquery": "jquery-1.7.2.min",
        "tablesorter": "jquery.tablesorter.min",
        "toolbar": "toolbar"
	}
});

require([
	"jquery",
	"tablesorter",
	"toolbar"
	], function($, tablesorter, toolbar) {

    $(function() {
        pdtb.init();
        $(".pDebugSortable").tablesorter();
    });
});

define("main", function(){});