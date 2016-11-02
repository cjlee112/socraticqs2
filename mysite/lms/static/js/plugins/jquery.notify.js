(function($){
  $.notify = function(message, opt){

    var options = $.extend({
      delay: 0,
      offset: {
        top: 20,
        right: 20
      },
      spacing: 20
    }, opt);

    var $notification;
    var $lastExistingNotification;
    var top = options.offset.top;

    // Create notification
    $notification = $('<div class="jquery-notify">' + message + '</div>');

    // Calculate offset
    $lastExistingNotification = $('.jquery-notify').last();
    if($lastExistingNotification.length > 0) top = $lastExistingNotification.offset().top + $lastExistingNotification.outerHeight() + options.spacing - $(window).scrollTop();

    // Add styling
    $notification.css({
      'position': 'fixed',
      'top': top,
      'right': options.offset.right,
      'z-index': 9999,
      'display': 'none'
    });

    // Show notification
    $notification.appendTo('body').fadeIn();

    // Remove automatically if delay is larger than 0
    if(options.delay > 0) {
      $notification.delay(options.delay).fadeOut(function(){
        $(this).remove();
      });
    }

    // Remove notification on click
    $notification.on('click', function(e){
      e.preventDefault();
      $(this).remove();
    });

    return $notification;
  };
})(jQuery);
