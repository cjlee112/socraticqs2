import React from 'react';

import {
  Route,
  NavLink,
  Switch,
  Redirect
} from 'react-router-dom';

import {AddManually} from './AddManually';
import {UploadDocument} from './UploadDocument';
import {SearchExercises} from './SearchExercises'


export class AddThreads extends React.Component {

  constructor(props){
    super(props);
    this.state = {
      fileName: '',
      bestPracticeId: ''
    }
    this.updateData = this.updateData.bind(this);
  }

  updateData(state) {
    this.setState({
      fileName: state.fileName,
      bestPracticeId: state.bestPracticeId
    });
  }

  render(){
    return (
      <div className="card">
        <header className="card__topbar">
          <h1>Add Threads</h1>
          <nav class="card__nav">
            <ul>
              <li> <NavLink to="/add" activeClassName="card__nav-active">Add Manually</NavLink> </li>
              <li> <NavLink to="/upload" activeClassName="card__nav-active">Upload a Document</NavLink> </li>
              <li> <NavLink to="/search" activeClassName="card__nav-active">Search for Exercises</NavLink> </li>
            </ul>
          </nav>
        </header>
        <div className="App-intro">
          <Switch>
            <Route exact path="/add"  component={AddManually} />
            <Route path="/upload">
              <UploadDocument updateData={this.updateData} fileData={this.state}/>
            </Route>
            <Route path="/search" component={SearchExercises} />
            <Redirect to="/add" />
          </Switch>
        </div>
      </div>
    );
  }
}
