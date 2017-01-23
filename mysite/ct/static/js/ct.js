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
