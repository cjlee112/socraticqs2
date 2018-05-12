import React from 'react';
import sinon from 'sinon';


import DrawApp from "./DrawApp";
import {configure, shallow, render, mount} from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

configure({adapter: new Adapter()});


const svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 841.9 595.3\" " +
    "xmlns:xlink=\"http://www.w3.org/1999/xlink\" preserveAspectRatio=\"xMidYMid meet\"" +
    " width=\"500\" height=\"500\"/>";


describe('<DrawApp />', () => {

    test('renders without crashing', () => {
        const wrapper = mount(<DrawApp/>);
    });

    test('should render a `.content`', () => {
        const wrapper = mount(<DrawApp svg={svg}/>);
        expect(wrapper.find('.canvas').length).toBe(1);
        expect(wrapper.props().svg).toBe(svg);
    });

    test('is enable', () => {
        const wrapper = mount(<DrawApp/>);
        expect(wrapper.instance().isEnabled()).toBe(true);
    });

    test('should render an `.actions`', () => {
        const wrapper = mount(<DrawApp/>);
        expect(wrapper.find('.actions').length).toBe(1);
    });

    test('should display colors panel', () => {
        const wrapper = mount(<DrawApp/>);
        wrapper.find('.colors-wrapper').simulate('click');
        expect([
            wrapper.state('showColorPicker'),
            wrapper.state('showShapes'),
            wrapper.state('showWidths'),
        ]).toEqual([
            true,
            false,
            false,
        ]);
    });

    test('should display shapes panel', () => {
        const wrapper = mount(<DrawApp/>);
        wrapper.find('.shapes-wrapper').simulate('click');
        expect([
            wrapper.state('showColorPicker'),
            wrapper.state('showShapes'),
            wrapper.state('showWidths'),
        ]).toEqual([
            false,
            true,
            false,
        ]);
    });

    test('should display width panel', () => {
        const wrapper = mount(<DrawApp/>);
        wrapper.find('.widths-wrapper').simulate('click');
        expect([
            wrapper.state('showColorPicker'),
            wrapper.state('showShapes'),
            wrapper.state('showWidths'),
        ]).toEqual([
            false,
            false,
            true,
        ]);
    });

    test('should change a shape', () => {
        const wrapper = mount(<DrawApp/>);
        expect(wrapper.state('brush')).toBe('pencil');

        wrapper.find('[data-brush="line"]').simulate('click');
        expect(wrapper.state('brush')).toBe('line');

        wrapper.find('[data-brush="triangle"]').simulate('click');
        expect(wrapper.state('brush')).toBe('triangle');

        wrapper.find('[data-brush="circle"]').simulate('click');
        expect(wrapper.state('brush')).toBe('circle');

        wrapper.find('[data-brush="rect"]').simulate('click');
        expect(wrapper.state('brush')).toBe('rect');

        wrapper.find('[data-brush="text"]').simulate('click');
        expect(wrapper.state('brush')).toBe('text');
    });

    test('should change a width', () => {
        const wrapper = mount(<DrawApp/>);
        expect(wrapper.state('width')).toBe(4);

        wrapper.find('[data-width="2"]').simulate('click');
        expect(wrapper.state('width')).toBe(2);

        wrapper.find('[data-width="4"]').simulate('click');
        expect(wrapper.state('width')).toBe(4);

        wrapper.find('[data-width="6"]').simulate('click');
        expect(wrapper.state('width')).toBe(6);

        wrapper.find('[data-width="8"]').simulate('click');
        expect(wrapper.state('width')).toBe(8);

        wrapper.find('[data-width="10"]').simulate('click');
        expect(wrapper.state('width')).toBe(10);
    });

    test('should create figure', () => {
        const wrapper = mount(<DrawApp/>);
        wrapper.instance().createFigure('circle');
        expect(wrapper.state('figures').length).toBe(1);
    });

    test('should undo', () => {
        const wrapper = mount(<DrawApp/>);
        const instance = wrapper.instance();
        instance.createFigure('circle');
        expect(wrapper.state('figures').length).toBe(1);
        expect(wrapper.state('redoFigures').length).toBe(0);

        instance.undo();
        expect(wrapper.state('figures').length).toBe(0);
        expect(wrapper.state('redoFigures').length).toBe(1);
    });

});