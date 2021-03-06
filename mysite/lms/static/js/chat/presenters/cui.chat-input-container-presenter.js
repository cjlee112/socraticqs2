/**
 * @file Defines the class CUI.ChatInputContinerPresenter
 */

var CUI = CUI || {};

/**
 * (Partially) Represents the chat input container UI and keeps references of pre-exising DOM elements.
 * @class
 * @param {Object} selectors - an Oject containing all neccessary selectors.
 * @param {string} selectors.rootSelector - a CSS selector for the root element (input bar).
 * @param {string} selectors.chatControlsContainerSelector - a CSS selector for the controls container element.
 * @returns {CUI.ChatInputContinerPresenter}
 */
CUI.ChatInputContinerPresenter = function(selectors){
  selectors = selectors || {};

  if (!selectors.rootSelector) {
    selectors.rootSelector = '.chat-input-bar';
  }

  if (!selectors.innerSelector) {
    selectors.innerSelector = '.inner';
  }

  if (!selectors.chatControlsContainerSelector) {
    selectors.chatControlsContainerSelector = '.chat-container'
  }

  if (!selectors.chatInputContainer) {
    selectors.chatInputContainer = '.chat-input'
  }

  /**
   * A jQuery object containing DOM element of the root chat input bar.
   * @type {jQuery}
   * @public
   */
  this.$el = $(selectors.rootSelector);

  /**
   * A jQuery object containing DOM element of the inner container.
   * @type {jQuery}
   * @public
   */
  this.$inner = this.$el.find(selectors.innerSelector);

  /**
   * A jQuery object containing DOM element of the inner container.
   * @type {jQuery}
   * @public
   */
  this.$chatInput = this.$inner.find(selectors.chatInputContainer);

  /**
   * A jQuery reference to text input field.
   * @type {jQuery}
   * @public
   */
  this.$text = this.$chatInput.find('.chat-input-text');

  /**
   * A jQuery reference to an input for text.
   * @type {jQuery}
   * @public
   */
  this.$textarea = this.$text.find('.input-text');

   /**
   * A jQuery reference to an input for nubers.
   * @type {jQuery}
   * @public
   */
  this.$numbers = this.$text.find('.input-number');

   /**
   * A jQuery reference to an options container.
   * @type {jQuery}
   * @public
   */
  this.$options = this.$chatInput.find('.chat-input-options');

   /**
   * A jQuery reference to custom input container.
   * @type {jQuery}
   * @public
   */
  this.$custom = this.$chatInput.find('.chat-input-custom');

  this.inputOptions = new Array();

  /**
   * A CUI.ThreadNavBar object.
   * @type {A CUI.ThreadNavBar}
   * @public
   */
  this.threadNavBar = new CUI.ThreadNavBar();

  /**
   * A jQuery object containing the DOM element of the chat controls container.
   * @type {jQuery}
   * @public
   */
  this.$chatControlsContainer = this.$inner.find(selectors.chatControlsContainerSelector);

  /**
   * An array of jQuery objects of all chat input elements except for next thread button.
   * @type {Array<jQuery>}
   * @private
   */
  this._mainControls = [
    this.$chatControlsContainer
  ];

  /**
   * Main controls visibility indicator
   * @private
   */
  this._mainControlsVisible = true;

  /**
   * A reference to To Next Breaktpoint button
   * @type {CUI.ChatToNextBreakpointButtonPresenter}
   * @public
   */
  this.toNextBreakpointButton = null;

  return this;
}


/**
 * Hide all input elements.
 * @public
 */
CUI.ChatInputContinerPresenter.prototype.hideAllInuptElements = function() {
  this.$text.hide();
  this.$options.hide();
  this.$custom.hide();
};

/**
 * Destroy all custom input and input options elements.
 * @public
 */
CUI.ChatInputContinerPresenter.prototype.destroyDynamicContent = function() {
  if(this.inputOptions.length) {
    $.each(this.inputOptions, function(i, inputOption){
      inputOption.destroy();
    });
  }

  this.inputOptions.length = 0;

  this.$custom.empty();
}

