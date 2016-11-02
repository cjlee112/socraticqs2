/**
 * @file Defines the class CUI.ChatMessagePresenter
 */

var CUI = CUI || {};

/**
 * Represents a message in {@link CUI.ChatPresenter}.
 * @class
 * @param {CUI.ChatMessageModel} model      - The model to present.
 * @returns {CUI.ChatMessagePresenter}
 */
CUI.ChatMessagePresenter = function(model){
  /**
   * The HTML for the message.
   * @type {String}
   * @public
   */
   this.el = null;

  /**
   * A jQuery object containing the DOM element for this message.
   * @type {jQuery}
   * @public
   */
  this.$el = null;

  /**
   * A reference to the model used to generate the message.
   * @type {CUI.ChatMessageModel}
   * @protected
   */
  this._model = model;

  // Render element
  this._render();

  // Add event listeners
  this._addEventListeners();

  return this;
};

/**
 * Updates the message.
 * @public
 * @param {CUI.ChatMessageModel} model      - The model to present.
 * @returns {CUI.ChatMessagePresenter}
 */
CUI.ChatMessagePresenter.prototype.update = function(model){
  // Replace existing model with new model
  this._model = model;

  // Save reference to the old message
  var $oldMessage = this.$el;

  // Render the new message
  this._render();

  // Insert new message after old message
  $oldMessage.after(this.$el);

  // Delete and clean up after old message
  $oldMessage.remove();

  // Add event listeners for new message
  this._addEventListeners();

  return this;
};

/**
 * Renders the html for the message using a Handlebars templates.
 * @protected
 */
CUI.ChatMessagePresenter.prototype._render = function(){
  this.el = CUI.views.chatMessage(this._model);
  this.$el = $(this.el);
};

/**
 * Attaches event listeners to elements in the message.
 * @protected
 */
CUI.ChatMessagePresenter.prototype._addEventListeners = function(){
  // Add more/less toggles
  this.$el.find('.chat-more-less').moreLess();

  // Add listeners for selectables
  this.$el.find('.chat-selectable').on('click', function(e){
    // Add selected class if not radio button or checkbox
    if(!$(this).is(':checkbox') && !$(this).is(':radio')) {
      e.preventDefault();
      $(this).toggleClass('chat-selectable-selected');
    }
  });

  // Overflow actions toggle
  this.$el.find('.chat-actions-toggle').on('click', function(e){
    e.preventDefault();

    $(this).parent().find('ul').stop().fadeToggle();
  });
};

/**
 * Destroys the message.
 * @public
 */
CUI.ChatMessagePresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  this.$el.remove();

  this.el = null;
  this.$el = null;
  this._model = null;
};
