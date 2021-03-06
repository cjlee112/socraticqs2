/**
 * @file Defines the class CUI.SidebarBreakpointPresenter
 */

var CUI = CUI || {};

/**
 * Represents a breakpoint in the sidebar.
 * @class
 * @param {CUI.SidebarBreakpointModel} model      - The model to present.
 * @returns {CUI.SidebarBreakpointPresenter}
 */
CUI.SidebarBreakpointPresenter = function(model){
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
   * @type {CUI.SidebarBreakpointModel}
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
CUI.SidebarBreakpointPresenter.prototype._render = function(){
  this.el = CUI.views.sidebarBreakpoint(this._model);
  this.$el = $(this.el);
};


/**
 * Returns an object with thread id & html values.
 * @public
 * @returns {Object} - {threadId: 1, html: 'example'}
 */
CUI.SidebarBreakpointPresenter.prototype.getInfo = function() {
  return {
    threadId: this._model.threadId,
    html: this._model.html,
    isDone: this._model.isDone,
    updatesCount: this._model.updatesCount
  };
};

/**
 * Destroys the breakpoint.
 * @public
 */
CUI.SidebarBreakpointPresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  if(this.$el) this.$el.remove();

  this.el = null;
  this.$el = null;
  this._model = null;
};
