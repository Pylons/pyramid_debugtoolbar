Notes:

Package: https://github.com/Mottie/tablesorter
Version: 2.24.3 [2015.11.06]

* This is the contents of the /dist/ directory
* Currently only 3 files are used:
	/css/theme.bootstrap.min.css
	/js/jquery.tablesorter.min.js
	/js/jquery.tablesorter.widgets.min.js
* If this library updated, please update this README file with the current version as well

Integration points:

The file `toolbar.js` invokes this with a following call:

	// see http://mottie.github.io/tablesorter/docs/example-widget-bootstrap-theme.html
	$(".pDebugSortable").tablesorter({theme: "bootstrap",
									  widgets: ["uitheme", ],
									  headerTemplate: '{content} {icon}'
									  });

Aside from that, panels need only apple a `pDebugSortable` class to <table> tags.
