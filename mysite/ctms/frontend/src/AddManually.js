import React from 'react';
import Cookie from 'js-cookie';

import {NavLink} from 'react-router-dom';

export class AddManually extends React.Component {
  render() {
    return (  
      <div>

        <main className="card__content">
          <form action={window.location} method="POST">
            <input type="hidden" name="csrfmiddlewaretoken" value={Cookie.get("csrftoken")} />
            <label for="id_title" className="card__title">Add a Thread Manually</label>
            <p className="content--medium">
              Use this option to add a new thread on your own. If you prefer, you can also
              <NavLink to="/upload"> upload a document </NavLink> and let our experienced instructors do it for you.
            </p>
            <label htmlFor="new-todo">
              Thread title.
            </label>
            <p className="content--large">
              Choose a name that's short – a few words – and distinct – that helps students easily recognize this question within the list shown in the sidebar. For example, if your courselet presented questions about probability, and this question was the only one that featured trains (as an example), you could name it something like "Two Trains". Don't try to make the name a summary of what the question's asking -- that will be too long.
            </p>
            <input
              id="new-todo"
              type="text"
              name="title"
            />
            <input type="submit" value="Add Thread" />

          </form>
        </main>
      </div>
    );
  }
}
