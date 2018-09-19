(function($){
  $.fn.expandingTextarea = function(options){

    var settings = $.extend({
      maxRows: 10
    }, options);

    return this.each(function(){
      $(this).on('input', function(e){
        // Get lineheight
        this.lineHeight = parseInt($(this).css('line-height'));

        // Reset to one row, height is needed for IE
        this.rows = 1;
        $(this).height( this.lineHeight );

        // Calculate new number of rows
        var newRows = Math.ceil(this.scrollHeight / this.lineHeight);

        if(newRows < 1) {
          newRows = settings.minRows;
        } else if(newRows > settings.maxRows) {
          newRows = settings.maxRows;
        }

        // Update the number of rows, height is needed for IE
        this.rows = newRows;
        $(this).height( this.lineHeight * newRows);

        // Update overflow
        if(newRows > settings.maxRows) {
          $(this).css('overflow', 'scroll');
        }else{
          $(this).css('overflow', 'hidden');
        }
      });
    });
  };
})(jQuery);
