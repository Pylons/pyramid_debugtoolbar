(function($) {
    $.cookie = function(name, value, options) { if (typeof value != 'undefined') { options = options || {}; if (value === null) { value = ''; options.expires = -1; } var expires = ''; if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) { var date; if (typeof options.expires == 'number') { date = new Date(); date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000)); } else { date = options.expires; } expires = '; expires=' + date.toUTCString(); } var path = options.path ? '; path=' + (options.path) : ''; var domain = options.domain ? '; domain=' + (options.domain) : ''; var secure = options.secure ? '; secure' : ''; document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join(''); } else { var cookieValue = null; if (document.cookie && document.cookie != '') { var cookies = document.cookie.split(';'); for (var i = 0; i < cookies.length; i++) { var cookie = $.trim(cookies[i]); if (cookie.substring(0, name.length + 1) == (name + '=')) { cookieValue = decodeURIComponent(cookie.substring(name.length + 1)); break; } } } return cookieValue; } };
    $('head').append('<link rel="stylesheet" href="'+DEBUG_TOOLBAR_STATIC_PATH+'css/toolbar.css?'+ Math.random() +'" type="text/css" />');
    var COOKIE_NAME = 'p_dt';
    var COOKIE_NAME_ACTIVE = COOKIE_NAME +'_active';
    var p_dt = {
        init: function() {
            $('#pDebug').show();
            var current = null;
            $('#pDebugPanelList li a').click(function() {
                if (!this.className) {
                    return false;
                }
                current = $('#pDebug #' + this.className + '-content');
                if (current.is(':visible')) {
                    $(document).trigger('close.pDebug');
                    $(this).parent().removeClass('active');
                } else {
                    $('.panelContent').hide(); // Hide any that are already open
                    current.show();
                    $('#pDebugToolbar li').removeClass('active');
                    $(this).parent().addClass('active');
                }
                return false;
            });
            $('#pDebugPanelList li .switch').click(function() {
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
            $('#pDebug a.pDebugClose').click(function() {
                $(document).trigger('close.pDebug');
                $('#pDebugToolbar li').removeClass('active');
                return false;
            });
            $('#pDebug a.remoteCall').click(function() {
                $('#pDebugWindow').load(this.href, {}, function() {
                    $('#pDebugWindow a.pDebugBack').click(function() {
                        $(this).parent().parent().hide();
                        return false;
                    });
                });
                $('#pDebugWindow').show();
                return false;
            });
            $('#pDebugTemplatePanel a.pTemplateShowContext').click(function() {
                p_dt.toggle_arrow($(this).children('.toggleArrow'))
                p_dt.toggle_content($(this).parent().next());
                return false;
            });
            $('#pDebugSQLPanel a.pSQLShowStacktrace').click(function() {
                p_dt.toggle_content($('.pSQLHideStacktraceDiv', $(this).parents('tr')));
                return false;
            });
            $('#pHideToolBarButton').click(function() {
                p_dt.hide_toolbar(true);
                return false;
            });
            $('#pShowToolBarButton').click(function() {
                p_dt.show_toolbar();
                return false;
            });
            $("#pShowToolBarButton").hover(function() {
                $(this).data('pTimeout', setTimeout(function() {
                    p_dt.show_toolbar(false, true);
                    return false;
                }, 1000));
            }, function () {
                clearTimeout($(this).data('pTimeout'));
            });
            $(document).bind('close.pDebug', function() {
                // If a sub-panel is open, close that
                if ($('#pDebugWindow').is(':visible')) {
                    $('#pDebugWindow').hide();
                    return;
                }
                // If a panel is open, close that
                if ($('.panelContent').is(':visible')) {
                    $('.panelContent').hide();
                    return;
                }
                // Otherwise, just minimize the toolbar
                if ($('#pDebugToolbar').is(':visible')) {
                    p_dt.hide_toolbar(true);
                    return;
                }
            });
            if ($.cookie(COOKIE_NAME)) {
                p_dt.hide_toolbar(false);
            } else {
                p_dt.show_toolbar(false);
            }
        },
        toggle_content: function(elem) {
            if (elem.is(':visible')) {
                elem.hide();
            } else {
                elem.show();
            }
        },
        close: function() {
            $(document).trigger('close.pDebug');
            return false;
        },
        hide_toolbar: function(setCookie) {
            // close any sub panels
            $('#pDebugWindow').hide();
            // close all panels
            $('.panelContent').hide();
            $('#pDebugToolbar li').removeClass('active');
            // finally close toolbar
            $('#pDebugToolbar').hide('fast');
            $('#pDebugToolbarHandle').show();
            // Unbind keydown
            $(document).unbind('keydown.pDebug');
            if (setCookie) {
                $.cookie(COOKIE_NAME, 'hide', {
                    path: '/',
                    expires: 10
                });
            }
        },
        show_toolbar: function(animate, auto_hide) {
            auto_hide = auto_hide || false
            // Set up keybindings
            $(document).bind('keydown.pDebug', function(e) {
                if (e.keyCode == 27) {
                    p_dt.close();
                }
            });
            $('#pDebugToolbarHandle').hide();
            if (animate) {
                $('#pDebugToolbar').show('fast');
            } else {
                $('#pDebugToolbar').show();
            }
            if (auto_hide == false) {
                $.cookie(COOKIE_NAME, null, {
                    path: '/',
                    expires: -1
                });
            }
        },
        toggle_arrow: function(elem) {
            var uarr = String.fromCharCode(0x25b6);
            var darr = String.fromCharCode(0x25bc);
            elem.html(elem.html() == uarr ? darr : uarr);
        }
    };
    $(document).ready(function() {
        p_dt.init();
        $(".pDebugSortable").tablesorter();
    });
})(jQuery);
