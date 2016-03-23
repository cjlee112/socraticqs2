/**
 * @file Defines the class CUI.ChatPresenter
 */

var CUI = CUI || {};

/**
 * Represents the chat UI and binds listeners to pre-existing DOM elements.
 * @class
 * @param {number} chatID           - A unique ID for the chat.
 * @param {string} historyUrl       - A url for loading a user's history.
 * @param {string} progressUrl      - A url for loading a user's progress.
 * @returns {CUI.ChatPresenter}
 */
CUI.ChatPresenter = function(chatID, historyUrl, progressUrl){
  // Check arguments
  if(typeof chatID !== 'number') throw new Error('CUI.ChatPresenter(): Invalid chatID.');
  if(!historyUrl) throw new Error('CUI.ChatPresenter(): No historyUrl.');
  if(!progressUrl) throw new Error('CUI.ChatPresenter(): No progressUrl.');

  /**
   * The chat's unique ID.
   * @type {number}
   * @protected
   */
  this._chatID = chatID;

  /**
   * An object with references to all messages, media, and breakpoints currently in the chat.
   * @type {Object.<number, CUI.ChatMessagePresenter|CUI.ChatMediaPresenter|CUI.ChatBreakpointPresenter>}
   * @protected
   */
  this._messages = {};

  /**
   * An array with references to all breakpoints currently in the sidebar.
   * @type {Array.<CUI.SidebarBreakpointPresenter>}
   * @protected
   */
  this._sidebarBreakpoints = {};

  /**
   * The url for loading a user's chat history.
   * @type {string}
   * @protected
   */
  this._historyUrl = historyUrl;

  /**
   * The url for loading a user's chat progress.
   * @type {string}
   * @protected
   */
  this._progressUrl = progressUrl;

  /**
   * The currently active input type in the chat. 'text', 'options', or 'custom'.
   * @type {string}
   * @protected
   */
  this._inputType = null;

  /**
   * The url for loading the next set of messages and input type.
   * @type {string}
   * @protected
   */
  this._inputUrl = null;

  /**
   * If input is enabled in the chat.
   * @type {boolean}
   * @protected
   */
  this._inputIsEnabled = false;

  /**
   * An array of existing input options.
   * @type {Array.<InputOptionPresenter>}
   * @protected
   */
  this._inputOptions = [];

  /**
   * The current set of message IDs that are searched for values when submitting input.
   * @type {Array.<number>}
   * @protected
   */
  this._includeSelectedValuesFromMessages = [];

  /**
   * True if the sidebar is visible.
   * @type {boolean}
   * @protected
   */
  this._isSidebarVisible = false;

  /**
   * A jQuery reference to the sidebar element.
   * @type {jQuery}
   * @protected
   */
  this._$sidebar = $('.chat-sidebar');

  /**
   * A jQuery reference to the container element for sidebar breakpoints.
   * @type {jQuery}
   * @protected
   */
  this._$sidebarBreakpointsContainer = $('.chat-sidebar-breakpoints');

  /**
   * A jQuery reference to the container element for messages.
   * @type {jQuery}
   * @protected
   */
  this._$messagesContainer = $('.chat-messages');

  /**
   * A jQuery reference to the input bar.
   * @type {jQuery}
   * @protected
   */
  this._$inputBar = $('.chat-input-bar');

  /**
   * A jQuery reference to the container element for the various input types.
   * @type {jQuery}
   * @protected
   */
  this._$inputContainer = $('.chat-input');

  /**
   * A jQuery reference to the progress element.
   * @type {jQuery}
   * @protected
   */
  this._$progress = $('.chat-progress');

  /**
   * A jQuery reference to the sidebar toggle element.
   * @type {jQuery}
   * @protected
   */
  this._$sidebarToggle = $('.sidebar-toggle');

  /**
   * A jQuery reference to the fullscreen toggle element.
   * @type {jQuery}
   * @protected
   */
  this._$fullscreenToggle = $('.fullscreen-toggle');

  /**
   * A jQuery reference to the spinner element.
   * @type {jQuery}
   * @protected
   */
  this._$loading = $('.chat-loading');

  // Add event listeners
  this._addEventListeners();

  // Update fullscreen icon if fullscreen is active
  if(screenfull.isFullscreen) this._$fullscreenToggle.addClass('active');

  // Show chat
  this._showChat();

  return this;
};

