/**
 * @file Defines the class CUI.ThreadNavBar.
 */

var CUI = CUI || {};

/**
 * (Partially) Represents the chat input thread nvaigation bar.
 * @class
 * @param {Object} selectors - an Oject containing all neccessary selectors.
 * @param {string} selectors.rootSelector - a CSS selector for the nav bar element.
 * @param {string} selectors.buttonSelector - a CSS selector for the nav bar toggler button element.
 * @returns {CUI.ThreadNavBar}
 */
CUI.ThreadNavBar = function($rootElement, selectors) {
    selectors = selectors || {};

    if (!selectors.rootSelector) {
        selectors.rootSelector = '.thread-nav-bar';
    }

    if (!selectors.buttonSelector) {
        selectors.buttonSelector = '.thread-toggler-btn';
    }

    /**
     * a jQuery object represnetint the root element (usualy a thread navigation bar toggler).
     * @type {jQuery}
     * @private
     */
    this.$rootElement = $(selectors.rootSelector);

    /**
     * a jQuery object representing the thread navigation bat toggler button.
     * @type {jQuery}
     * @private
     */
    this.$threadNavBarTogglerButton = this.$rootElement.find(selectors.buttonSelector);

    /**
     * State flag, that indicates if a thread with updates is currently opened.
     * @type {boolean}
     * @private
     */
    this._isInUpdates = false;

    /**
     * Current state.
     * @type {CUI.ThreadNavBar.state.*}
     */
    this._state = CUI.ThreadNavBar.state.hidden;

    /**
     * Holds the previous state.
     * @type {CUI.ThreadNavBar.state.*}
     * @private
     */
    this._prevState = CUI.ThreadNavBar.state.none;

    /**
     * Current display text.
     * @type {CUI.ThreadNavBar.strings.displayText.*}
     * @private
     */
    this._displayText = '';

    /**
     * Current display arrow
     * @type {CUI.ThreadNavBar.strings.arrow.*}
     * @private
     */
    this._displayArrow = '';

    /**
     * Scroll to current question.
     * @type {function}
     * @private
     */
    this._scrollToQuestionCallback = function () {};

    /**
     * Scroll to question and hide subsequent threads callback.
     * @type {function}
     * @private
     */
    this._scrollToQuestionWithUpdatesCallback = function () {};

    /**
     * Show subsequent threads callback.
     * @type {function}
     * @private
     */
    this._showSubsequentThreadsCallback = function () {};


    this._setupEventCallbacks();

    this.$rootElement.hide();

    return this;
};

/**
 * Class static strings namespace.
 */
CUI.ThreadNavBar.strings = CUI.ThreadNavBar.strings || {};

/**
 * Display text strings.
 */
CUI.ThreadNavBar.strings.displayText = CUI.ThreadNavBar.strings.displayText || {};
CUI.ThreadNavBar.strings.displayText.scrollToCurrentQuestion = 'Scroll to Current Question';
CUI.ThreadNavBar.strings.displayText.scrollToSubsequentThreads = 'Show Subsequent Threads';
CUI.ThreadNavBar.strings.displayText.hideSubsequentThreads = 'Hide Subsequent Threads';

/**
 * Arrow symbols.
 */
CUI.ThreadNavBar.strings.arrow = CUI.ThreadNavBar.strings.arrow || {};
CUI.ThreadNavBar.strings.arrow.up = '↑';
CUI.ThreadNavBar.strings.arrow.down = '↓';

/**
 * Class static states naemspace.
 */
CUI.ThreadNavBar.state = CUI.ThreadNavBar.state || {};
CUI.ThreadNavBar.state.none = "none";
CUI.ThreadNavBar.state.hidden = "hidden";
CUI.ThreadNavBar.state.scrollToQuestion = "scrollToQuestion";
CUI.ThreadNavBar.state.scrollToQuestionWithUpdates = "scrollToQuestionWithUpdates";
CUI.ThreadNavBar.state.hideSubsequentThreads = "hideSubsequentThreads";
CUI.ThreadNavBar.state.showSubsequentThreads = "showSubsequentThreads";
CUI.ThreadNavBar.state.subsequentThreadsAreShowed = "subsequentThreadsAreShowed";

