$(function() {
    var shiftWindow = function() { scrollBy(0, -70) };
    if (location.hash){
        setTimeout(shiftWindow, 100);
    }
    window.addEventListener("hashchange", shiftWindow);
});
