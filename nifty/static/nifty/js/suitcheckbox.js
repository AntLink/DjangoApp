// $(document).on("nifty.ready", function () {
$(document).ready(function () {
    $(".checkbox-select > #select-all ").on("click", function () {
        "checked" == $(this).attr("checked") ? ($(this).removeAttr("checked"), $(".magic-checkbox").removeAttr("checked")) : ($(".magic-checkbox").attr({checked: "checked"}), $(this).attr({checked: "checked"}))
    })
});
