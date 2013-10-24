$(function() {
    var shiftWindow = function() { scrollBy(0, -70) };
    if (location.hash){
        setTimeout(shiftWindow, 100);
    }
    window.addEventListener("hashchange", shiftWindow);
    $('[data-confirm-url]').click(function () {
        var loc = $(this).data('confirm-url')
        bootbox.confirm("Are you sure you want to permanently delete this account?", function () {
            window.location = loc
        });
    });
});
