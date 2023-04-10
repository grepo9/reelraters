$(document).ready(function() {
    // Get the current URL
    var url = window.location.pathname;

    // Add active class to navbar item if its URL matches the current URL
    $('.nav-item').removeClass('active');
    $('.nav-item a[href="' + url + '"]').parent().addClass('active');

    // Remove and add active class on click
    $(".nav-item").click(function() {
        $(".nav-item").removeClass("active");
        $(this).addClass("active");
    });
});