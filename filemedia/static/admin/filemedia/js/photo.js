Dropzone.autoDiscover = false;
if (!FileManager) var FileManager = {};

FileManager = {
    init: function (iv) {
        this.filemediaUploadImage(iv);
        this.filemediaGetimage(iv);
        this.fileMediaScrollImage(iv);
        this.filemediaNextPage(iv);
        this.filemediaPrevPage(iv);
    },
    getCsrftoken: function (name) {
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
    },

    reloadFreeWall: function () {
        var wall = new freewall('.dropzone');
        wall.reset({
            selector: '.dz-preview',
            animate: true,
            gutterX: 6,
            gutterY: 6,
            cellW: 125,
            cellH: 125,
            onResize: function () {
                wall.fitWidth();
            },
            onComplete: function () {
            }
        });
        return wall.fitWidth();
    },
    filemediaUploadImage: function (iv) {
        var self = this;
        var op = JSON.parse($(iv).attr('data-filemedia-options'));
        var name = $(iv).attr('data-name');
        $("#add-image-" + name).dropzone({
            url: op.upload_url,
            addRemoveLinks: false,
            previewsContainer: '#dropzone-preview-' + name,
            acceptedFiles: "image/*",
            maxFilesize: 128,
            thumbnailWidth: 115,
            thumbnailHeight: 115,
            previewTemplate: '<div class="dz-preview"><img data-dz-thumbnail /><div style="text-align: center; width:inherit; position:absolute;margin-top:-25px"><span style="font-size:14px;"><a id="" class="add-tooltip btn-link img-delete" data-id="" href="javascript:;" data-original-title="' + gettext("Delete") + '"><i class="demo-pli-trash"></i></a></span></div><div class="dz-progress"><div class="progress progress-striped active" ><div data-dz-uploadprogress class="progress-bar progress-bar-success"></div></div></div></div>',
            success: function (file, response) {
                if (response.status) {
                    $(file.previewTemplate).find('.dz-progress').remove();
                    $(file.previewTemplate).find('img').attr('style', 'cursor: pointer');
                    $(file.previewTemplate).find('img').attr('src', response.thmb.width100);
                    $(file.previewTemplate).find('img').attr('rel', response.imagedefault);
                    $(file.previewTemplate).find('img').attr('title', response.filename);
                    $(file.previewTemplate).find('img').attr('data-id', response.imgid);
                    $(file.previewTemplate).find('img').attr('data-uniquename', response.uniquename);
                    $(file.previewTemplate).find('img').attr('data-path', response.path_date);
                    $(file.previewTemplate).find('img').attr('data-imagedetail', response.thmb.width255);
                    $(file.previewTemplate).find('img').attr('data-image256', response.thmb.width256);
                    $(file.previewTemplate).find('img').attr('data-des', response.description);
                    $(file.previewTemplate).find('a').attr('data-id', response.imgid);
                    $(file.previewTemplate).find('a').attr('id', "img" + response.imgid);
                    var imgid = ('img' + response.imgid);
                    self.deleteUploadImage(iv, imgid);
                    $('.img-delete').tooltip();
                } else {
                    $(file.previewTemplate).remove();
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
                    message: gettext(response),
                    container: 'floating',
                    timer: 5000
                });
            },
            sending: function (file, xhr, formData) {
                formData.append('csrfmiddlewaretoken', self.getCsrftoken('csrftoken'));
                var dzv = $('#dropzone-load-' + name).find('.dz-preview');
                if (dzv.length = 18) {
                    var l = (dzv.length - 1);
                    $(dzv[l]).remove();
                }
                self.reloadFreeWall();
                var img = $(file.previewTemplate).find('img');
                $(img).on('click', function () {
                    var imgd = '<img class="img-responsive thumbnail" data-imagedetail="' + $(img).attr('data-image256') + '" src="' + $(img).attr('data-imagedetail') + '" data-id="' + $(img).attr('data-id') + '" data-uniquename="' + $(img).attr('data-uniquename') + '"' + ' title="' + $(img).attr('title') + '">';
                    var formd = '' +
                        '<div id="form-img-detail-' + name + '">' +
                        '<input id="img-csrf" type="hidden" name="csrfmiddlewaretoken" value="' + self.getCsrftoken('csrftoken') + '">' +
                        '<input id="img-id" type="hidden" name="id" value="' + $(img).attr('data-id') + '">' +
                        '<input id="img-name" type="text" name="name" value="' + $(img).attr('title') + '" placeholder="' + gettext("Name") + '" class="form-control">' +
                        '<textarea id="img-des" name="description" style="height: 95px;" placeholder="' + gettext("Description") + '" rows="13" class="form-control mar-top">' + $(img).attr('data-des') + '</textarea>' +
                        '<button data-dismiss="modal" type="button" class="btn btn-primary mar-top" id="btn-img-' + name + '">' + gettext("Insert") + '</button>' +
                        '</div>';
                    $('#img-detail-' + name).html(imgd + formd);
                    $('#btn-img-' + name).on('click', function () {
                        var imgd = $('#img-detail-' + name).find('img');
                        $('#img-' + name).attr('src', imgd.attr('data-imagedetail'));
                        $('#id_img_' + name).val(imgd.attr('data-imagedetail'));

                        $.ajax({
                            dataType: "json",
                            cache: false,
                            url: op.update_url,
                            method: 'POST',
                            data: {
                                'csrfmiddlewaretoken': $('#form-img-detail-' + name).find('#img-csrf').val(),
                                'id': $('#form-img-detail-' + name).find('#img-id').val(),
                                'name': $('#form-img-detail-' + name).find('#img-name').val(),
                                'description': $('#form-img-detail-' + name).find('#img-des').val(),
                            },
                            success: $.proxy(function (data) {
                                $('#modal-img-' + name).modal('hide');
                                $('#dropzone-preview-' + name).empty();
                                $('#dropzone-load-' + name).empty();
                                $('#img-detail-' + name).empty();
                            }, this)
                        });

                    });
                });
            },

        });

    },
    filemediaGetimage: function (iv) {
        var self = this;
        var op = JSON.parse($(iv).attr('data-filemedia-options'));
        var name = $(iv).attr('data-name');

        $.ajax({
            dataType: "json",
            cache: false,
            url: op.load_url,
            data: {'page': 1},
            success: $.proxy(function (data) {

                if (data.status) {
                    $.each(data.store, $.proxy(function (key, val) {
                        var thumbtitle = '';
                        if (typeof val.title !== 'undefined') thumbtitle = val.title;
                        var img = $('<div class="dz-preview" ><img data-path= "' + val.path_date + '" data-id="' + val.imgid + '" data-uniquename="' + val.uniquename + '" data-imagedetail="' + val.thmb.width255 + '" src="' + val.thmb.width100 + '" rel="' + val.image + '" title="' + thumbtitle + '"  data-description="' + val.description + '" style="cursor: pointer;" ><div style="text-align: center; width:inherit; position:absolute;margin-top:-25px"><span style="font-size:14px;"><a class="add-tooltip btn-link img-delete" data-id="' + val.imgid + '" href="javascript:;" data-original-title="' + gettext("Delete") + '"><i class="demo-pli-trash"></i></a></span></div></div>');
                        $(img).on('click', function () {
                            var imgd = '<img data-path= "' + val.path_date + '" class="img-responsive thumbnail" data-imagedetail="' + val.thmb.width256 + '" src="' + val.thmb.width255 + '" data-uniquename="' + val.uniquename + '"' + ' title="' + thumbtitle + '"  data-description="' + val.description + '">';
                            var formd = '' +
                                '<div id="form-img-detail-' + name + '">' +
                                '<input id="img-csrf" type="hidden" name="csrfmiddlewaretoken" value="' + self.getCsrftoken('csrftoken') + '">' +
                                '<input id="img-id" type="hidden" name="id" value="' + val.imgid + '">' +
                                '<input id="img-name" type="text" name="name" value="' + thumbtitle + '" placeholder="' + gettext("Name") + '" class="form-control">' +
                                '<textarea id="img-des" name="description" style="height: 95px;" placeholder="' + gettext("Description") + '" rows="13" class="form-control mar-top">' + val.description + '</textarea>' +
                                '<button data-dismiss="modal" type="button" class="btn btn-primary mar-top" id="btn-img-' + name + '">' + gettext("Insert") + '</button>' +
                                '</div>';
                            $('#img-detail-' + name).html(imgd + formd);
                            $('#btn-img-' + name).on('click', function () {
                                var imgd = $('#img-detail-' + name).find('img');
                                $('#img-' + name).attr('src', imgd.attr('data-imagedetail'));
                                $('#id_img_' + name).val(imgd.attr('data-imagedetail'));

                                $.ajax({
                                    dataType: "json",
                                    cache: false,
                                    url: op.update_url,
                                    method: 'POST',
                                    data: {
                                        'csrfmiddlewaretoken': $('#form-img-detail-' + name).find('#img-csrf').val(),
                                        'id': $('#form-img-detail-' + name).find('#img-id').val(),
                                        'name': $('#form-img-detail-' + name).find('#img-name').val(),
                                        'description': $('#form-img-detail-' + name).find('#img-des').val(),
                                    },
                                    success: $.proxy(function (data) {
                                        if (data.status) {
                                            $('#modal-img-' + name).modal('hide');
                                            $('#dropzone-preview-' + name).empty();
                                            $('#dropzone-load-' + name).empty();
                                            $('#dropzone-' + name).attr('data-page', '1');
                                            $('#img-detail-' + name).empty();
                                        } else {
                                            $('#modal-img-' + name).modal('hide');
                                            $('#dropzone-preview-' + name).empty();
                                            $('#dropzone-load-' + name).empty();
                                            $('#dropzone-' + name).attr('data-page', '1');
                                            $('#img-detail-' + name).empty();
                                            $.niftyNoty({
                                                type: 'danger',
                                                icon: 'pli-exclamation icon-2x',
                                                message: gettext(data.content),
                                                container: 'floating',
                                                timer: 5000
                                            });
                                        }
                                    }, this)
                                });

                            });
                        });


                        $('#dropzone-load-' + name).append(img);
                        $('.img-delete').tooltip();
                    }, this));
                    self.reloadFreeWall();
                    self.deleteImage(iv);
                } else {
                    $.niftyNoty({
                        type: 'danger',
                        icon: 'pli-exclamation icon-2x',
                        message: gettext(data.content),
                        container: 'floating',
                        timer: 5000
                    });
                }

            }, this)
        });
    },
    filemediaNextPage: function (iv) {
        var self = this;
        var op = JSON.parse($(iv).attr('data-filemedia-options'));
        var name = $(iv).attr('data-name');
        $('#img-next-' + name).on('click', function () {
            var page = $(this).attr('data-page');
            $.ajax({
                dataType: "json",
                cache: false,
                url: op.load_url,
                data: {'page': page},
                success: $.proxy(function (data) {
                    if (data.status) {
                        if (data.leng !== 0) {
                            $('#dropzone-preview-' + name).empty();
                            $('#dropzone-load-' + name).empty();
                            $('#img-prev-' + name).attr('data-page', data.pageprev);
                            $('#img-next-' + name).attr('data-page', data.pagenext);
                            $.each(data.store, $.proxy(function (key, val) {
                                var thumbtitle = '';
                                if (typeof val.title !== 'undefined') thumbtitle = val.title;
                                var img = $('<div class="dz-preview" ><img data-path= "' + val.path_date + '" data-id="' + val.imgid + '" data-uniquename="' + val.uniquename + '" data-imagedetail="' + val.thmb.width255 + '" src="' + val.thmb.width100 + '" rel="' + val.image + '" title="' + thumbtitle + '"  data-description="' + val.description + '" style="cursor: pointer;" ><div style="text-align: center; width:inherit; position:absolute;margin-top:-25px"><span style="font-size:14px;"><a class="add-tooltip btn-link img-delete" data-id="' + val.imgid + '" href="javascript:;" data-original-title="' + gettext("Delete") + '"><i class="demo-pli-trash"></i></a></span></div></div>');
                                $(img).on('click', function () {
                                    var imgd = '<img data-path= "' + val.path_date + '" class="img-responsive thumbnail" data-imagedetail="' + val.thmb.width256 + '"  src="' + val.thmb.width255 + '" data-id="' + val.imgid + '" data-uniquename="' + val.uniquename + '"' + ' title="' + thumbtitle + '"  data-description="' + val.description + '">';
                                    var formd = '' +
                                        '<div id="form-img-detail-' + name + '">' +
                                        '<input id="img-csrf" type="hidden" name="csrfmiddlewaretoken" value="' + self.getCsrftoken('csrftoken') + '">' +
                                        '<input id="img-id" type="hidden" name="id" value="' + val.imgid + '">' +
                                        '<input id="img-name" type="text" name="name" value="' + thumbtitle + '" placeholder="' + gettext("Name") + '" class="form-control">' +
                                        '<textarea id="img-des" name="description" style="height: 95px;" placeholder="' + gettext("Description") + '" rows="13" class="form-control mar-top">' + val.description + '</textarea>' +
                                        '<button data-dismiss="modal" type="button" class="btn btn-primary mar-top" id="btn-img-' + name + '">' + gettext("Insert") + '</button>' +
                                        '</div>';
                                    $('#img-detail-' + name).html(imgd + formd);
                                    $('#btn-img-' + name).on('click', function () {
                                        var imgd = $('#img-detail-' + name).find('img');
                                        $('#img-' + name).attr('src', imgd.attr('data-imagedetail'));
                                        $('#id_img_' + name).val(imgd.attr('data-imagedetail'));

                                        $.ajax({
                                            dataType: "json",
                                            cache: false,
                                            url: op.update_url,
                                            method: 'POST',
                                            data: {
                                                'csrfmiddlewaretoken': $('#form-img-detail-' + name).find('#img-csrf').val(),
                                                'id': $('#form-img-detail-' + name).find('#img-id').val(),
                                                'name': $('#form-img-detail-' + name).find('#img-name').val(),
                                                'description': $('#form-img-detail-' + name).find('#img-des').val(),
                                            },
                                            success: $.proxy(function (data) {
                                                $('#modal-img-' + name).modal('hide');
                                                $('#dropzone-preview-' + name).empty();
                                                $('#dropzone-load-' + name).empty();
                                                $('#img-detail-' + name).empty();
                                            }, this)
                                        });

                                    });
                                });
                                $('#dropzone-load-' + name).append(img)
                            }, this));
                            self.reloadFreeWall();
                            self.deleteImage(iv);
                            $('.img-delete').tooltip();
                        }
                    } else {
                        $.niftyNoty({
                            type: 'danger',
                            icon: 'pli-exclamation icon-2x',
                            message: gettext(data.content),
                            container: 'floating',
                            timer: 5000
                        });
                    }
                }, this)
            });
        });
    },
    filemediaPrevPage: function (iv) {
        var self = this;
        var op = JSON.parse($(iv).attr('data-filemedia-options'));
        var name = $(iv).attr('data-name');
        $('#img-prev-' + name).on('click', function () {
            var page = $(this).attr('data-page');
            $.ajax({
                dataType: "json",
                cache: false,
                url: op.load_url,
                data: {'page': page},
                success: $.proxy(function (data) {
                    if (data.status) {
                        if (data.leng !== 0) {
                            $('#dropzone-preview-' + name).empty();
                            $('#dropzone-load-' + name).empty();
                            $('#img-prev-' + name).attr('data-page', data.pageprev);
                            $('#img-next-' + name).attr('data-page', data.pagenext);
                            $.each(data.store, $.proxy(function (key, val) {
                                var thumbtitle = '';
                                if (typeof val.title !== 'undefined') thumbtitle = val.title;
                                var img = $('<div class="dz-preview" ><img data-path= "' + val.path_date + '" data-id="' + val.imgid + '" data-uniquename="' + val.uniquename + '" data-imagedetail="' + val.thmb.width255 + '" src="' + val.thmb.width100 + '" rel="' + val.image + '" title="' + thumbtitle + '"  data-description="' + val.description + '" style="cursor: pointer;" ><div style="text-align: center; width:inherit; position:absolute;margin-top:-25px"><span style="font-size:14px;"><a class="add-tooltip btn-link img-delete" data-id="' + val.imgid + '" href="javascript:;" data-original-title="' + gettext("Delete") + '"><i class="demo-pli-trash"></i></a></span></div></div>');
                                $(img).on('click', function () {
                                    var imgd = '<img data-path= "' + val.path_date + '" class="img-responsive thumbnail" data-imagedetail="' + val.thmb.width256 + '"  src="' + val.thmb.width255 + '" data-id="' + val.imgid + '" data-uniquename="' + val.uniquename + '"' + ' title="' + thumbtitle + '"  data-description="' + val.description + '">';
                                    var formd = '' +
                                        '<div id="form-img-detail-' + name + '">' +
                                        '<input id="img-csrf" type="hidden" name="csrfmiddlewaretoken" value="' + self.getCsrftoken('csrftoken') + '">' +
                                        '<input id="img-id" type="hidden" name="id" value="' + val.imgid + '">' +
                                        '<input id="img-name" type="text" name="name" value="' + thumbtitle + '" placeholder="' + gettext("Name") + '" class="form-control">' +
                                        '<textarea id="img-des" name="description" style="height: 95px;" placeholder="' + gettext("Description") + '" rows="13" class="form-control mar-top">' + val.description + '</textarea>' +
                                        '<button data-dismiss="modal" type="button" class="btn btn-primary mar-top" id="btn-img-' + name + '">' + gettext("Insert") + '</button>' +
                                        '</div>';
                                    $('#img-detail-' + name).html(imgd + formd);
                                    $('#btn-img-' + name).on('click', function () {
                                        var imgd = $('#img-detail-' + name).find('img');
                                        $('#img-' + name).attr('src', imgd.attr('data-imagedetail'));
                                        $('#id_img_' + name).val(imgd.attr('data-imagedetail'));

                                        $.ajax({
                                            dataType: "json",
                                            cache: false,
                                            url: op.update_url,
                                            method: 'POST',
                                            data: {
                                                'csrfmiddlewaretoken': $('#form-img-detail-' + name).find('#img-csrf').val(),
                                                'id': $('#form-img-detail-' + name).find('#img-id').val(),
                                                'name': $('#form-img-detail-' + name).find('#img-name').val(),
                                                'description': $('#form-img-detail-' + name).find('#img-des').val(),
                                            },
                                            success: $.proxy(function (data) {
                                                $('#modal-img-' + name).modal('hide');
                                                $('#dropzone-preview-' + name).empty();
                                                $('#dropzone-load-' + name).empty();
                                                $('#img-detail-' + name).empty();
                                            }, this)
                                        });

                                    });
                                });
                                $('#dropzone-load-' + name).append(img)
                            }, this));
                            self.reloadFreeWall();
                            self.deleteImage(iv);
                            $('.img-delete').tooltip();
                        }
                    } else {
                        $.niftyNoty({
                            type: 'danger',
                            icon: 'pli-exclamation icon-2x',
                            message: gettext(data.content),
                            container: 'floating',
                            timer: 5000
                        });
                    }
                }, this)
            });
        });
    },
    deleteUploadImage: function (iv, id) {
        var op = JSON.parse($(iv).attr('data-filemedia-options'));
        var self = this;
        $('#' + id).on('click', function () {
            var imgcl = this;
            var imgid = $(this).attr('data-id');
            $.ajax({
                dataType: "json",
                cache: false,
                url: op.delete_url,
                method: 'POST',
                data: {
                    'csrfmiddlewaretoken': self.getCsrftoken('csrftoken'),
                    'id': imgid,
                },
                success: $.proxy(function (data) {
                    if (data.status) {
                        $.niftyNoty({
                            type: 'success',
                            icon: 'pli-exclamation icon-2x',
                            message: gettext(data.content),
                            container: 'floating',
                            timer: 5000
                        });
                        $(imgcl).parent().parent().parent().remove();
                        self.reloadFreeWall();
                        $('#img-detail-photo').empty();
                    } else {
                        $.niftyNoty({
                            type: 'danger',
                            icon: 'pli-exclamation icon-2x',
                            message: gettext(data.content),
                            container: 'floating',
                            timer: 5000
                        });
                    }
                }, this)
            });
        });
    },
    deleteImage: function (iv) {
        var op = JSON.parse($(iv).attr('data-filemedia-options'));
        var self = this;
        $('.img-delete').on('click', function () {
            var imgcl = this;
            var imgid = $(this).attr('data-id');
            $.ajax({
                dataType: "json",
                cache: false,
                url: op.delete_url,
                method: 'POST',
                data: {
                    'csrfmiddlewaretoken': self.getCsrftoken('csrftoken'),
                    'id': imgid,
                },
                success: $.proxy(function (data) {
                    if (data.status) {
                        $.niftyNoty({
                            type: 'success',
                            icon: 'pli-exclamation icon-2x',
                            message: gettext(data.content),
                            container: 'floating',
                            timer: 5000
                        });
                        $(imgcl).parent().parent().parent().remove();
                        self.reloadFreeWall();
                        $('#img-detail-photo').empty();
                    } else {
                        $.niftyNoty({
                            type: 'danger',
                            icon: 'pli-exclamation icon-2x',
                            message: gettext(data.content),
                            container: 'floating',
                            timer: 5000
                        });
                    }
                }, this)
            });
        });

    },
    fileMediaScrollImage: function (iv) {
        var self = this;
        var op = JSON.parse($(iv).attr('data-filemedia-options'));
        var name = $(iv).attr('data-name');
        $('#slim-scroll-' + name).slimScroll({
            height: '380px',
            color: '#1e3a57',
            opacity: .8,
            borderRadius: 0,
            railVisible: true,
            size: '4px',
        });
    }
};

$(document).on('nifty.ready', function () {
    $('.img-filemedia').unbind('click').click(function (e) {
        var name = $(this).attr('data-name');
        FileManager.init(this);
        $('#img-modal-close-' + name).on('click', function () {
            $('#modal-img-' + name).modal('hide');
            $('#dropzone-preview-' + name).empty();
            $('#dropzone-load-' + name).empty();
            $('#dropzone-' + name).attr('data-page', '1');
        });
    });
});