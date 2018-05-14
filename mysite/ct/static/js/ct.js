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
    var GRADEABLE_SUB_KINDS = ['numbers', 'equation'];

    var number_elements = $("#div_id_number_max_value,#div_id_number_min_value,#div_id_number_value");
    var grading_elements = $("#div_id_enable_auto_grading");
    var sub_kind_field = $('#id_sub_kind');

    if (sub_kind_field.val() !== 'numbers') {
      number_elements.hide();
    }


    if ($.inArray(sub_kind_field.val(), GRADEABLE_SUB_KINDS) == -1 ) {
        grading_elements.hide();
    }

    sub_kind_field.on('change', function(e){
        //  show and hide numbers related fields
        if ($.inArray($(this).val(), GRADEABLE_SUB_KINDS) != -1 ) {
          grading_elements.show();
        } else {
          grading_elements.hide();
          $("#id_enable_auto_grading").prop('checked', false);
        }
    })
});
