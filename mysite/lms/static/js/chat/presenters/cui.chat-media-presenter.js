/**
 * @file Defines the class CUI.ChatMediaPresenter
 */

var CUI = CUI || {};

/**
 * Represents a media message in {@link CUI.ChatPresenter}.
 * @class
 * @param {CUI.ChatMediaModel} model      - The model to present.
 * @returns {CUI.ChatMediaPresenter}
 */
CUI.ChatMediaPresenter = function(model){
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
   * @type {CUI.ChatMediaModel}
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
 * @param {CUI.ChatMediaModel} model      - The model to present.
 * @returns {CUI.ChatMediaPresenter}
 */
CUI.ChatMediaPresenter.prototype.update = function(model){
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
CUI.ChatMediaPresenter.prototype._render = function(){
  this.el = CUI.views.chatMedia(this._model);
  this.$el = $(this.el);

  // Calculate max-width for caption
  this._renderCaption();
};

/**
 * Attaches event listeners to elements in the message.
 * @protected
 */
CUI.ChatMediaPresenter.prototype._addEventListeners = function(){
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

  // Re-render caption only when any embedded image has loaded
  var $img = this.$el.find('.chat-bubble img');

  if($img.length > 0){
    $($img).one('load', $.proxy(function() {
      this._renderCaption();
    }, this)).each($.proxy(function() {
      if(this.complete) this._renderCaption();
    }, this));
  }
};

/**
 * Sets max-width for caption based on image width. Ignored for other media types as they generally have an initial width set.
 * @protected
 */
CUI.ChatMediaPresenter.prototype._renderCaption = function(){
  var $caption = this.$el.find('.caption');
  var $mediaElement = this.$el.find('.chat-bubble > *:first-child');
  var width = $mediaElement.width();

  if($caption.length > 0 && width > 0){
    $caption.css('max-width', width);
  }
};

/**
 * Destroys the message.
 * @public
 */
CUI.ChatMediaPresenter.prototype.destroy = function(){
  // Use jQuery.remove() to remove element from DOM and unbind event listeners
  this.$el.remove();

  this.el = null;
  this.$el = null;
  this._model = null;
};
