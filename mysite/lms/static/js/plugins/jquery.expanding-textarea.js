(function($){
  $.fn.expandingTextarea = function(options){

    var settings = $.extend({
      minRows: 1,
      maxRows: 10
    }, options);

    return this.each(function(){
      $(this).one('focus', function(){
        var savedValue = this.value;
        this.value = '';
        this.baseScrollHeight = this.scrollHeight;
        this.value = savedValue;
      }).on('keydown', function(e){
        // Disable new linebreaks when pressing enter as it is used for submit
        if(e.which == 13 && (!e.shiftKey && !e.ctrlKey && !e.altKey))
          return false;
      }).on('input', function(e){
          this.rows = settings.minRows;
          var rows = Math.ceil((this.scrollHeight - this.baseScrollHeight) / parseInt($(this).css('line-height')));
          rows += settings.minRows;
          if(rows > 10) {
            rows = 10;
            $(this).css('overflow', 'scroll');
          }else{
            $(this).css('overflow', 'hidden');
          }
          this.rows = rows;
      });
    });
  };
})(jQuery);
