$(document).on('nifty.ready', function () {
    $('.date-form').datepicker({
        autoclose: true,
        format: "yyyy-mm-dd",
        todayBtn: "linked",
        todayHighlight: true
    });
});