/**
 * Loads a user's chat history and sends the response to {@link CUI.ChatPresenter#_parseHistory}.
 * @protected
 */
CUI.ChatPresenter.prototype._getHistory = function(){
  // Show spinner
  this._showLoading();

  // Get history json
  $.ajax({
    url: this._historyUrl,
    method: 'GET',
    dataType: 'json',
    cache: false,
    context: this
  }).done(this._parseHistory).fail(function(){ throw new Error("CUI.ChatPresenter._getHistory(): Failed to load history."); });
};

/**
 * Loads a user's progress and sends the response to {@link CUI.ChatPresenter#_parseProgress}.
 * @protected
 */
CUI.ChatPresenter.prototype._getProgress = function(){
  // Get progress
  $.ajax({
    url: this._progressUrl,
    method: 'GET',
    dataType: 'json',
    cache: false,
    context: this
  }).done(this._parseProgress).fail(function(){
    throw new Error('CUI.ChatPresenter._getProgress(): Could not load progress.');
  });
};

/**
 * Loads a user's next set of messages and input type.
 * @protected
 * @param {string} url     - A url for loading a user's next set of messages and input type.
 */
CUI.ChatPresenter.prototype._getMessages = function(url){
  // Get messages and input
  $.ajax({
    url: url,
    method: 'GET',
    dataType: 'json',
    cache: false,
    context: this
  }).done(function(data){
    // Update the current input type in the chat
    if(data.input) this._setInput(data.input);
    else throw new Error("CUI.ChatPresenter._getMessages(): No data.input.");

    // Update chat with new messages
    if(data.addMessages) this._parseMessages(data, true);
    else throw new Error("CUI.ChatPresenter._getMessages(): No data.addMessages.");

    // Hide spinner
    this._hideLoading();
  }).fail(function(){ throw new Error("CUI.ChatPresenter._getMessages(): Failed to load messages."); });
};

/**
 * Sends the user's input to the server.
 * @protected
 * @param {object} input     - An object containing the user's input.
 */
CUI.ChatPresenter.prototype._postInput = function(input){
  // Check that input is enabled
  if(!this._inputIsEnabled) return;

  // Disable input while validating and sending input
  this._inputIsEnabled = false;

  // Add selected elements to input
  input.selected = this._findSelectedValues();

  // Show loading
  this._showLoading();

  // Post input to server
  $.ajax({
    url: this._inputUrl,
    method: 'PUT',
    dataType: 'json',
    data: input,
    cache: false,
    context: this
  }).done(function(response){
    // Check that nextMessagesUrl is in response
    if(response && response.nextMessagesUrl){
        // Load next set of messages
        this._getMessages(response.nextMessagesUrl);

        // Update progress
        this._getProgress();
    }else if(response.error){
      // Enable input
      this._inputIsEnabled = true;

      // Hide spinner
      this._hideLoading();

      // Show message to try again
      this._showNotification(response.error);
    }else{
      throw new Error('CUI.ChatPresenter._postInput(): No response.nextMessagesUrl or response.error');
    }
  }).fail(function(){
    // Enable input
    this._inputIsEnabled = true;

    // Hide spinner
    this._hideLoading();

    // Show message to try again
    this._showNotification(CUI.text.errorTryAgain);
  });
};

/**
 * Passes text input onto to {@link ChatPresenter#_postInput}.
 * @protected
 */
CUI.ChatPresenter.prototype._postText = function(){
  // Create input object
  var input = {};

  // Find text
  var text = this._$inputContainer.find('.chat-input-text').find('textarea').val();

  // Add text to input object if set
  input.text = text;

  this._postInput(input);
};

/**
 * Pass option input onto to {@link ChatPresenter#_postInput}.
 * @protected
 * @param {string} optionValue     - The selected option's value.
 */
