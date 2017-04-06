/**
 * @file Defines the class CUI.ChatBreakpointModel
 */

var CUI = CUI || {};
CUI.models = CUI.models || {};

/**
 * Model for a breakpoint.
 * @class
 * @param {Object} data               - The data used to generate the breakpoint.
 * @param {number} data.id            - A unqiue ID for the breakpoint.
 * @param {string} data.html          - The  html that is displayed within the breakpoint.
 * @returns {CUI.ChatBreakpointModel}
 */
CUI.ChatBreakpointModel = function(data){
  // Check that data has all required properties
  if(typeof data.id !== 'number') throw new Error('CUI.ChatBreakpointModel(): Invalid data.id.');
  if(!data.html) throw new Error('CUI.ChatBreakpointModel(): No data.html.');

  /**
   * A unqiue ID for the breakpoint.
   * @type {number}
   * @public
   */
  this.id = data.id;

  /**
   * The html that is displayed within the breakpoint.
   * @type {string}
   * @public
   */
  this.html = data.html;

  return this;
};
