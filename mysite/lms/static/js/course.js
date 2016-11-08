// Bind event listeners when the DOM has loaded
$(function(){
  // Bind clicks on courselets and live sessions tabs
  $('.course-content-tabs a').on('click', function(e){
    e.preventDefault();

    // Get ID of new section
    var section = $(e.currentTarget).attr('href');

    // Remove selected state from tabs
    $('.course-content-tabs a').removeClass('course-content-tabs--selected');

    // Add selected state to new tab
    $(e.currentTarget).addClass('course-content-tabs--selected');

    // Hide visible sections
    $('.course-content-units').hide();

    // Show new section
    $(section).show();
  });
});
