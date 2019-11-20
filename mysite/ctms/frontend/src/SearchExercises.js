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
            <label htmlFor="id_title" className="card__title">Search for Exercises</label>
            <p className="content--medium">
            You can search Courselets for exercises to add. Please note that you will be redirected to the <b>old Instructor interface</b> to use this feature.
            </p>
            <button type="button" onClick={this.handleClick} className="button button--primary button--search">Search for Exercises</button>
        </main>
      </div>
    );
  }
  handleClick(e) {
    e.preventDefault();
    window.location=window.searchUrl;
  }
}
