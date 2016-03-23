/**
 * @file Defines the class CUI.ChatBreakpointPresenter
 */

var CUI = CUI || {};

/**
 * Represents a breakpoint in {@link CUI.ChatPresenter}.
 * @class
 * @param {CUI.ChatBreakpointModel} model      - The model to present.
 * @returns {CUI.ChatBreakpointPresenter}
 */
CUI.ChatBreakpointPresenter = function(model){
  /**
   * The HTML for the breakpoint.
   * @type {String}
   * @public
   */
   this.el= null;

  /**
   * A jQuery object containing the DOM element for the breakpoint.
   * @type {jQuery}
   * @public
   */
  this.$el = null;

  /**
   * A reference to the model used to generate the breakpoint.
   * @type {CUI.ChatBreakpointModel}
   * @protected
   */
  this._model = model;

  // Render element
  this._render();

  return this;
};

/**
 * Updates the breakpoint.
 * @public
 * @param {CUI.ChatBreakpointModel} model      - The model to present.
 * @returns {CUI.ChatBreakpointPresenter}
 */
CUI.ChatBreakpointPresenter.prototype.update = function(model){
  // Replace existing model with new model
  this._model = model;

  // Save reference to the old message
  var $oldMessage = this.$el;

  // Render the new message
  this._render();

  // Insert new message after old message
  $oldMessage.after(this.$el);

  // Delete and clean up after old message
  $oldMessage.remove();

  return this;
};

/**
 * Renders the html for the breakpoint using a Handlebars templates.
 * @protected
 */
CUI.ChatBreakpointPresenter.prototype._render = function(){
  this.el = CUI.views.chatBreakpoint(this._model);
  this.$el = $(this.el);
};

/**
 * Destroys the breakpoint.
 * @public
 */
CUI.ChatBreakpointPresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  this.$el.remove();

  this.el = null;
  this.$el = null;
  this._model = null;
};