CUI.ChatPresenter.prototype._postOption = function(optionValue){
  // Create input object
  var input = {option: optionValue};

  // Send input to server
  this._postInput(input);
};

/**
 * Sends a user's action to the server.
 * @protected
 * @param {string} actionUrl     - Where to fetch the next set of messages and input type.
 */
CUI.ChatPresenter.prototype._postAction = function(actionUrl){
  // Check that input is enabled
  if(!this._inputIsEnabled) return;

  // Disable input while validating and sending input
  this._inputIsEnabled = false;

  // Show loading
  this._showLoading();

  // Post input to server
  $.ajax({
    url: actionUrl,
    method: 'PUT',
    dataType: 'json',
    cache: false,
    context: this
  }).done(function(response){
    // Check that nextMessagesUrl is in response
    if(response && response.nextMessagesUrl){
        // Load next set of messages
        this._getMessages(response.nextMessagesUrl);

        // Update progress
        this._getProgress();
    }else{
      throw new Error('CUI.ChatPresenter._postAction(): No response.nextMessagesUrl');
    }
  }).fail(function(){
    // Enable input
    this._inputIsEnabled = true;

    // Hide spinner
    this._hideLoading();

    // Show message to try again
    this._showNotification(CUI.text.errorTryAgain);
  });
};

/**
 * Gets called when the history has loaded to initialize and show the chat.
 * @protected
 */
CUI.ChatPresenter.prototype._showChat = function(){
  // Fade out preloader
  var timeline = new TimelineMax();

  // Show chat
  this._$messagesContainer.show();
  this._$sidebar.show();
  this._$inputBar.show();
  timeline.fromTo(this._$messagesContainer, 1.2, {opacity: 0}, {opacity: 1, ease: Power1.easeInOut, force3D: 'auto', clearProps: 'transform'});
  timeline.from(this._$inputBar, 0.7, {bottom: -85, ease: Power1.easeInOut, force3D: 'auto', clearProps: 'transform'}, 0.3);

  //Scroll to chat
  var top = this._$messagesContainer.offset().top;
  TweenLite.to(window, this._getScrollSpeed(top), {scrollTo: {y: top, autoKill: false}, ease: Power2.easeInOut, onComplete: $.proxy(function(){
    // Get message history
    this._getHistory();

    // Update progress
    this._getProgress();
  }, this)});
};

/**
 * Parses progress data and updates the progress bar and the list of breakpoints in the sidebar.
 * @protected
 * @param {object} data               - An object containing the user's progress.
 * @param {number} data.progress      - The user's progress 0 - 1.
 * @param {Array} data.breakpoints    - An array of breakpoints to display in the sidebar.
 */
CUI.ChatPresenter.prototype._parseProgress = function(data){
  var newWidth;
  var breakpoint;
  var timeline;
  var $progressBar;

  // Check that data contains progress
  if(data && typeof data.progress === 'number'){
    // Calculate new progress bar width
    newWidth = this._$progress.width() * data.progress;
    newWidth = (newWidth > 10) ? newWidth : 10;

    // Animate progress bar
    $progressBar = this._$progress.find('span');
    TweenMax.fromTo($progressBar, 0.5, {scale: 1}, {scale: 1.3, repeat: 1, yoyo:true, ease: Power1.easeInOut});
    TweenMax.to($progressBar, 1, {width: newWidth}, {width: newWidth, ease: Back.easeOut}, 0);

    // Add breakpoints to the sidebar
    if(data.breakpoints instanceof Array && data.breakpoints.length > 0){
      // Remove existing breakpoints
      $.each(this._sidebarBreakpoints, $.proxy(function(i, b){
        b.destroy();
      }, this));

      // Reset breakpoints Array
      this._sidebarBreakpoints = [];

      // Add new breakpoints
      $.each(data.breakpoints, $.proxy(function(i, b){
        // Create breakpoint from template
        breakpoint = new CUI.SidebarBreakpointPresenter(new CUI.SidebarBreakpointModel(b));

        // Add reference to breakpoint
        this._sidebarBreakpoints.push(breakpoint);

        // Add breakpoint in sidebar
        this._$sidebarBreakpointsContainer.append(breakpoint.$el);
      }, this));
    }
  }else{
    throw new Error('CUI.ChatPresenter._parseProgress(): No data.progress');
  }
};

