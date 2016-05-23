/**
 * @file Defines the class CUI.SidebarBreakpointModel
 */

var CUI = CUI || {};
CUI.models = CUI.models || {};

/**
 * Model for a sidebar breakpoint.
 * @class
 * @param {Object} data               - The data used to generate the breakpoint.
 * @param {number} data.id            - The id of the message this breakpoint links to in the chat.
 * @param {string} data.html          - The html that is displayed within the breakpoint.
 * @param {boolean} data.isUnlocked   - If the user currently has access to this breakpint.
 * @param {boolean} data.isDone       - If this breakpoint should be marked as complete.
 * @returns {CUI.SidebarBreakpointModel}
 */
CUI.SidebarBreakpointModel = function(data){
  // Check that data has all required properties
  if(typeof data.id !== 'number') throw new Error('CUI.SidebarBreakpointModel(): Invalid data.id.');
  if(!data.html) throw new Error('CUI.SidebarBreakpointModel(): No data.html.');
  if(typeof data.isUnlocked !== 'boolean') throw new Error('CUI.SidebarBreakpointModel(): Invalid data.isUnlocked.');
  if(typeof data.isDone !== 'boolean') throw new Error('CUI.SidebarBreakpointModel(): Invalid data.isDone.');

  /**
   * The id of the message this breakpoint links to in the chat.
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

  /**
   * If the user currently has access to this breakpint.
   * @type {string}
   * @public
   */
  this.isUnlocked = data.isUnlocked;

  /**
   * If this breakpoint should be marked as complete.
   * @type {string}
   * @public
   */
  this.isDone = data.isDone;

  return this;
};
