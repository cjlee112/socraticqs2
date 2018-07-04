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
    var number_elements = $("#div_id_number_max_value,#div_id_number_min_value,#div_id_number_value");
    var grading_elements = $("#div_id_enable_auto_grading");

    var attachmentContainer = $('.draw-svg-preview,#div_id_attachment_clear');
    var sub_kind_field = $('#id_sub_kind');

    sub_kind_field.on('change', function() {
        $(grading_elements).hide();
        $(number_elements).hide();
        $(attachmentContainer).hide();
        switch ($(this).val()) {
            case 'numbers':
                number_elements.show();
                grading_elements.show();
                break;
            // gradings
            case 'equation':
                grading_elements.show();
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
