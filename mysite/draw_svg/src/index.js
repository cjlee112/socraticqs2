import React from 'react';
import ReactDOM from 'react-dom';
import './index.scss';
import DrawApp from './DrawApp';


document.drawToElement = function (elements, onChange) {
    Array.from(elements).forEach((e) => {
        ReactDOM.render(<DrawApp onChange={onChange} svg={e.innerHTML}/>, e);
    });
};


if (process.env.NODE_ENV !== 'production') {
  document.drawToElement(document.getElementsByClassName('draw-svg-container-demo'), function(data) {
    console.log(data);
  });
}
