$(document).on('nifty.ready', function () {
    setInterval(function () {
        $("#page-head > .alert").fadeOut("slow");
    }, 1000);

    $(".setting-admin").on("click", function () {
        var con = $('#container').attr('class').split(' ');
        for (i = 0; i < con.length; i++) {
            if (con[i] == 'push' || con[i] == 'slide' || con[i] == 'reveal') {
                if ($(this).attr('data-value') == 'admin_colpase_menu') {
                    $(this).attr('data-content', 'mainnav-out');
                }
            } else {
                if ($(this).attr('data-value') == 'admin_colpase_menu') {
                    $(this).attr('data-content', 'mainnav-lg');
                }
            }
        }

        var click = this;
        $.ajax({
            url: settings_update,
            type: 'POST',
            dataType: 'json',
            data: {
                'csrfmiddlewaretoken': csrf_token,
                'val': $(click).attr('data-value'),
                'content': $(click).attr('data-content'),
            },
            success: function (data) {
                $(click).attr('data-value', data.val);
                $(click).attr('data-content', data.content)
            }
        }).done(function (msg) {
        });
    });
});