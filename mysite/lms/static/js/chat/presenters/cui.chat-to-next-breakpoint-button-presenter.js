/**
 * @file Defines the class CUI.ChatToNextBreakpointButtonPresenter
 */

var CUI = CUI || {};

/**
 * Represents a to next breakpoint button in {@link CUI.ChatPresenter}.
 * @class
 * @param {CUI.ChatToNextBreakpointButtonModel} model      - The model to present.
 * @returns {CUI.ChatToNextBreakpointButtonPresenter}
 */
CUI.ChatToNextBreakpointButtonPresenter = function(model){
  /**
   * The HTML for the button.
   * @type {String}
   * @public
   */
   this.el = null;

  /**
   * CSS Selector for the button.
   * @type {string}
   * @public
   */
  this.buttonSelector = '.chat-next-thread';

  /**
   * A jQuery object containing the DOM element for the button.
   * @type {jQuery}
   * @public
   */
  this.$button = null;

  /**
   * A reference to the model used to generate the button.
   * @type {CUI.ChatBackToBreakpointButtonModel}
   * @protected
   */
  this._model = model;

  // Render element
  this._render();

  return this;
};

/**
 * Updates button text and threadId.
 * @public
 * @param {CUI.ChatToNextBreakpointButtonModel} model      - The model to present.
 * @returns {CUI.ChatToNextBreakpointButtonPresenter}
 */
CUI.ChatToNextBreakpointButtonPresenter.prototype.update = function(model){
    // Replace existing model with new model
    this._model = model;

    // Save reference to the current button container
    var $currentButtonContainer = this.$el;

    // Render the new button
    this._render();

    // Insert new button after current button container
    $currentButtonContainer.after(this.$el);

    // Delete and clean up after current button container
    $currentButtonContainer.remove();

    return this;
  };

/**
 * Renders the html for the breakpoint using a Handlebars templates.
 * @protected
 */
CUI.ChatToNextBreakpointButtonPresenter.prototype._render = function(){
  this.el = CUI.views.chatToNextBreakpointButton(this._model);
  this.$el = $(this.el);
  this.$button = this.$el.find(this.buttonSelector);
};

/**
 * Set the onClick callback handler to the one provided.
 * @public
 * @param {function} callback - callback to handle the onClick eecnt.
 */
CUI.ChatToNextBreakpointButtonPresenter.prototype.setOnClick = function(callback){
  this.$button.on('click', callback);
};

/**
 * Remove all onClick callback handlers.
 * @public
 */
CUI.ChatToNextBreakpointButtonPresenter.prototype.removeOnClick = function(){
  this.$button.off('click', '**');
};

/**
 * Destroys the breakpoint.
 * @public
 */
CUI.ChatToNextBreakpointButtonPresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  this.$el.remove();

  this.el = null;
  this.$el = null;
  this.$button = null;
  this._model = null;
};
