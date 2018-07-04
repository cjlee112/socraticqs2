/**
 * @file Defines the class CUI.InputOptionPresenter
 */

var CUI = CUI || {};

/**
 * Represents an input option in {@link CUI.ChatPresenter}.
 * @class
 * @param {CUI.InputOptionModel} model      - The model to present.
 * @returns {CUI.InputOptionPresenter}
 */
CUI.InputOptionPresenter = function(model){
  /**
   * The HTML for the input option.
   * @type {String}
   * @public
   */
   this.el = null;

  /**
   * A jQuery object containing the DOM element for the input option.
   * @type {jQuery}
   * @public
   */
  this.$el = null;

  /**
   * A reference to the model used to generate the input option.
   * @type {CUI.InputOptionModel}
   * @protected
   */
  this._model = model;

  // Render element
  this._render();

  return this;
};

/**
 * Renders the html for the input option using a Handlebars templates.
 * @protected
 */
CUI.InputOptionPresenter.prototype._render = function(){
  this.el = CUI.views.inputOption(this._model);
  this.$el = $(this.el);
};

/**
 * Destroys the input option.
 * @public
 */
CUI.InputOptionPresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  this.$el.remove();

  this.el = null;
  this.$el = null;
  this._model = null;
};
