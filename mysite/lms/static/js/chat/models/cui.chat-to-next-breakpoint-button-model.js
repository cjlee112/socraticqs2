/**
 * @file Defines the class CUI.ChatToNextBreakpointButtonModel
 */

var CUI = CUI || {};
CUI.models = CUI.models || {};

/**
 * Model for a to next thread butotn.
 * @class
 * @param {Object} data               - The data used to generate the breakpoint.
 * @param {number} data.threadId      - A unqiue breakpoint thread ID.
 * @param {string} data.type          - A type of breakpoint.
 * @param {string} data.html          - The  html that is displayed within the breakpoint.
 * @returns {CUI.ChatBackToBreakpointButtonModel}
 */
CUI.ChatToNextBreakpointButtonModel = function(data){
  // Check that data has all required properties
  if(typeof data.threadId !== 'number') throw new Error('CUI.ChatToNextBreakpointButtonModel(): Invalid data.threadId.');
  if(!data.type) throw new Error('CUI.ChatToNextBreakpointButtonModel(): Invalid data.type.');
  if(!data.html) throw new Error('CUI.ChatToNextBreakpointButtonModel(): No data.html.');

  /**
   * A unqiue breakpoint thread ID.
   * @type {number}
   * @public
   */
  this.threadId = data.threadId;

  /**
   * The string indicating a type of breakpoint.
   * @type {string}
   * @public
   */
  this.type = data.type;

  /**
   * The html that is displayed within a button.
   * @type {string}
   * @public
   */
  this.html = data.html;

  return this;
};
