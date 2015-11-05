(function(){
  window.Courselets = {

    init: function(){
      this.initAffix();
      this.initButtons();
      this.initFAQ();
      this.initForms();
    },

    initAffix: function(){
      $('.cta-bar').affix({
        offset: {
            top: $('.cta-bar').offset().top
        }
      });
    },

    initButtons: function(){
      $('.im-interested').on('click', function(e){
        e.preventDefault();
        $('html, body').animate({
            scrollTop: $("#interested").offset().top
        }, 1200);
      })
    },

    initFAQ: function(){
      $('.faq dt').on('click', function(e){
        e.preventDefault();

        $(this).closest('dt').next().slideToggle();
      })
    },

    initForms: function(){
      $form = $('#interested-form');

      $form.on('submit', function(e){
        e.preventDefault();

        // Validate form
        if($form.isValid({}, {scrollToTopOnError: false})){
          // Serialize form
          var formData = $form.serialize();

          // Post form
          $.ajax({
            type: 'POST',
            url: '/xxx',
            data: formData,
            dataType: 'json'
          }).done(function(data){

            // Display success message
            if(data.success) {
              base.showMessage('success', data.success);

            // Display error message
            }else if(data.error){
              base.showMessage('error', data.error);
            }

          }).fail(function(){
            base.showMessage('error', 'Something went wrong. Please try again later.');
          });

        // Show validation errors
        }else{

          // Scroll to first error message
          $('html, body').animate({
              scrollTop: $(".form-error").offset().top-200
          }, 600);
        }
      });
    },

    showMessage: function(type, message){
      if(type == 'error') type = 'danger';

      $messageContainer = $('.message-container');

      // Create message
      $messageContainer.html('<div class="alert alert-'+type+'"><div class="container">'+message+'</div></div>');

      // Scroll to message
      $('html, body').animate({
          scrollTop: $messageContainer.offset().top-100
      }, 600);
    }
  };
  var base = window.Courselets;

  $(function(){
    Courselets.init();
  });
})();
