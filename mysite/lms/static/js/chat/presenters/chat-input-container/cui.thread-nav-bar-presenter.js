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
     * Show all threads callback.
     * @type {function}
     * @private
     */
    this._showAllThreadsCallback = function () {};

    /**
     * Show specific thread callback.
     * @type {function}
     * @private
     */
    this._showThreadCallback = function () {};

    this._setupEventCallbacks();

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
 * Setup event callbacks.
 * @private
 */
CUI.ThreadNavBar.prototype._setupEventCallbacks = function() {
    this.$threadNavBarTogglerButton.on('click', $.proxy(onThreadNavBarTogglerButtonClick, this));
};

/**
 * Show thread navigtaion button.
 * @public
 */
CUI.ThreadNavBar.prototype.show = function() {
    this.$rootElement.show();
};

/**
 * Hide thread navigation bar.
 * @public
 */
CUI.ThreadNavBar.prototype.hide = function() {
    this.$rootElement.hide();
};

/**
 * Updates thread navigation toggler button state.
 * @private
 */
CUI.ThreadNavBar.prototype._updateState = function() {
    if (this._isInUpdates) {
        this.$threadNavBarTogglerButton.text(CUI.ThreadNavBar.strings.scrollToSubsequentThreads);
    } else {
        this.$threadNavBarTogglerButton.text(CUI.ThreadNavBar.strings.scrollToCurrentQuestion);
    }
};

/**
 * Set callback to show all threads.
 */
CUI.ThreadNavBar.prototype.setShowAllThreadsCallback = function(callback) {
    this._showAllThreadsCallback = callback;
};

/**
 * Set callback to show specific thread.
 */
CUI.ThreadNavBar.prototype.setShowThreadCallback = function(callback) {
    this._showThreadCallback = callback;
};

/**
 * An on thread navigation bar toggler button click event handler.
 * @param {MouseEvent} event
 */
function onThreadNavBarTogglerButtonClick(event) {
    event.preventDefault();

    console.log('onThreadNavBarTogglerButtonClick!', event)

    if (this._isInUpdates) {
        this.$threadNavBarTogglerButton.text(CUI.ThreadNavBar.strings.scrollToSubsequentThreads);
        this._showAllThreadsCallback();
    } else {
        this.$threadNavBarTogglerButton.text(CUI.ThreadNavBar.strings.scrollToCurrentQuestion);
        this._showThreadCallback()
    }

    this._isInUpdates = !this._isInUpdates;
};