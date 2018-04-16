import React, {Component} from 'react';
import ReactDOM from 'react-dom';

import * as d3 from "d3";
import {CompactPicker} from 'react-color';


class DrawApp extends Component {

    constructor(props) {
        super(props);
        this.state = {
            'container': null,

            'brush': 'pencil',
            'color': '#000000',
            'width': 4,

            'showColorPicker': false,
            'showShapes': false,
            'showWidths': false,
            'isUploading': false,

            'figures': [],
            'redoFigures': [],
        };
        this.changeBrush = this.changeBrush.bind(this);
        this.changeWidth = this.changeWidth.bind(this);
        this.hidePopups = this.hidePopups.bind(this);
        this.onKeyDown = this.onKeyDown.bind(this);
        this.toggleEditor = this.toggleEditor.bind(this);
    }

    componentDidMount() {
        let svg = d3.select(this.node);
        svg.call(d3.drag().on('start', () => {
            this.hidePopups();
            if (!this.isEnabled()) {
                return;
            }
            switch (this.state.brush) {
                case 'line':
                    this.drawLine();
                    break;
                case 'triangle':
                    this.drawTriangle();
                    break;
                case 'circle':
                    this.drawCircle();
                    break;
                case 'rect':
                    this.drawRect();
                    break;
                default:
                    this.drawFree();
                    break;
            }
        }));
        this.setState({
            'container': ReactDOM.findDOMNode(this).parentNode,
        });
        window.addEventListener('keydown', this.onKeyDown);
    }

    componentWillUnmount() {
        window.removeEventListener('keydown', this.onKeyDown);
    }

    changeBrush(event) {
        this.setState({
            'brush': event.currentTarget.getAttribute('data-brush')
        })
    }

    changeWidth(event) {
        this.setState({
            'width': parseInt(event.currentTarget.getAttribute('data-width'), 10),
        });
    }

    createFigure(type) {
        let svg = d3.select(this.node);
        let figure = svg.append(type);
        figure.attr('class', 'figure');
        figure.attr('style', 'stroke: ' + this.state.color + '; stroke-width: ' + this.state.width + 'px');
        return figure;
    }

    drawTriangle() {
        let figure = this.createFigure('polygon');
        let figures = this.state.figures;
        figures.push(figure);
        this.setState({
            'figures': figures,
            'redoFigures': [],
        });
        const x = d3.mouse(this.node)[0];
        const y = d3.mouse(this.node)[1];
        let radius = 1;
        figure.attr('points', [
            [x, y - radius],
            [x + radius, y + radius],
            [x - radius, y + radius],
        ]);
        d3.event.on('drag', () => {
            const coordX = d3.mouse(this.node)[0];
            const coordY = d3.mouse(this.node)[1];
            let radius = Math.abs(coordX - x);
            if (coordX - x > 0) {
                figure.attr('points', [
                    [x, y],
                    [coordX, coordY],
                    [x - radius, coordY],
                ]);
            } else {
                figure.attr('points', [
                    [x, y],
                    [coordX, coordY],
                    [x + radius, coordY],
                ]);
            }
            this.onChange();
        });
    }

    drawLine() {
        let figure = this.createFigure('line');
        let figures = this.state.figures;
        figures.push(figure);
        this.setState({
            figures: figures,
            redoFigures: [],
        });
        const x = d3.mouse(this.node)[0];
        const y = d3.mouse(this.node)[1];
        figure.attr('x1', x).attr('y1', y);
        figure.attr('x2', x).attr('y2', y);
        d3.event.on('drag', () => {
            const coordX = d3.mouse(this.node)[0];
            const coordY = d3.mouse(this.node)[1];
            figure.attr('x2', coordX).attr('y2', coordY);
            this.onChange();
        });
    }

    drawCircle() {
        let figure = this.createFigure('circle');
        let figures = this.state.figures;
        figures.push(figure);
        this.setState({
            'figures': figures,
            'redoFigures': [],
        });
        const x = d3.mouse(this.node)[0];
        const y = d3.mouse(this.node)[1];
        figure.attr('cx', x).attr('cy', y);
        d3.event.on('drag', () => {
            const coordX = d3.mouse(this.node)[0];
            figure.attr('r', Math.abs(coordX - x));
            this.onChange();
        });
    }

