Dropzone.autoDiscover = false;

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

function reloadFreeWall() {
    var wall = new freewall('.dropzone');
    var wd = ($('.panel-body').width() / 24 * 3);
    wall.reset({
        selector: '.dz-preview',
        animate: true,
        gutterX: 10,
        gutterY: 10,
        cellW: wd,
        cellH: wd,
        delay: 10,
        onResize: function () {
            var wa = ($('.panel-body').width() / 24 * 3);
            this.reset({
                selector: '.dz-preview',
                gutterX: 10,
                gutterY: 10,
                cellW: wa,
                cellH: wa,
                delay: 10,
            });
            wall.refresh();
        }
    });
    return wall.fitWidth();
}

$(document).on('nifty.ready', function () {
    reloadFreeWall();
    $("#add-image-grid").dropzone({
        url: imguploadURL,
        addRemoveLinks: false,
        previewsContainer: '#dropzone-grid-preview',
        acceptedFiles: "image/*",
        maxFilesize: 128,
        thumbnailWidth: 144,
        thumbnailHeight: 144,
        previewTemplate: '<span></span>',
        success: function (file, response) {
            $(file.previewTemplate).remove();
            var id = (file.size + file.lastModified);
            if (response.status) {
                $('.img-' + id).find('.magic-checkbox').attr('value', response.imgid);
                $('.img-' + id).find('img').attr('src', response.thmb.width100);
                $('.img-' + id).find('.change-link').attr('href', response.imgchange_link);
                $('.img-' + id).find('.delete-link').attr('href', response.imgdelete_link);
                $('.img-' + id).find('.view-link').attr('href', response.imgview_link);
                $('.img-' + id).find('.progress').hide();
                $('.img-' + id).find('.img-meta-link').css({'margin-top': '-25px'});
                $('.img-from').text(" 1 - " + response.imgcount);
                $('.img-to').text(response.imgcount);
                $('.add-tooltip').tooltip();
            } else {
                $('.img-' + id).remove();
                $.niftyNoty({
                    type: 'danger',
                    icon: 'pli-exclamation icon-2x',
                    message: gettext(response.content),
                    container: 'floating',
                    timer: 5000
                });
                reloadFreeWall();
            }
        },
        error: function (file, response) {
            $.niftyNoty({
                type: 'danger',
                icon: 'pli-exclamation icon-2x',
                message: gettext(response.content),
                container: 'floating',
                timer: 5000
            });
        },
        sending: function (file, xhr, formData) {
            formData.append('csrfmiddlewaretoken', getCsrftoken('csrftoken'));
            if (typeof taxID !== 'undefined') {
                formData.append("taxid", taxID);
            }
            if (canupload == 'True' && candelete == 'True') {
                $('#image-alert').remove();
                $('#panel-image').fadeIn();
            }

            var id = (file.size + file.lastModified);

            var img_src = '/static/admin/filemedia/img/no-thumb/td_100x100.png';
            var img_id = 'img-' + id;
            var progress_id = 'progress-' + id;

            var ch = canchange == 'True' ? '<a class="change-link add-tooltip btn-link" title="" href="#" data-original-title="' + gettext('Change') + '"><i class="demo-pli-pen-5"></i></a>&nbsp;' : '';
            var dw = candelete == 'True' ? '<a class="delete-link add-tooltip btn-link" title="" href="#" data-original-title="' + gettext('Delete') + '"><i class="demo-pli-trash"></i></a>' : '';
            var dl = candownload == 'True' ? '<a target="_blank" class="view-link add-tooltip btn-link" title="" href="javascript:;" data-original-title="' + gettext('Download') + '"><i class="demo-pli-download-from-cloud"></i></a>&nbsp;' : '';

            $('#dropzone').prepend('<div class="dz-preview ' + img_id + '"><div class="file-control"><input type="checkbox" name="_selected_action" class="magic-checkbox" id="list-' + id + '">' +
                '<label for="list-' + id + '"></label></div><img src="' + img_src + '" alt="Image"/><div class="img-meta-link" style="text-align: center; width:inherit; position:absolute;">' +
                '<div class="progress progress-striped active" style="margin-top:-68px;margin-right: 10px;margin-left: 10px;margin-bottom: 30px;">' +
                '<div id="' + progress_id + '" class="progress-bar progress-bar-success"></div></div><span style="font-size:14px;">' +
                ch + dl + dw +
                '</span></div></div>');
            reloadFreeWall();
        },
        thumbnail: function (file, dataUrl) {
            var id = (file.size + file.lastModified);
            $('.img-' + id).find('img').attr('src', dataUrl);
            $('.img-' + id).fadeIn();
            reloadFreeWall();
        },
        uploadprogress: function (file, progress, bytesSent) {
            var id = (file.size + file.lastModified);
            $("#progress-" + id).css({"width": progress + "%"});
        }
    });

    $("#add-image-list").dropzone({
        url: imguploadURL,
        addRemoveLinks: false,
        previewsContainer: '#dropzone-list-preview',
        acceptedFiles: "image/*",
        maxFilesize: 128,
        thumbnailWidth: 50,
        thumbnailHeight: 50,
        previewTemplate: '<span></span>',
        success: function (file, response) {
            $(file.previewTemplate).remove();
            var id = (file.size + file.lastModified);
            if (response.status) {
                $('#img-' + id).find('.magic-checkbox').attr('value', response.imgid);
                $('#img-' + id).find('img').attr('src', response.thmb.width100);
                $('#img-' + id).find('.change-link').attr('href', response.imgchange_link);
                $('#img-' + id).find('.delete-link').attr('href', response.imgdelete_link);
                $('#img-' + id).find('.view-link').attr('href', response.imgview_link);
                $('#img-' + id).find('.progress').hide();
                $('#img-' + id).find('.file-name').text(response.name);
                $('#img-' + id).find('.file-date').text(response.created_at + ' | ' + response.filesize);
                $('.img-from').text(" 1 - " + response.imgcount);
                $('.img-to').text(response.imgcount);

            } else {
                $('#img-' + id).remove();
                $.niftyNoty({
                    type: 'danger',
                    icon: 'pli-exclamation icon-2x',
                    message: gettext(response.content),
                    container: 'floating',
                    timer: 5000
                });
            }
        },
        error: function (file, response) {
            $.niftyNoty({
                type: 'danger',
                icon: 'pli-exclamation icon-2x',
                message: gettext(response.content),
                container: 'floating',
                timer: 5000
            });
        },
        sending: function (file, xhr, formData) {
            formData.append('csrfmiddlewaretoken', getCsrftoken('csrftoken'));
            if (typeof taxID !== 'undefined') {
                formData.append("taxid", taxID);
            }

            if (canupload == 'True' && candelete == 'True') {
                $('#image-alert').remove();
                $('#panel-image').fadeIn();
            }

            var id = (file.size + file.lastModified);
            var img_src = '/static/admin/filemedia/img/no-thumb/td_100x100.png';
            var img_id = 'img-' + id;
            var progress_id = 'progress-' + id;

            var ch = canchange == 'True' ? '<li><a class="btn-link change-link" style="width:100%" href="#"><i class="demo-pli-pen-5"></i> ' + gettext('Change') + '</a></li>' : '';
            var dw = candelete == 'True' ? '<li><a class="btn-link delete-link" style="width:100%" href="#"><i class="demo-pli-trash"></i> ' + gettext('Delete') + '</a></li>' : '';
            var dl = candownload == 'True' ? '<li><a target="_blank" class="btn-link view-link" style="width:100%" href="javascript:;"><i class="demo-pli-download-from-cloud"></i> ' + gettext('Download') + '</a></li>' : '';

            var cb = candelete == 'True' ? '<div class="file-control" style="width: 30px;"><input type="checkbox" name="_selected_action" value="104" class="magic-checkbox" id="list-' + id + '"><label for="list-' + id + '"></label></div>' : '';

            var btn = '';
            if (canchange == 'True' || candelete == 'True' || candownload == 'True'){
                btn = '<button class="btn btn-icon" data-toggle="dropdown" type="button" aria-expanded="false"><i class="pci-ver-dots"></i></button>';
            }
            $('#list-items').prepend('<li id="' + img_id + '">' + cb +
                '<div class="file-settings dropdown">' + btn +
                '<ul class="dropdown-menu dropdown-menu-right with-arrow" style="right:-6px"> ' + ch + dw + dl + '</ul> </div>' +
                '<div class="file-details"> <div class="media-block"> <div class="media-left"><img class="file-img img-responsive" style="width:40px" src="' + img_src + '" alt="upload"></div>' +
                '<div class="media-body"> <div class="progress progress-striped active" style="margin-top:15px;"><div id="' + progress_id + '" class="progress-bar progress-bar-success"></div>' +
                '</div><p class="file-name"></p><small class="file-date"></small> </div></div></div></li>');
            $('#img' + id).hide();
        },
        thumbnail: function (file, dataUrl) {
            var id = (file.size + file.lastModified);
            $('#img-' + id).find('img').attr('src', dataUrl);
            $('#img-' + id).fadeIn();
        },
        uploadprogress: function (file, progress, bytesSent) {
            var id = (file.size + file.lastModified);
            $("#progress-" + id).css({"width": progress + "%"});
        }
    });

});