function setInterest(targeturl, state, csrftoken)
{
  $.post(targeturl,
  {
    csrfmiddlewaretoken:csrftoken,
    state:state
  });
}

function toggleInterest(o, targeturl, csrftoken)
{
  if (o.value == "1")
  {
    o.value="0";
  }
  else
  {
    o.value="1";
  }
  setInterest(targeturl, o.value, csrftoken);
}

$(document).ready(function(){
    var elements = $("#div_id_number_max_value,#div_id_number_min_value,#div_id_number_precision,#div_id_enable_auto_grading");
    var attachmentContainer = $('.draw-svg-preview');
    var sub_kind_field = $('#id_sub_kind');

    sub_kind_field.on('change', function(e) {
        $(elements).hide();
        $(attachmentContainer).hide();
        switch ($(this).val()) {
            case 'numbers':
                elements.show();
                break;
            case 'canvas':
                attachmentContainer.show();
                break;
            default:
                $('#id_enable_auto_grading').prop('checked', false);
                break;
        }
    }).change();
});