    drawRect() {
        let figure = this.createFigure('rect');
        let figures = this.state.figures;
        figures.push(figure);
        this.setState({
            'figures': figures,
            'redoFigures': [],
        });
        const x = d3.mouse(this.node)[0];
        const y = d3.mouse(this.node)[1];
        figure.attr('x', x).attr('y', y);
        d3.event.on('drag', () => {
            const coordX = d3.mouse(this.node)[0];
            const coordY = d3.mouse(this.node)[1];
            if ((coordX - x) > 0) {
                figure.attr('width', coordX - x);
            } else {
                figure.attr('x', coordX);
                figure.attr('width', x - coordX);
            }
            if ((coordY - y) > 0) {
                figure.attr('height', coordY - y);
            } else {
                figure.attr('y', coordY);
                figure.attr('height', y - coordY);
            }
            this.onChange();
        });
    }

    drawFree() {
        let figure = this.createFigure('path').datum([]);
        let renderPath = d3.line()
            .x(function (d) {
                return d[0];
            })
            .y(function (d) {
                return d[1];
            });
        let figures = this.state.figures;
        figures.push(figure);
        this.setState({
            'figures': figures,
            'redoFigures': [],
        });
        figure.datum().push(d3.mouse(this.node));
        d3.event.on('drag', () => {
            figure.datum().push(d3.mouse(this.node));
            figure.attr('d', renderPath);
            this.onChange();
        });
    }

    undo() {
        let figures = this.state.figures;
        let redoFigures = this.state.redoFigures;
        if (figures.length) {
            const figure = figures.splice(-1, 1)[0];
            redoFigures.push(figure);
            figure.remove();
            this.setState({
                'figures': figures,
                'redoFigures': redoFigures,
            }, this.onChange);
        }
    }

    redo() {
        let figures = this.state.figures;
        let redoFigures = this.state.redoFigures;
        if (redoFigures.length) {
            const figure = redoFigures.splice(-1, 1)[0];
            figures.push(figure);
            this.node.appendChild(figure.node());
            this.setState({
                'figures': figures,
                'redoFigures': redoFigures,
            }, this.onChange);
        }
    }

    onChange() {
        try {
            this.props.onChange(this.node.outerHTML);
        } catch (e) {}
    }

    handleChangeColor(color) {
        this.setState({
            'color': color.hex,
            'showColorPicker': false,
        });
    }

    isEnabled() {
        if (this.state.container) {
            return ['disabled', 'true', '1', ''].indexOf(this.state.container.getAttribute('disabled')) === -1;
        } else {
            return false;
        }
    }

    toggleEditor() {
        if (this.isEnabled()) {
            this.state.container.removeAttribute('disabled');
        } else {
            this.state.container.setAttribute('disabled', 'disabled');
        }
    }

    toggleColorPicker() {
        let showColorPicker = !this.state.showColorPicker;
        this.hidePopups();
        this.setState({'showColorPicker': showColorPicker});
    }

    toggleShapes() {
        let showShapes = !this.state.showShapes;
        this.hidePopups();
        this.setState({'showShapes': showShapes});
    }

    toggleWidths() {
        let showWidths = !this.state.showWidths;
        this.hidePopups();
        this.setState({'showWidths': showWidths});
    }

    hidePopups() {
        this.setState({
            'showShapes': false,
            'showColorPicker': false,
            'showWidths': false,
        });
    }

    onKeyDown(event) {
        switch (event.key.toLowerCase()) {
            case 'escape':
                this.hidePopups();
                break;
            case 'z':
                if (event.ctrlKey || event.metaKey) {
                    if (event.shiftKey) {
                        this.redo();
                    } else {
                        this.undo();
                    }
                }
                break;
            default:
                break;
        }
    }

    save() {
        this.setState({
                'isUploading': true,
            }, () =>
                fetch('/api/v0/echo/data/', {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(this.node.outerHTML),
                }).then(function (response) {
                    this.setState({
                        'isUploading': false,
                    });
                    console.log(response);
                }.bind(this)).catch(function (error) {
                    console.log(error);
                })
        );
    }

