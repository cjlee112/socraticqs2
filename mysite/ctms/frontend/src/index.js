import React from 'react';
import ReactDOM from 'react-dom';
import registerServiceWorker from './registerServiceWorker';


import { HashRouter } from 'react-router-dom';

import {AddThreads} from './addThreads';


ReactDOM.render(
  <HashRouter>
    <AddThreads />
  </HashRouter>,
    document.getElementById('add-threads-root')
  );
registerServiceWorker();

