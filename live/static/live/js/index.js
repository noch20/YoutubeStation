$(function() {
    var $win = $(window),
        $header = $('header'),
        $nav_toggle = $('.nav_toggle'),
        headerHeight = $header.outerHeight(),
        startPos = 0;
  
    $win.on('load scroll', function() {
      var value = $(this).scrollTop();
      if ( value > startPos && value > headerHeight ) {
        $header.css('top', '-' + headerHeight + 'px');
      } else {
        $header.css('top', '0');
      }
      startPos = value;
    });

    $nav_toggle.on('click', function () {
        $('.nav_toggle, .nav').toggleClass('show');
      });
      
  });