    render() {
        let actions = this.isEnabled() ? (
            <div className="border-bottom actions">
                <button className="btn" onClick={this.undo.bind(this)} disabled={!this.state.figures.length}>
                    <span className="oi oi-action-undo"/>
                </button>
                <button className="btn" onClick={this.redo.bind(this)} disabled={!this.state.redoFigures.length}>
                    <span className="oi oi-action-redo"/>
                </button>
                <button className="btn" onClick={this.save.bind(this)} disabled={this.state.isUploading}>
                    <span className="oi oi-cloud-upload"/>
                </button>

                <div className={this.state.showShapes ? 'shapes-wrapper active' : 'shapes-wrapper'}
                     onClick={this.toggleShapes.bind(this)}>
                    <label>Shape</label>
                    <div className="shapes">
                        <button className={this.state.brush === 'circle' ? 'btn active' : 'btn'}
                                onClick={this.changeBrush}
                                data-brush="circle">
                            <span className="oi oi-media-record"/>
                        </button>
                        <button className={this.state.brush === 'rect' ? 'btn active' : 'btn'}
                                onClick={this.changeBrush}
                                data-brush="rect">
                            <span className="oi oi-media-stop"/>
                        </button>
                        <button className={this.state.brush === 'triangle' ? 'btn active' : 'btn'}
                                onClick={this.changeBrush} data-brush="triangle">
                            <span className="oi oi-caret-top"/>
                        </button>
                        <button className={this.state.brush === 'line' ? 'btn active' : 'btn'}
                                onClick={this.changeBrush} data-brush="line">
                            <span className="oi oi-minus"/>
                        </button>
                        <button className={this.state.brush === 'pencil' ? 'btn active' : 'btn'}
                                onClick={this.changeBrush}
                                data-brush="pencil">
                            <span className="oi oi-pencil"/>
                        </button>
                    </div>
                </div>
                <label>Color <button type="button" className="btn color-picker-handler"
                                     style={{backgroundColor: this.state.color}}
                                     onClick={this.toggleColorPicker.bind(this)}/></label>
                <div className={this.state.showColorPicker ? 'color-picker' : 'color-picker hidden'}>
                    <CompactPicker onChange={this.handleChangeColor.bind(this)}/>
                </div>

                <div className={this.state.showWidths ? 'widths-wrapper active' : 'widths-wrapper'}
                     onClick={this.toggleWidths.bind(this)}>
                    <label>Width</label>
                    <div className="widths">
                        <button className={this.state.width === 2 ? 'btn active' : 'btn'}
                                onClick={this.changeWidth}
                                data-width="2">1
                        </button>
                        <button className={this.state.width === 4 ? 'btn active' : 'btn'}
                                onClick={this.changeWidth}
                                data-width="4">2
                        </button>
                        <button className={this.state.width === 6 ? 'btn active' : 'btn'}
                                onClick={this.changeWidth} data-width="6">3
                        </button>
                        <button className={this.state.width === 8 ? 'btn active' : 'btn'}
                                onClick={this.changeWidth} data-width="8">4
                        </button>
                        <button className={this.state.width === 10 ? 'btn active' : 'btn'}
                                onClick={this.changeWidth} data-width="10">5
                        </button>
                    </div>
                </div>

            </div>
        ) : null;

        return (
            <div className="text-center">
                {actions}
                <svg ref={(node) => this.node = node} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 841.9 595.3"
                     preserveAspectRatio="xMidYMid meet"
                     width={500} height={500}>
                    <g fill="#61DAFB">
                        <path
                            d="M666.3 296.5c0-32.5-40.7-63.3-103.1-82.4 14.4-63.6 8-114.2-20.2-130.4-6.5-3.8-14.1-5.6-22.4-5.6v22.3c4.6 0 8.3.9 11.4 2.6 13.6 7.8 19.5 37.5 14.9 75.7-1.1 9.4-2.9 19.3-5.1 29.4-19.6-4.8-41-8.5-63.5-10.9-13.5-18.5-27.5-35.3-41.6-50 32.6-30.3 63.2-46.9 84-46.9V78c-27.5 0-63.5 19.6-99.9 53.6-36.4-33.8-72.4-53.2-99.9-53.2v22.3c20.7 0 51.4 16.5 84 46.6-14 14.7-28 31.4-41.3 49.9-22.6 2.4-44 6.1-63.6 11-2.3-10-4-19.7-5.2-29-4.7-38.2 1.1-67.9 14.6-75.8 3-1.8 6.9-2.6 11.5-2.6V78.5c-8.4 0-16 1.8-22.6 5.6-28.1 16.2-34.4 66.7-19.9 130.1-62.2 19.2-102.7 49.9-102.7 82.3 0 32.5 40.7 63.3 103.1 82.4-14.4 63.6-8 114.2 20.2 130.4 6.5 3.8 14.1 5.6 22.5 5.6 27.5 0 63.5-19.6 99.9-53.6 36.4 33.8 72.4 53.2 99.9 53.2 8.4 0 16-1.8 22.6-5.6 28.1-16.2 34.4-66.7 19.9-130.1 62-19.1 102.5-49.9 102.5-82.3zm-130.2-66.7c-3.7 12.9-8.3 26.2-13.5 39.5-4.1-8-8.4-16-13.1-24-4.6-8-9.5-15.8-14.4-23.4 14.2 2.1 27.9 4.7 41 7.9zm-45.8 106.5c-7.8 13.5-15.8 26.3-24.1 38.2-14.9 1.3-30 2-45.2 2-15.1 0-30.2-.7-45-1.9-8.3-11.9-16.4-24.6-24.2-38-7.6-13.1-14.5-26.4-20.8-39.8 6.2-13.4 13.2-26.8 20.7-39.9 7.8-13.5 15.8-26.3 24.1-38.2 14.9-1.3 30-2 45.2-2 15.1 0 30.2.7 45 1.9 8.3 11.9 16.4 24.6 24.2 38 7.6 13.1 14.5 26.4 20.8 39.8-6.3 13.4-13.2 26.8-20.7 39.9zm32.3-13c5.4 13.4 10 26.8 13.8 39.8-13.1 3.2-26.9 5.9-41.2 8 4.9-7.7 9.8-15.6 14.4-23.7 4.6-8 8.9-16.1 13-24.1zM421.2 430c-9.3-9.6-18.6-20.3-27.8-32 9 .4 18.2.7 27.5.7 9.4 0 18.7-.2 27.8-.7-9 11.7-18.3 22.4-27.5 32zm-74.4-58.9c-14.2-2.1-27.9-4.7-41-7.9 3.7-12.9 8.3-26.2 13.5-39.5 4.1 8 8.4 16 13.1 24 4.7 8 9.5 15.8 14.4 23.4zM420.7 163c9.3 9.6 18.6 20.3 27.8 32-9-.4-18.2-.7-27.5-.7-9.4 0-18.7.2-27.8.7 9-11.7 18.3-22.4 27.5-32zm-74 58.9c-4.9 7.7-9.8 15.6-14.4 23.7-4.6 8-8.9 16-13 24-5.4-13.4-10-26.8-13.8-39.8 13.1-3.1 26.9-5.8 41.2-7.9zm-90.5 125.2c-35.4-15.1-58.3-34.9-58.3-50.6 0-15.7 22.9-35.6 58.3-50.6 8.6-3.7 18-7 27.7-10.1 5.7 19.6 13.2 40 22.5 60.9-9.2 20.8-16.6 41.1-22.2 60.6-9.9-3.1-19.3-6.5-28-10.2zM310 490c-13.6-7.8-19.5-37.5-14.9-75.7 1.1-9.4 2.9-19.3 5.1-29.4 19.6 4.8 41 8.5 63.5 10.9 13.5 18.5 27.5 35.3 41.6 50-32.6 30.3-63.2 46.9-84 46.9-4.5-.1-8.3-1-11.3-2.7zm237.2-76.2c4.7 38.2-1.1 67.9-14.6 75.8-3 1.8-6.9 2.6-11.5 2.6-20.7 0-51.4-16.5-84-46.6 14-14.7 28-31.4 41.3-49.9 22.6-2.4 44-6.1 63.6-11 2.3 10.1 4.1 19.8 5.2 29.1zm38.5-66.7c-8.6 3.7-18 7-27.7 10.1-5.7-19.6-13.2-40-22.5-60.9 9.2-20.8 16.6-41.1 22.2-60.6 9.9 3.1 19.3 6.5 28.1 10.2 35.4 15.1 58.3 34.9 58.3 50.6-.1 15.7-23 35.6-58.4 50.6zM320.8 78.4z"/>
                        <circle cx="420.9" cy="296.5" r="45.7"/>
                    </g>
                </svg>
            </div>
        );
    }

}

export default DrawApp;