/**
 * Parses chat history data.
 * @protected
 * @param {Object} data                   - An object containing the user's history data and what input type to display.
 * @param {Object} data.input             - An object with settings for the input type.
 * @param {Array} data.addMessages        - An array with message objects that will be added to the chat.
 */
CUI.ChatPresenter.prototype._parseHistory = function(data){
  // Update the current input type in the chat
  if(data.input) this._setInput(data.input);
  else throw new Error("CUI.ChatPresenter._parseHistory(): No data.input.");

  // Update chat with new messages
  if(data.addMessages) this._parseMessages(data, false);
  else throw new Error("CUI.ChatPresenter._parseHistory(): No data.addMessages.");

  // Enable input
  this._hideLoading();
};

/**
 * Adds, updates, and removes messages in the chat.
 * @protected
 * @param {Object} data                   - An object containing messages and what input type do display.
 * @param {Array} data.addMessages        - An array with message objects that will be added to the chat.
 * @param {Array} [data.updateMessages]   - An array with message objects that will be updated in the chat.
 * @param {Array} [data.deleteMessages]   - An array of message ids for messages that will be removed from the chat.
 * @param {boolean} scrollTo              - Scrolls to first new message if true.
 */
CUI.ChatPresenter.prototype._parseMessages = function(data, scrollTo){
  var currentScrollTop = $(window).scrollTop();
  var newMessages = [];

  // Add new messages
  if(data.addMessages instanceof Array && data.addMessages.length > 0){
    $.each(data.addMessages, $.proxy(function(i, m){
      var model;

      // Create a model based on type
      if(m.type === 'message') model = new CUI.ChatMessageModel(m);
      else if(m.type === 'media') model = new CUI.ChatMediaModel(m);
      else if(m.type === 'breakpoint') model = new CUI.ChatBreakpointModel(m);
      else throw new Error("CUI.ChatPresenter._parseMessages(): Invalid m.type.");

      // Add message to chat
      newMessages.push(this._addMessage(model));
    }, this));
  }else{
    throw new Error("CUI.ChatPresenter._parseMessages(): No data.addMessages.");
  }

  // Update messages
  if(data.updateMessages instanceof Array && data.updateMessages.length > 0){
    $.each(data.updateMessages, $.proxy(function(i, m){
      var model;

      // Create a model based on type
      if(m.type === 'message') model = new CUI.ChatMessageModel(m);
      else if(m.type === 'media') model = new CUI.ChatMediaModel(m);
      else if(m.type === 'breakpoint') model = new CUI.ChatBreakpointModel(m);
      else throw new Error("CUI.ChatPresenter._parseMessages(): Invalid m.type.");

      //Update messages
      this._updateMessage(model);
    }, this));
  }

  // Delete messages
  if(data.deleteMessages instanceof Array && data.deleteMessages.length > 0){
    $.each(data.deleteMessages, $.proxy(function(i, id){
      this._removeMessage(id);
    }, this));
  }

  // Animate new messages
  TweenMax.from(newMessages, 0.7, {opacity: 0, scale: 0.9, ease: Power1.easeOut, force3D: true, clearProps: 'transform', onComplete: function(){
    // Draw equations after animation has completed
    MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
  }});

  // Scroll to first new message
  if(scrollTo) this._scrollToMessage(data.addMessages[0].id);
};

/**
 * Creates and adds a message to the chat.
 * @protected
 * @param {ChatMessageModel|ChatMediaModel|ChatBreakpointModel} model   - The model for the message.
 * @param {ChatMessageModel|ChatMediaModel|ChatBreakpointModel} model   - The model for the message.
 * @returns {jQuery}
 */
