/**
 * @file Defines the class CUI.ChatBackToBreakpointButtonModel
 */

var CUI = CUI || {};
CUI.models = CUI.models || {};

/**
 * Model for a back to breakpoint button.
 * @class
 * @param {Object} data               - The data used to generate the breakpoint.
 * @param {number} data.threadId      - A unqiue breakpoint thread ID.
 * @param {string} data.html          - The  html that is displayed within the breakpoint.
 * @returns {CUI.ChatBackToBreakpointButtonModel}
 */
CUI.ChatBackToBreakpointButtonModel = function(data){
  // Check that data has all required properties
  if(typeof data.threadId !== 'number') throw new Error('CUI.ChatBackToBreakpointButtonModel(): Invalid data.threadId.');
  if(!data.html) throw new Error('CUI.ChatBackToBreakpointButtonModel(): No data.html.');
  if(!data.type) data.type = CUI.ChatBackToBreakpointButtonModel.ItemType.none;

  /**
   * A unqiue breakpoint thread ID.
   * @type {number}
   * @public
   */
  this.threadId = data.threadId;

  /**
   * The html that is displayed within a button.
   * @type {string}
   * @public
   */
  this.html = data.html;

    /**
   * The type of the item it refers to.
   * @type {string} - one of {ChatBackToBreakpointButtonModel.ItemType}
   * @public
   */
  this.type = data.type;

  return this;
};

CUI.ChatBackToBreakpointButtonModel.ItemType = {
  none: 'none',
  breakpoint: 'breakpoint',
  resource: 'resource'
};