/**
 * Create chat input option.
 * @protected
 * @param {Object} data       - input option data.
 * @param {Object} data.value - input option value.
 * @param {Object} data.text  - input option text.
 *
 * @returns {CUI.InputOptionPresenter}
 */
CUI.ChatInputContinerPresenter.prototype.createInputOption = function(data, $container) {
  // Create a new input option
  var inputOption = new CUI.InputOptionPresenter(new CUI.InputOptionModel(data));
  this.inputOptions.push(inputOption);

  if (!$container) {
    $container = this.$options;
  }

  $container.append(inputOption.$el);

  return inputOption;
};

/**
 * Chain Show animation for all given elements
 * @protected
 * @param {Array<JQuery>} elements - an array of elements to apply animation to.
 * @param elements.$element        - jQuery object reference.
 */
CUI.ChatInputContinerPresenter.prototype._showAnimationFor = function(elements) {
  elements.forEach(function($element) {
    $element.show();
  });
};

/**
 * Chain Hide animation for all given elements
 * @protected
 * @param {Array<jQuery>} elements - an array of elements to apply animation to.
 * @param elements.$element        - jQuery object reference.
 */
CUI.ChatInputContinerPresenter.prototype._hideAnimationFor = function(elements) {
  elements.forEach(function($element) {
    $element.hide();
  });

};

/**
 * Show main control elements.
 * @protected
 */
CUI.ChatInputContinerPresenter.prototype._showMainControls = function() {
  if (this._mainControlsVisible) return;

  this._showAnimationFor(this._mainControls);

  this._mainControlsVisible = true;
};

/**
 * Hide main control elements.
 * @protected
 */
CUI.ChatInputContinerPresenter.prototype._hideMainControls = function() {
  if (!this._mainControlsVisible) return;

  this._hideAnimationFor(this._mainControls);

  this._mainControlsVisible = false;
};

/**
 * Create or update the "To Next Breakpoint" button
 * @public
 * @param {Object} info - object containing info about the button.
 * @param {number} info.threadId - an id of thread the button reference to.
 * @param {string} info.html - the text the button should display.
 * @returns {CUI.ChatToNextBreakpointButtonPresenter} - reference to
 */
CUI.ChatInputContinerPresenter.prototype.placeNextThreadButton = function(info, onClickCallback) {
  var model = new CUI.ChatToNextBreakpointButtonModel(info);

  if (this.toNextBreakpointButton) {
    this.toNextBreakpointButton.update(model);
  } else {
    this.toNextBreakpointButton = new CUI.ChatToNextBreakpointButtonPresenter(model);
  }

  if (onClickCallback) {
    this.toNextBreakpointButton.removeOnClick();
    this.toNextBreakpointButton.setOnClick(onClickCallback);
  }

  this._hideMainControls();

  this.$inner.prepend(this.toNextBreakpointButton.$el);
  this._showAnimationFor([this.toNextBreakpointButton.$el]);
};

/**
 * Remove "To Next Breakpoint" button
 * @public
 */
CUI.ChatInputContinerPresenter.prototype.removeNextThreadButton = function() {
  this._showMainControls();

  if (this.toNextBreakpointButton) {
    this.toNextBreakpointButton.destroy();
    this.toNextBreakpointButton = null;
  }
};

/**
 * Set callback to show subsequent threads (proxy).
 * @public
 */
CUI.ChatInputContinerPresenter.prototype.setShowSubsequentThreadsCallback = function(callback) {
  this.threadNavBar.setShowSubsequentThreadsCallback(callback);
};

/**
 * Set callback to scroll to question and hide subsequent threads (proxy).
 * @public
 */
CUI.ChatInputContinerPresenter.prototype.setScrollToQuestionWithUpdatesCallback = function(callback) {
  this.threadNavBar.setScrollToQuestionWithUpdatesCallback(callback);
};

/**
 * Set callback to scroll to current question (proxy).
 * @public
 */
CUI.ChatInputContinerPresenter.prototype.setScrollToQuestionCallback = function(callback) {
  this.threadNavBar.setScrollToQuestionCallback(callback);
};