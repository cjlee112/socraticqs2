import React from 'react';


export class SearchExercises extends React.Component {
  constructor(props) {
    super(props);
    this.handleClick = this.handleClick.bind(this);
  }

  render() {
    return (  
      <div>
        <main className="card__content">
            <label for="id_title">Search for Exercises</label>
            <p>
            You can search Courselets for exercises to add. Please note that you will be redirected to the old Instructor interface to use this feature.
            </p>
            <button type="button" onClick={this.handleClick} class="button button--primary">Search for Exercises</button>
        </main>
      </div>
    );
  }
  handleClick(e) {
    e.preventDefault();
    window.location=window.searchUrl;
  }
}