CUI.ChatPresenter.prototype._addMessage = function(model){
  var message;

  // Create a message presenter based on model type
  if(model instanceof CUI.ChatMessageModel) message = new CUI.ChatMessagePresenter(model);
  else if(model instanceof CUI.ChatMediaModel) message = new CUI.ChatMediaPresenter(model);
  else if(model instanceof CUI.ChatBreakpointModel) message = new CUI.ChatBreakpointPresenter(model);
  else throw new Error("CUI.ChatPresenter._addMessage(): Invalid model.");

  // Save a reference to the message
  this._messages[model.id] = message;

  // Add message to chat
  this._$messagesContainer.append(message.$el);

  return message.$el;
};

/**
 * Updates a message in the chat.
 * @protected
 * @param {ChatMessageModel|ChatMediaModel|ChatBreakpointModel} model   - The new model for the message.
 */
CUI.ChatPresenter.prototype._updateMessage = function(model){
  var currentMessage;

  // Select existing message
  currentMessage = this._messages[model.id];

  // Update message
  if(currentMessage) currentMessage.update(model);
  else throw new Error('CUI.ChatPresenter._updateMessage(): Message with id "'+model.id+'" does not exist.');
};

/**
 * Removes a message from the chat.
 * @protected
 * @param {number} id       - The id of the message to remove.
 */
CUI.ChatPresenter.prototype._removeMessage = function(id){
  var currentMessage;
  var breakpoint;

  // Select existing message
  currentMessage = this._messages[id];

  // Check that message exists
  if(currentMessage){
    // Destroy message and remove reference
    currentMessage.destroy();
    this._messages[id] = null;

    // Remove any sidebar breakpoints linking to this message
    breakpoint = this._sidebarBreakpoints[id];

    if(breakpoint) breakpoint.destroy();
  }else{
    // Unneseccary to throw an error here
    // throw new Error('CUI.ChatPresenter._removeMessage(): Message with id "'+id+'" does not exist.');
  }
};

/**
 * Finds selected values within messages.
 * @protected
 * @returns {object}
 */
CUI.ChatPresenter.prototype._findSelectedValues = function(){
  var selected = {};

  // Loop through messages with selectables and look for selected elements
  $.each(this._includeSelectedValuesFromMessages, $.proxy(function(i, messageID){
    var $message;
    var $selectedSelectables;

    // Check that the message exists in the DOM
    if(this._messages[messageID]) {
      $message = this._messages[messageID].$el;

      // Find selected elements in message
      $selectedSelectables = $message.find('.chat-selectable.chat-selectable-selected, .chat-selectable:checked');

      // Add selected values to selected array
      if($selectedSelectables.length){
        $.each($selectedSelectables, function(ii, s){
          var attribute = $(s).data('selectable-attribute');
          var value = $(s).data('selectable-value');

          selected[messageID] = selected[messageID] || {};
          selected[messageID][attribute] = selected[messageID][attribute] || [];
          selected[messageID][attribute].push(value);
        });
      }
    }
  }, this));

  return selected;
};

/**
 * Hides input and displays a spinner.
 * @protected
 */
CUI.ChatPresenter.prototype._showLoading = function(){
  // Hide input
  TweenMax.set(this._$inputContainer, {opacity: 0, display: 'none', overwrite: 'all', force3D: 'auto', clearProps: 'transform'});

  // Fade in spinner
  TweenMax.fromTo(this._$loading, 0.5, {opacity: 0}, {opacity: 1, display: 'block', ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform'});

  // Animate dots in spinner
  if(!CUI.animation.chatLoadingTimeline) CUI.animation.chatLoadingTimeline = new TimelineMax().staggerTo(this._$loading.find('span'), 0.6, {y: -6, yoyo: true, repeat: -1, repeatDelay: 0.3, ease: Back.easeInOut,  force3D: true, clearProps: 'transform'}, 0.1);
  else CUI.animation.chatLoadingTimeline.play();
};

/**
 * Hides the spinner and displays input.
 * @protected
 */
CUI.ChatPresenter.prototype._hideLoading = function(){
  // Hide spinner
  TweenMax.set(this._$loading, {opacity: 0, display: 'none', overwrite: 'all', force3D: 'auto', clearProps: 'transform'});

  // Pause spinner dots animation
  CUI.animation.chatLoadingTimeline.pause();

  // Show input
  TweenMax.fromTo(this._$inputContainer, 0.5, {opacity: 0}, {opacity: 1, display: 'block', ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform', onComplete: $.proxy(function(){
      // Focus textarea if inputType is text
      if(this._inputType == 'text') this._$inputContainer.find('.chat-input-text').find('textarea').focus();
  }, this)});
};

