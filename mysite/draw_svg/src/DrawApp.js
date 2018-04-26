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
                case 'text':
                    this.printText();
                    break;
                default:
                    this.drawFree();
                    break;
            }
        }));
        let container = ReactDOM.findDOMNode(this).parentNode;
        container.addEventListener('disable-canvas', () => {
            container.setAttribute('disabled', 'disabled');
            this.setState({'enabled': false});
        });
        container.addEventListener('enable-canvas', () => {
            container.removeAttribute('disabled');
            this.setState({'enabled': true});
        });
        this.setState({
            'container': container,
        }, this.onChange);
        window.addEventListener('keydown', this.onKeyDown);
    }

    componentWillUnmount() {
        window.removeEventListener('keydown', this.onKeyDown);
    }

    changeBrush(event) {
        event.preventDefault();
        this.setState({
            'brush': event.currentTarget.getAttribute('data-brush')
        })
    }

    changeWidth(event) {
        event.preventDefault();
        this.setState({
            'width': parseInt(event.currentTarget.getAttribute('data-width'), 10),
        });
    }

    createFigure(type) {
        let svg = d3.select(this.node);
        let figure = svg.append(type);
        figure.attr('class', 'figure');
        figure.attr('style',
            'fill: none;' +
            'stroke-linejoin: round;' +
            'stroke-linecap: round;' +
            'stroke: ' + this.state.color + ';' +
            'stroke-width: ' + this.state.width + 'px;'
        );
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

    printText() {
        let figure = this.createFigure('text');
        figure.attr('style', figure.attr('style') +
            'font-size: ' + 10 * this.state.width + '; ' +
            'fill: ' + this.state.color + '; ' +
            'stroke-width: 1px; '
        );
        let figures = this.state.figures;
        figures.push(figure);
        this.setState({
            'figures': figures,
            'redoFigures': [],
        });
        const x = d3.mouse(this.node)[0];
        const y = d3.mouse(this.node)[1];

        figure.attr('x', x).attr('y', y);
        let text = figure.text('text...');

        let coords = text.node().getBoundingClientRect();
        let input = document.createElement('input');
        input.setAttribute('class', 'editor');
        input.setAttribute('style', 'top:' + Math.round(coords.top) + 'px; ' +
            'left: ' + Math.round(coords.left) + 'px; font-size: ' + 6 * this.state.width + 'px');
        this.node.parentElement.appendChild(input);

        function endPrint(event) {
            try {
                this.node.parentElement.removeChild(input);
            } catch (e) {}
        }
        endPrint = endPrint.bind(this);

        input.addEventListener('keyup', (e) => {
            figure.text(e.target.value);
            if (e.key === 'Enter') {
                endPrint(e);
            }
        });
        input.addEventListener('blur', endPrint);
        setTimeout(function() { input.focus(); }, 50);
    }

    undo(event) {
        event.preventDefault();
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

    redo(event) {
        event.preventDefault();
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
        } catch (e) {
        }
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

    toggleColorPicker(event) {
        event.preventDefault();
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
                        this.redo(event);
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
                        <button className={this.state.brush === 'text' ? 'btn active' : 'btn'}
                                onClick={this.changeBrush}
                                data-brush="text">
                            <span className="oi oi-text"/>
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

        let svg = this.props.svg;
        return (
            <div className="text-center">
                {actions}
                <div ref={(node) => {
                    if (node) {
                        this.node = node.children[0]
                    }
                }} dangerouslySetInnerHTML={{__html: svg}}/>
            </div>
        );
    }

}

export default DrawApp;
