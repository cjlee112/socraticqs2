/**
 * @file Defines the class CUI.SidebarResourceModel
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
 * @param {boolean} data.isStarted    - If the user currently has started this breakpint.
 * @param {boolean} data.isDone       - If this breakpoint should be marked as complete.
 * @returns {CUI.SidebarResourceModel}
 */
CUI.SidebarResourceModel = function(data){
  // Check that data has all required properties
  // if(typeof data.id !== 'number') throw new Error('CUI.SidebarResourceModel(): Invalid data.id.');
  if(!data.html) throw new Error('CUI.SidebarResourceModel(): No data.html.');
  if(typeof data.isStarted !== 'boolean') throw new Error('CUI.SidebarResourceModel(): Invalid data.isStarted.');
  if(typeof data.isUnlocked !== 'boolean') throw new Error('CUI.SidebarResourceModel(): Invalid data.isUnlocked.');
  if(typeof data.isDone !== 'boolean') throw new Error('CUI.SidebarResourceModel(): Invalid data.isDone.');

  /**
   * The id of the message this breakpoint links to in the chat.
   * @type {number}
   * @public
   */
  this.id = data.id;

    /**
   * The id of the message this breakpoint links to in the chat.
   * @type {number}
   * @public
   */
  this.ul = data.ul;

  /**
   * The html that is displayed within the breakpoint.
   * @type {string}
   * @public
   */
  this.html = data.html;

  /**
   * If user has access to resources
   * @type {string}
   * @public
   */
  this.isUnlocked = data.isUnlocked;

  /**
   * If the user currently has started this resource
   * @type {string}
   * @public
   */
  this.isStarted = data.isStarted;

  /**
   * If this breakpoint should be marked as complete.
   * @type {string}
   * @public
   */
  this.isDone = data.isDone;

  return this;
};
