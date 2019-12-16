/**
 * @file Defines the class CUI.ChatBackToBreakpointButtonPresenter
 */

var CUI = CUI || {};

/**
 * Represents a back to breakpoint button in {@link CUI.ChatPresenter}.
 * @class
 * @param {CUI.ChatBackToBreakpointButtonModel} model      - The model to present.
 * @returns {CUI.ChatBackToBreakpointButtonPresenter}
 */
CUI.ChatBackToBreakpointButtonPresenter = function(model){
  /**
   * The HTML for the button.
   * @type {String}
   * @public
   */
   this.el= null;

  /**
   * A jQuery object containing the DOM element for the button.
   * @type {jQuery}
   * @public
   */
  this.$el = null;

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
 * @param {CUI.ChatBackToBreakpointButtonModel} model      - The model to present.
 * @returns {CUI.ChatMessagePresenter}
 */
CUI.ChatBackToBreakpointButtonPresenter.prototype.update = function(model){
    // Replace existing model with new model
    this._model = model;

    // Save reference to the current button
    var $currentButton = this.$el;

    // Render the new button
    this._render();

    // Insert new button after current button
    $currentButton.after(this.$el);

    // Delete and clean up after current button
    $currentButton.remove();

    return this;
  };

/**
 * Renders the html for the breakpoint using a Handlebars templates.
 * @protected
 */
CUI.ChatBackToBreakpointButtonPresenter.prototype._render = function(){
  this.el = CUI.views.chatBackToBreakpointButton(this._model);
  this.$el = $(this.el);
};

/**
 * Destroys the breakpoint.
 * @public
 */
CUI.ChatBackToBreakpointButtonPresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  this.$el.remove();

  this.el = null;
  this.$el = null;
  this._model = null;
};