/**
 * Toggles the visibility of the sidebar.
 * @protected
 */
CUI.ChatPresenter.prototype._toggleSidebar = function(){
  var timeline = new TimelineMax();

  // Hide sidebar if visible
  if(this._isSidebarVisible){
    timeline.to(this._$sidebar, 0.6, {left: -320, ease: Sine.easeInOut});
    timeline.to($('main, .chat-input-bar'), 0.6, {paddingLeft: 0, ease: Sine.easeInOut}, 0);
    timeline.to(this._$sidebar.find('header .inner, section'), 0.5, {opacity: 0, x: -40, ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform'}, 0);
    this._isSidebarVisible = false;
  // Show sidebar if not visible
  }else{
    timeline.to(this._$sidebar, 0.6, {left: 0, ease: Sine.easeInOut});
    timeline.to($('main, .chat-input-bar'), 0.6, {paddingLeft: 320, ease: Sine.easeInOut}, 0);
    timeline.fromTo(this._$sidebar.find('header .inner, section'), 0.5, {opacity: 0, x: -40}, {opacity: 1, x: 0, ease: Sine.easeInOut, force3D: 'auto', clearProps: 'transform'}, 0.3);
    this._isSidebarVisible = true;
  }
};

/**
 * Toggles fullscreen.
 * @protected
 */
CUI.ChatPresenter.prototype._toggleFullscreen = function(){
  // Toggle fullscreen if allowed by browser
  if(screenfull.enabled){
   screenfull.toggle();
   if(screenfull.isFullscreen) this._$fullscreenToggle.addClass('active');
   else this._$fullscreenToggle.removeClass('active');
  }else{
   this._showNotification(CUI.text.errorNoFullscreenSupport);
  }
};

/**
 * Displays a notification.
 * @protected
 * @param {string} text   - The text to display in the notification.
 */
CUI.ChatPresenter.prototype._showNotification = function(text){
  $.notify(text, {
    delay: 4000
  });
};

/**
 * Scrolls to a message in the chat.
 * @protected
 * @param {number} id   - The ID of the message to scroll to.
 */
CUI.ChatPresenter.prototype._scrollToMessage = function(id){
  var $message;
  var top;

  // Check that message exists
  if(this._messages[id]){
    $message = this._messages[id].$el;
    top = $message.offset().top;
    TweenLite.to(window, this._getScrollSpeed(top), {scrollTo: top, ease: Power2.easeInOut});
  }
};

/**
 * Calculates the scroll animation time for window based on distance.
 * @protected
 * @param {number} scrollTo   - The new scroll position.
 * @returns {number}          - The animation time in seconds.
 */
CUI.ChatPresenter.prototype._getScrollSpeed = function(scrollTo){
  // Calculate distance
  var distance = Math.abs($(window).scrollTop() - scrollTo);
  var minSpeed = 1;
  var maxSpeed = 2;

  // Multiply distance with milliseconds
  var speed = (distance * 2) / 1000;

  // Make sure that speed is within the minSpeed - maxSpeed range
  speed = (speed < minSpeed) ? minSpeed : speed;
  speed = (speed > maxSpeed) ? maxSpeed : speed;

  return speed;
};

/**
 * Updates the input type visible in the chat.
 * @protected
 * @param {object} input          - An object with settings for the input type.
 */
CUI.ChatPresenter.prototype._setInput = function(input){
  var $text;
  var $options;
  var $custom;
  var $option;

  //Disable input
  this._inputIsEnabled = false;

  // Find containers for the various input types
  $text = this._$inputContainer.find('.chat-input-text');
  $options = this._$inputContainer.find('.chat-input-options');
  $custom = this._$inputContainer.find('.chat-input-custom');

  // Hide all input containers
  $text.hide();
  $options.hide();
  $custom.hide();

  // Empty dynamic content in input containers
  $custom.empty();
  if(this._inputOptions.length) $.each(this._inputOptions, function(i, io){
    io.destroy();
  });
  this._inputOptions = [];

  // Reset textarea size
  $text.find('textarea').val('').attr('rows', 1);

  // Create new input based on type
  if(input.type === 'text'){
   // Set input type
   this._inputType = 'text';

   // Set input url
   if(input.url) this._inputUrl = input.url;
   else throw new Error('CUI.ChatPresenter._setInput(): No input.url.');

   // Show text input
   $text.show();
  }else if(input.type === 'options'){
   // Set input type
   this._inputType = 'options';

   // Set input url
   if(input.url) this._inputUrl = input.url;
   else throw new Error('CUI.ChatPresenter._setInput(): No input.url.');

   // Check that we have an options array
   if(!(input.options instanceof Array && input.options.length > 0)) throw new Error('CUI.ChatPresenter._setInput(): No input.options.');

   // Create a button for each option
   $.each(input.options, $.proxy(function(i, o){
     // Create a new input option
     var inputOption = new CUI.InputOptionPresenter(new CUI.InputOptionModel(o));
     this._inputOptions.push(inputOption);

     // Append input option
     $options.append(inputOption.$el);
   }, this));

   // Show input
   $options.show();
  }else if(input.type === 'custom'){
   // Set input type
   this._inputType = 'custom';

   // No input url for custom
   this._inputUrl = null;

   // Add custom HTML to input
   if(input.html){
     $custom.html(input.html);
   }else{
     throw new Error("CUI.ChatPresenter._setInput(): No input.html.");
   }

   // Show input
   $custom.show();
  }else{
   // Throw an error if type is missing or invalid
   throw new Error('CUI.ChatPresenter._setInput(): Invalid input.type');
  }

  // Set the array of ids for messages that contains selectable elements
  if(input.includeSelectedValuesFromMessages) this._includeSelectedValuesFromMessages = input.includeSelectedValuesFromMessages;
  else this._includeSelectedValuesFromMessages = [];

  // Enable input
  this._inputIsEnabled = true;
};

/**
 * Adds event listeners to the chat.
 * @protected
 */
CUI.ChatPresenter.prototype._addEventListeners = function(){
  // Sidebar toggle
  this._$sidebarToggle.on('click', $.proxy(function(e){
    e.preventDefault();
    $(e.currentTarget).toggleClass('active');

    this._toggleSidebar();
  }, this));

  // Fullscreen toggle
  this._$fullscreenToggle.on('click', $.proxy(function(e){
    e.preventDefault();
    this._toggleFullscreen();
  }, this));

  // Delegated event listeners for input options
  this._$inputContainer.find('.chat-input-options').on('click', '.chat-option', $.proxy(function(e){
    e.preventDefault();

    // Post input to server
    this._postOption($(e.currentTarget).data('option-value'));
  }, this));

  // Delegated events for sidebar breakpoint links
  this._$sidebarBreakpointsContainer.on('click', 'li', $.proxy(function(e){
    e.preventDefault();

    // Scroll to message
    this._scrollToMessage($(e.currentTarget).data('href'));
  }, this));

  // Text input submit
  this._$inputContainer.find('#chat-input-text-form').on('submit', $.proxy(function(e){
    e.preventDefault();

    // Validate and post text to server
    this._postText();
  }, this)).on('keyup', $.proxy(function(e){
    // Submit form on enter but ignore if ctrl, alt or shift is pressed
    if(e.which == 13 && (!e.shiftKey && !e.ctrlKey && !e.altKey)) {
      e.preventDefault();
      this._$inputContainer.find('#chat-input-text-form').submit();
    }
  }, this));

  // Overflow actions
  this._$messagesContainer.on('click', '.chat-actions li', $.proxy(function(e){
    e.preventDefault();

    // Hide actions
    $(e.currentTarget).closest('ul').stop().fadeToggle();

    // Post action
    var action = $(e.currentTarget).data('action');
    this._postAction(action);
  }, this));

  // Autoexpanding textarea for text input
  this._$inputContainer.find('.chat-input-text textarea').expandingTextarea({maxRows: 10});
};
