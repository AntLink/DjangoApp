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
    $("#add-files").dropzone({
        url: fileUploadURL,
        addRemoveLinks: false,
        previewsContainer: '#dropzone-list-file-preview',
        maxFilesize: 1024,
        previewTemplate: '<span></span>',
        success: function (file, response) {
            $(file.previewTemplate).remove();
            var id = (file.lastModified + file.size);
            if (response.status) {
                $('#file-' + id).find('.magic-checkbox').attr('value', response.id);
                $('#file-' + id).find('.change-link').attr('href', response.change_link);
                $('#file-' + id).find('.delete-link').attr('href', response.delete_link);
                $('#file-' + id).find('.download-link').attr('href', response.download_link);
                $('#file-' + id).find('.progress').hide();
                $('#file-' + id).find('.file-name').text(response.name);
                $('#file-' + id).find('.file-date').text(response.created_at + ' | ' + response.filesize);
                $(file.previewTemplate).find('.progress').hide();
                $('.file-from').text(" 1 - " + response.count);
                $('.file-to').text(response.count);
            } else {
                $('#file-' + id).remove();
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
            var id = (file.lastModified + file.size);

            if (canupload == 'True' && candelete == 'True') {
                $('#file-alert').remove();
                $('#panel-file').fadeIn();
            }

            var btn = '';
            if (canchange == 'True' || candelete == 'True' || candownload == 'True') {
                btn = '<button class="btn btn-icon" data-toggle="dropdown" type="button" aria-expanded="false"><i class="pci-ver-dots"></i></button>';
            }

            var ch = canchange == 'True' ? '<li><a class="btn-link change-link" style="width:100%" href="#"><i class="demo-pli-pen-5"></i> ' + gettext('Change') + '</a></li>' : '';
            var dw = candelete == 'True' ? '<li><a class="btn-link delete-link" style="width:100%" href="#"><i class="demo-pli-trash"></i> ' + gettext('Delete') + '</a></li>' : '';
            var dl = candownload == 'True' ? '<li><a target="_blank" class="btn-link download-link" style="width:100%" href="javascript:;"><i class="demo-pli-download-from-cloud"></i> ' + gettext('Download') + '</a></li>' : '';

            var cb = candelete == 'True' ? '<div class="file-control" style="width: 33px;"><input type="checkbox" name="_selected_action" class="magic-checkbox" id="list-' + id + '"><label for="list-' + id + '"></label></div>' : '';

            $('#files-list').prepend('<li id="file-' + id + '"> '+cb+'<div class="file-settings dropdown"> ' + btn + '<ul class="dropdown-menu dropdown-menu-right with-arrow" style="right:-6px"> ' + ch + dw + dl + '</ul> </div><div class="file-details"> <div class="media-block"> <div class="media-left"><i class="demo-pli-file"></i></div><div class="media-body"> <div class="progress progress-striped active" style="margin-top:15px;"><div id="progress-' + id + '" class="progress-bar progress-bar-success"></div></div><p class="file-name"></p><small class="file-date"></small> </div></div></div></li>');
            if (typeof taxID !== 'undefined') {
                formData.append("taxid", taxID);
            }


        },
        uploadprogress: function (file, progress, bytesSent) {
            var id = (file.lastModified + file.size);
            $("#progress-" + id).css({"width": progress + "%"});
        }
    });

});