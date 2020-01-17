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
     * @type {CUI.ThreadNavBar.state.{hidden|scrollToCurrentQuestion|showSubsequentThreads}}
     */
    this._state = CUI.ThreadNavBar.state.hidden;

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
 * Toggler button text when in updates mode and showing subsequent threads.
 */
CUI.ThreadNavBar.strings.scrollToCurrentQuestion = '↑ Scroll to Current Question';


/**
 * Toggler button text when in a thread with updates.
 */
CUI.ThreadNavBar.strings.scrollToSubsequentThreads = '↓ Show Subsequent Threads';

/**
 * Class static states naemspace.
 */
CUI.ThreadNavBar.state = CUI.ThreadNavBar.state || {};
CUI.ThreadNavBar.state.hidden = "hidden";
CUI.ThreadNavBar.state.scrollToQuestion = "scrollToQuestion";
CUI.ThreadNavBar.state.scrollToQuestionWithUpdates = "scrollToQuestionWithUpdates";
CUI.ThreadNavBar.state.showSubsequentThreads = "showSubsequentThreads";
CUI.ThreadNavBar.state.subsequentThreadsAreShowed = "subsequentThreadsAreShowed";

/**
 * Setup event callbacks.
 * @private
 */
CUI.ThreadNavBar.prototype._setupEventCallbacks = function() {
    this.$threadNavBarTogglerButton.on('click', $.proxy(onThreadNavBarTogglerButtonClick, this));
};

/**
 * Behaive according to current state.
 * @private
 */
CUI.ThreadNavBar.prototype._update = function() {
    console.log('Updating state to : ', this._state);
    switch(this._state) {
        case CUI.ThreadNavBar.state.hidden:
            this.$rootElement.hide();
            break;

        case CUI.ThreadNavBar.state.scrollToQuestion:
            this.$rootElement.show();
            this.$threadNavBarTogglerButton.text(CUI.ThreadNavBar.strings.scrollToCurrentQuestion);
            break;

        case CUI.ThreadNavBar.state.scrollToQuestionWithUpdates:
        case CUI.ThreadNavBar.state.subsequentThreadsAreShowed:
            this.$rootElement.show();
            this.$threadNavBarTogglerButton.text(CUI.ThreadNavBar.strings.scrollToCurrentQuestion);
            break;

        case CUI.ThreadNavBar.state.showSubsequentThreads:
            this.$rootElement.show();
            this.$threadNavBarTogglerButton.text(CUI.ThreadNavBar.strings.scrollToSubsequentThreads);
            break;

        default:
            this.$rootElement.hide();
            break;
    }
};

/**
 * Set current state.
 * @public
 * @param {CUI.ThreadNavBar.state.{hidden|scrollToQuestion|showSubsequentThreads}} state
 */
CUI.ThreadNavBar.prototype.setState = function(state) {
    if (this._state === state) {
        return;
    }

    console.log('NAVBAR SETTINGS STATE TO: ', state);

    this._state = state;
    this._update()
};

/**
 * Set scroll to question state (depends on the current state).
 * @public
 */
CUI.ThreadNavBar.prototype.setScrollToQuestionState = function() {
    if (this._state === CUI.ThreadNavBar.state.scrollToQuestionWithUpdates) {
        return;
    }

    this.setState(CUI.ThreadNavBar.state.scrollToQuestion);
};

/**
 * Set show subsequent threads state (depends on the current state).
 * @public
 */
CUI.ThreadNavBar.prototype.setShowSubsequentThreadsState = function() {
    if (this._state === CUI.ThreadNavBar.state.scrollToQuestionWithUpdates) {
        return;
    }

    this.setState(CUI.ThreadNavBar.state.showSubsequentThreads);
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
 * An on thread navigation bar toggler button click event handler.
 * @global
 * @param {MouseEvent} event
 */
function onThreadNavBarTogglerButtonClick(event) {
    event.preventDefault();

    console.log('threadNavBar State is: ', this._state);

    switch(this._state) {
        case CUI.ThreadNavBar.state.scrollToQuestion:
            this._scrollToQuestionCallback();
            // this.setState(CUI.ThreadNavBar.state.hidden);
            break;

        case CUI.ThreadNavBar.state.scrollToQuestionWithUpdates:
        case CUI.ThreadNavBar.state.subsequentThreadsAreShowed:
            this._scrollToQuestionWithUpdatesCallback();
            this.setState(CUI.ThreadNavBar.state.showSubsequentThreads);
            break;

        case CUI.ThreadNavBar.state.showSubsequentThreads:
            this._showSubsequentThreadsCallback();
            this.setState(CUI.ThreadNavBar.state.scrollToQuestionWithUpdates);
            break;

        default:
            break;
    }
};