CUI.ThreadNavBar.stateMap = new Object();
CUI.ThreadNavBar.stateMap[CUI.ThreadNavBar.state.hidden] = [
    CUI.ThreadNavBar.state.scrollToQuestion,
    CUI.ThreadNavBar.state.showSubsequentThreads,
    CUI.ThreadNavBar.state.hideSubsequentThreads
];
CUI.ThreadNavBar.stateMap[CUI.ThreadNavBar.state.scrollToQuestion] = [
    CUI.ThreadNavBar.state.hidden,
];
CUI.ThreadNavBar.stateMap[CUI.ThreadNavBar.state.scrollToQuestionWithUpdates] = [
    CUI.ThreadNavBar.state.showSubsequentThreads,
    CUI.ThreadNavBar.state.hideSubsequentThreads,
    CUI.ThreadNavBar.state.hidden
];
CUI.ThreadNavBar.stateMap[CUI.ThreadNavBar.state.showSubsequentThreads] = [
    CUI.ThreadNavBar.state.scrollToQuestionWithUpdates,
    CUI.ThreadNavBar.state.hideSubsequentThreads,
    CUI.ThreadNavBar.state.hidden
];
CUI.ThreadNavBar.stateMap[CUI.ThreadNavBar.state.hideSubsequentThreads] = [
    CUI.ThreadNavBar.state.scrollToQuestionWithUpdates,
    CUI.ThreadNavBar.state.showSubsequentThreads,
    CUI.ThreadNavBar.state.hidden
];

/**
 * Sets up arrow.
 * @public
 */
CUI.ThreadNavBar.prototype.setUpArrow = function() {
    this._setArrow(CUI.ThreadNavBar.strings.arrow.up);
};

/**
 * Sets down arrow.
 * @public
 */
CUI.ThreadNavBar.prototype.setDownArrow = function() {
    this._setArrow(CUI.ThreadNavBar.strings.arrow.down);
};

/**
 * Sets current arrow and redraws text.
 * @private
 * @param {CUI.ThreadNavBar.strings.arrow.*} arrow  - an arrow type.
 */
CUI.ThreadNavBar.prototype._setArrow = function(arrow) {
    this._displayArrow = arrow;
    this._redrawText();
};

/**
 * Sets display text and redraws text.
 * @private
 * @param {CUI.ThreadNavBar.strings.displayText} displayText    - text to be displayed.
 */
CUI.ThreadNavBar.prototype._setDisplayText = function(displayText) {
    this._displayText = displayText;
    this._redrawText();
};

/**
 * Redraws current button text.
 * @private
 */
CUI.ThreadNavBar.prototype._redrawText = function() {
    this.$threadNavBarTogglerButton.text(this._displayArrow + ' ' + this._displayText);
};

/**
 * Hide navigation bar.
 * @private
 */
CUI.ThreadNavBar.prototype._hide = function() {
    this.$rootElement.hide();
};

/**
 * Show navigation bar.
 */
CUI.ThreadNavBar.prototype._show = function() {
    this.$rootElement.show();
};

/**
 * Setup event callbacks.
 * @private
 */
CUI.ThreadNavBar.prototype._setupEventCallbacks = function() {
    this.$threadNavBarTogglerButton.on('click', $.proxy(onThreadNavBarTogglerButtonClick, this));
};

/**
 * Behave according to current state.
 * @private
 */
CUI.ThreadNavBar.prototype._updateState = function() {
    switch(this._state) {
        case CUI.ThreadNavBar.state.scrollToQuestion:
        case CUI.ThreadNavBar.state.scrollToQuestionWithUpdates:
            this._show();
            this._setDisplayText(CUI.ThreadNavBar.strings.displayText.scrollToCurrentQuestion);
            this.setDownArrow();
            break;

        case CUI.ThreadNavBar.state.hideSubsequentThreads:
            this._show();
            this._setDisplayText(CUI.ThreadNavBar.strings.displayText.hideSubsequentThreads);
            this.setUpArrow();
            break;

        case CUI.ThreadNavBar.state.showSubsequentThreads:
            this._show();
            this._setDisplayText(CUI.ThreadNavBar.strings.displayText.scrollToSubsequentThreads);
            this.setDownArrow();
            break;

        case CUI.ThreadNavBar.state.hidden:
        default:
            this._hide();
            break;
    }
};

