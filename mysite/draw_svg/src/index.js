import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import DrawApp from './DrawApp';
import registerServiceWorker from './registerServiceWorker';

ReactDOM.render(<DrawApp />, document.getElementById('root'));
registerServiceWorker();
