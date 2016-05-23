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