/**
 * Check if the new state is valid to transition to.
 * @private
 * @param {String} state    - new state.
 *
 * @returns {Boolean}
 */
CUI.ThreadNavBar.prototype._isValidState = function(state) {
    var isValid = false;
    var validTransitionStates = CUI.ThreadNavBar.stateMap[this._state];

    if (validTransitionStates) {
        isValid = validTransitionStates.includes(state);
    }

    return isValid;
};

/**
 * Set current state.
 * @public
 * @param {CUI.ThreadNavBar.state.*} state
 */
CUI.ThreadNavBar.prototype.setState = function(state) {
    if (this._state === state) {
        return;
    }

    if (this._isValidState(state)) {
        this._prevState = this._state;
        this._state = state;

        this._updateState()
    }
};

/**
 * Activate scroll to question state.
 * @public
 */
CUI.ThreadNavBar.prototype.activateScrollToQuestion = function() {
    switch (this._state) {
        case CUI.ThreadNavBar.state.hidden:
            this.setState(CUI.ThreadNavBar.state.scrollToQuestion);
            break;

        case CUI.ThreadNavBar.state.showSubsequentThreads:
        case CUI.ThreadNavBar.state.hideSubsequentThreads:
            this.setState(CUI.ThreadNavBar.state.scrollToQuestionWithUpdates);
    }
};

/**
 * Activate thread controls.
 * @public
 */
CUI.ThreadNavBar.prototype.activateThreadControls = function() {
    switch (this._state) {
        case CUI.ThreadNavBar.state.hidden:
            this.setState(CUI.ThreadNavBar.state.showSubsequentThreads);
            break;

        case CUI.ThreadNavBar.state.scrollToQuestionWithUpdates:
            this.setState(this._prevState);
            break;
    }
};

/**
 * Activate hide subsequent threads state.
 * @public
 */
CUI.ThreadNavBar.prototype.activateHideSubsequentThreadsState = function() {
    this.setState(CUI.ThreadNavBar.state.hideSubsequentThreads);
};

/**
 * Hide navigation bar.
 * @public
 */
CUI.ThreadNavBar.prototype.hide = function() {
    this.setState(CUI.ThreadNavBar.state.hidden);
};

/**
 * Set callback to scroll to current question.
 * @public
 */
CUI.ThreadNavBar.prototype.setScrollToQuestionCallback = function(callback) {
    this._scrollToQuestionCallback = callback;
};

/**
 * Set callback to scroll to question and hide subsequent threads.
 * @public
 */
CUI.ThreadNavBar.prototype.setScrollToQuestionWithUpdatesCallback = function(callback) {
    this._scrollToQuestionWithUpdatesCallback = callback;
};

/**
 * Set callback to show subsequent threads.
 * @public
 */
CUI.ThreadNavBar.prototype.setShowSubsequentThreadsCallback = function(callback) {
    this._showSubsequentThreadsCallback = callback;
};

/**
 * Set callback to show subsequent threads.
 * @public
 */
CUI.ThreadNavBar.prototype.setDetailNavText = function(detailNavText) {
    this.$rootElement.find('span').text(detailNavText);
};

/**
 * An on thread navigation bar toggler button click event handler.
 * @global
 * @param {MouseEvent} event
 */
function onThreadNavBarTogglerButtonClick(event) {
    event.preventDefault();

    switch(this._state) {
        case CUI.ThreadNavBar.state.scrollToQuestion:
        case CUI.ThreadNavBar.state.scrollToQuestionWithUpdates:
            this._scrollToQuestionCallback();
            break;

        case CUI.ThreadNavBar.state.hideSubsequentThreads:
            this._scrollToQuestionWithUpdatesCallback();
            this.setState(CUI.ThreadNavBar.state.showSubsequentThreads);
            break;

        case CUI.ThreadNavBar.state.showSubsequentThreads:
            this._showSubsequentThreadsCallback();
            this.setState(CUI.ThreadNavBar.state.hideSubsequentThreads);
            break;

        default:
            break;
    }
};