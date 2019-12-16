/**
 * @file Defines the class CUI.SidebarBreakpointPresenter
 */

var CUI = CUI || {};

/**
 * Represents a breakpoint in the sidebar.
 * @class
 * @param {CUI.SidebarResourceModel} model      - The model to present.
 * @returns {CUI.SidebarBreakpointPresenter}
 */
CUI.SidebarResourcePresenter = function(model){
  /**
   * The HTML for the breakpoint.
   * @type {String}
   * @public
   */
   this.el = null;

  /**
   * A jQuery object containing the DOM element for the breakpoint.
   * @type {jQuery}
   * @public
   */
  this.$el = null;

  /**
   * A reference to the model used to generate the breakpoint.
   * @type {CUI.SidebarResourceModel}
   * @protected
   */
  this._model = model;

  // Render element
  this._render();

  return this;
};

/**
 * Renders the html for the breakpoint using a Handlebars templates.
 * @protected
 */
CUI.SidebarResourcePresenter.prototype._render = function(){
  this.el = CUI.views.sidebarResources(this._model);
  this.$el = $(this.el);
};

/**
 * Returns an object with id, ul, thread id & html values.
 * @public
 * @returns {Object} - {id: 100, ul: 1, threadId: 1, html: 'example'}
 */
CUI.SidebarResourcePresenter.prototype.getInfo = function() {
  return {
    id: this._model.id,
    ul: this._model.ul,
    threadId: this._model.threadId,
    html: this._model.html
  };
};

/**
 * Destroys the breakpoint.
 * @public
 */
CUI.SidebarResourcePresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  if(this.$el) this.$el.remove();

  this.el = null;
  this.$el = null;
  this._model = null;
};
