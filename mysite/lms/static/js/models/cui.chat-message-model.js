/**
 * @file Defines the class CUI.ChatMessageModel
 */

var CUI = CUI || {};
CUI.models = CUI.models || {};

/**
 * Model for a message.
 * @class
 * @param {Object} data               - The data used to generate the message.
 * @param {number} data.id            - A unqiue ID for the message.
 * @param {string} data.html          - The message html that is displayed within the message body.
 * @param {string} data.name          - The name of the person who wrote the message.
 * @param {string} data.userMessage   - Is true if the current user has created the message.
 * @param {string} [data.avatar]      - A url to an avatar displayed next to the message.
 * @param {Array} [data.overflow]     - An optional array of overflow options.
 * @returns {CUI.ChatMessageModel}
 */
CUI.ChatMessageModel = function(data){
  // Check that data has all required properties
  if(typeof data.id !== 'number') throw new Error('CUI.ChatMessageModel(): Invalid data.id.');
  if(!data.type) throw new Error('CUI.ChatMessageModel(): No data.type.');
  if(!data.html) throw new Error('CUI.ChatMessageModel(): No data.html.');
  if(!data.name) throw new Error('CUI.ChatMessageModel(): No data.name.');
  if(typeof data.userMessage !== 'boolean') throw new Error('CUI.ChatMessageModel(): No data.userMessage.');

  /**
   * A unqiue ID for the message.
   * @type {number}
   * @public
   */
  this.id = data.id;

  /**
   * The message html that is displayed within the message body.
   * @type {string}
   * @public
   */
  this.html = data.html;

  /**
   * The name of the person who wrote the message.
   * @type {string}
   * @public
   */
  this.name = data.name;

  /**
   * Is true if the current user has created the message.
   * @type {boolean}
   * @public
   */
  this.userMessage = data.userMessage;

  /**
   * A url to an avatar displayed next to the message.
   * @type {string}
   * @public
   */
  this.avatar = data.avatar || this._getDefaultAvatar();

  /**
   * An optional array of overflow options.
   * @type {Array}
   * @public
   */
  this.overflow = data.overflow || null;

  return this;
};

/**
 * Returns a default avatar url from {@link CUI.config}.
 * @protected
 * @returns {string}
 */
CUI.ChatMessageModel.prototype._getDefaultAvatar = function(){
  if(this.userMessage) return CUI.config.defaultStudentAvatar;
  else return CUI.config.defaultTeacherAvatar;
};
