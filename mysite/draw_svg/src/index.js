import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import DrawApp from './DrawApp';
import registerServiceWorker from './registerServiceWorker';


document.drawToElement = function (elements, onChange) {
    Array.from(elements).forEach((e) => {
        ReactDOM.render(<DrawApp onChange={onChange} svg={e.innerHTML}/>, e);
    });
};

document.drawToElement(document.getElementsByClassName('draw-svg-container-demo'), function(data) {
    console.log(data);
});
registerServiceWorker();
