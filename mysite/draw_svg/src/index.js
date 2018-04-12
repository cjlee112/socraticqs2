import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import DrawApp from './DrawApp';
import registerServiceWorker from './registerServiceWorker';


document.drawToElement = function (elements) {
    Array.from(elements).forEach((e) => {
        ReactDOM.render(<DrawApp/>, e);
    })
};

document.drawToElement(document.getElementsByClassName('draw-svg-container'));
registerServiceWorker();
