/**
 * @file Handles page preloading and binds event listeners for starting the chat.
 */

// Bind event listeners when the DOM has loaded
$(function(){
  var chatHasStarted = false;
  var $preloader = $('#page-preloader');
  var $preloaderDots = $preloader.find('span');

  // Animate the preloader
  CUI.animation.pagePreloaderTimeline = new TimelineMax();
  CUI.animation.pagePreloaderTimeline.staggerTo($preloaderDots, 0.6, {y: -10, yoyo: true, repeat: -1, repeatDelay: 0.3, ease: Back.easeInOut,  force3D: true, clearProps: 'transform'}, 0.1);

  // Create and initialize the chat when the start button is clicked
  $('.chat-start').on('click', function(e){
    e.preventDefault();

    // Disable multiple clicks
    if(chatHasStarted) return;
    else chatHasStarted = true;

    // Hide call to action
    $('.chat-introduction .cta').hide();

    // Create the chat
    var chat = new CUI.ChatPresenter(CUI.config.chatID, CUI.config.historyUrl, CUI.config.progressUrl);
  });
});

// Animate the UI when all assets have loaded
$(window).on('load', function(){
  var timeline = new TimelineMax();
  var $loading = $('#page-preloader');
  var $main = $('main');
  var $logo = $('.chat-introduction .logo');
  var $title = $('.chat-introduction header h1');
  var $course = $('.chat-introduction header p');
  var $about = $('.chat-introduction-body');

  // Hide spinner
  timeline.to($loading, 1, {opacity: 0, display: 'none', onComplete: function(){
    // Kill spinner animation timeline
    CUI.animation.pagePreloaderTimeline.kill();
    CUI.animation.pagePreloaderTimeline = null;

    // Reset scroll to fix page refresh bug in Firefox
    $(window).scrollTop(0);
  }});

  // Show main manually to avoid bug in Firefox when refreshing the page
  $main.css({'display': 'block', 'opacity': 0});

  // Animate main
  timeline.to($main, 1.2, {opacity: 1, ease: Power1.easeInOut, force3D: 'auto', clearProps: 'transform'}, 1);

  // Animate individual elements
  timeline.from($logo, 0.6, {y: +40, ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform'}, 1);
  timeline.from($title, 0.8, {y: +40, ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform'}, 1);
  timeline.from($course, 1, {y: +40, ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform'}, 1);
  timeline.from($about, 1.2, {y: +40, ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform'}, 1);
});
