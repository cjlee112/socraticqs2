import Cookie from 'js-cookie';

export function uploadFile(formData){
    return fetch('/api/v0/bp/upload/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': Cookie.get('csrftoken'),
      },
      body: formData,
    }).then(
      resp => resp.json()
    ).catch(
      error => console.log(error)
    );
  }
