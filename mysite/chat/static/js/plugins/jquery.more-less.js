(function($){
  $.fn.moreLess = function(opt){

    var options = $.extend({
      characters: 60,
      ellipsis: ' ...',
      moreText: 'more',
      lessText: 'less'
    }, opt);

    return this.each(function(){
      var el = $(this);
      var content = el.html().trim();
      var settings = {};

      settings.characters = el.data('more-less-characters') || options.characters;
      settings.ellipsis = el.data('more-less-ellipsis') || options.ellipsis;
      settings.moreText = el.data('more-less-more-text') || options.moreText;
      settings.lessText = el.data('more-less-less-text') || options.lessText;

      if(content.length > settings.characters) {
          var c = content.substr(0, settings.characters);
          var h = content.substr(settings.characters, content.length - settings.characters);

          var html = c + '<span class="more-less-ellipsis">' + settings.ellipsis + '</span><span class="more-less-more-content" style="display: none;">' + h + '</span>&nbsp;<a href="" class="more-less-toggle" data-more-text="' + settings.moreText + '" data-less-text="'+ settings.lessText + '">' + settings.moreText + '</a></span>';

          el.html(html);

          el.find(".more-less-toggle").on('click', function(e){
            e.preventDefault();

            if($(this).hasClass("more-less-toggle-less")) {
                $(this).removeClass("more-less-toggle-less").html($(this).data('more-text'));
                $(this).parent().find('.more-less-more-content').hide();
                $(this).parent().find('.more-less-ellipsis').show();
            } else {
                $(this).addClass("more-less-toggle-less").html($(this).data('less-text'));
                $(this).parent().find('.more-less-more-content').show();
                $(this).parent().find('.more-less-ellipsis').hide();
            }
          });
      }
    });
  };
})(jQuery);
