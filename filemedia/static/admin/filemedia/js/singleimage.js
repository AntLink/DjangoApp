function getCsrftoken(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
Dropzone.autoDiscover = false;
$(document).on('nifty.ready', function () {
    $('.dropzone').on('click', function () {

        var op = JSON.parse($(this).attr('data-filemedia-options'));
        var name = $(this).attr('data-name');
        var obid = $(this).attr('data-objectid');
        $("#img-" + name).dropzone({
            url: op.upload_url,
            addRemoveLinks: false,
            dictDefaultMessage: '',
            previewsContainer: '#dropzone-preview-' + name,
            acceptedFiles: "image/*",
            maxFilesize: 128,
            thumbnailWidth: 150,
            uploadMultiple: false,
            parallelUploads: 1,
            thumbnailHeight: 150,
            maxFiles: 1,
            previewTemplate: '<div class="dz-preview"><img data-dz-thumbnail class="img-responsive img-rounded dz-clickable" style="width: 125px"/><div class="dz-progress" style="width: 110px;margin-left: 8px; margin-top: -65px; position: absolute;"><div class="progress progress-striped active"><div data-dz-uploadprogress class="progress-bar progress-bar-success"></div></div></div></div>',
            success: function (file, response) {
                if (response.status) {
                    $(file.previewTemplate).find('.dz-progress').remove();
                    $(file.previewTemplate).find('img').attr('id', 'img-');
                    $(file.previewTemplate).find('img').attr('src', response.thmb.width150);
                    $(file.previewTemplate).find('img').attr('rel', response.imagedefault);
                    $(file.previewTemplate).find('img').attr('title', response.filename);
                    $(file.previewTemplate).find('img').attr('data-id', response.imgid);
                    $(file.previewTemplate).find('img').attr('data-uniquename', response.uniquename);
                    $(file.previewTemplate).find('img').attr('data-path', response.path_date);
                    $(file.previewTemplate).find('img').attr('data-imagedetail', response.thmb.width356);
                    $(file.previewTemplate).find('img').attr('data-image150', response.thmb.width150);
                    $(file.previewTemplate).find('img').attr('data-des', response.description);
                    $('#dropzone-get-' + name + ' img').attr('src', response.thmb.width150);
                    $('#dropzone-get-' + name + ' img').fadeIn();
                    $('#id_img_' + name).val(response.uniquename);
                } else {
                    $(file.previewTemplate).remove();
                    $.niftyNoty({
                        type: 'danger',
                        icon: 'pli-exclamation icon-2x',
                        message: gettext(response.data),
                        container: 'floating',
                        timer: 5000
                    });
                }
            },
            error: function (file, response) {
                $.niftyNoty({
                    type: 'danger',
                    icon: 'pli-exclamation icon-2x',
                    message: gettext(response),
                    container: 'floating',
                    timer: 5000
                });
            },
            sending: function (file, xhr, formData) {
                formData.append('csrfmiddlewaretoken', getCsrftoken('csrftoken'));
                formData.append('object_id', obid);
                $('#dropzone-get-' + name + ' img').hide();

            },
            init: function () {
                this.on("complete", function (file) {
                    this.removeAllFiles(true);
                })
            }
        });
    });

});