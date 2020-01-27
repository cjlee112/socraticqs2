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
CUI.ChatPresenter = function(chatID, historyUrl, progressUrl, resourcesUrl, updatesUrl, showUpdates){
  // Check arguments
  if(typeof chatID !== 'number') throw new Error('CUI.ChatPresenter(): Invalid chatID.');
  if(!historyUrl) throw new Error('CUI.ChatPresenter(): No historyUrl.');
  if(!progressUrl) throw new Error('CUI.ChatPresenter(): No progressUrl.');
  if(!resourcesUrl) throw new Error('CUI.ChatPresenter(): No resourcesUrl.');
  if(!updatesUrl) throw new Error('CUI.ChatPresenter(): No updatesUrl.');

  /* When chat gets doWait parameter it should show messages only first time. This flag is about it.
   * @type {bool}
   * @protected
   */
  this._needShowMsg = true;

  /**
   * The chat's unique ID.
   * @type {number}
   * @protected
   */
  this._chatID = chatID;

  /**
   * Current thread unique ID.
   * @type {number}
   * @protected
   */
  this._currentThreadId = -1;

  /**
   * An id of a thread that is next to be activated after the update sequence is over.
   * @type {Number}
   * @protected
   */
  this._flowPreviousThreadId = -1;

  /**
   * Previous thread unique ID.
   * @type {number}
   * @protected
   */
  this._previousThreadId = -1;

  /**
   * An udpates thread ID. (possible duplicates with {this._currentThreadId})
   */
  this._updatesThreadId = -1;

  /**
   * A reference to Back to Breaktpoint button
   * @type {CUI.ChatBackToBreakpointButtonPresenter}
   * @protected
   */
  this._backToBreakpointButton = null;

  /**
   * A reference to the chat input container
   * @type {CUI.Chat}
   * @protected
   */
  this._inputContainer = new CUI.ChatInputContinerPresenter();

  /**
   * A reference to Chat messages container.
   * @type {CUI.ChatMessagesContainerPresenter}
   * @protected
   */
  this._messagesContainer = new CUI.ChatMessagesContainerPresenter();

  /**
   * An object with references to all messages, media, and breakpoints currently in the chat grouped by threadId.
   * @type {Object.<number, Object.<number, CUI.ChatMessagePresenter|CUI.ChatMediaPresenter|CUI.ChatBreakpointPresenter>>}
   * @protected
   */
  this._messagesByThread = {};

  /**
   * Messages split to the ones that are related to a thread Id with updates that is currently open. And the rest of them.
   * @type {Object.<relatedMessages|subsequentMessages, CUI.ChatMessagePresenter|CUI.ChatMediaPresenter|CUI.ChatBreakpointPresenter>}
   */
  this._$splitMessages = {};

  /**
   * An array with references to all breakpoints currently in the sidebar.
   * @type {Array.<CUI.SidebarBreakpointPresenter>}
   * @protected
   */
  this._sidebarBreakpoints = {};

  /**
   * An array with references to all resources currently in the sidebar.
   * @type {Array.<CUI.SidebarBreakpointPresenter>}
   * @protected
   */
  this._sidebarResources = {};

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
   * The url for loading a resources of the unit.
   * @type {string}
   * @protected
   */
  this._resourcesUrl = resourcesUrl;

  /**
   * The url for loading a updates of the unit.
   * @type {string}
   * @protected
   */
  this._updatesUrl = updatesUrl;

  /**
   * The currently active input type in the chat. 'text', 'options', or 'custom'.
   * @type {string}
   * @protected
   */
  this._inputType = null;

  /** Input sub type: {multipleChioce,}
   *
   * @type {null}
   * @private
   */
  this._inputSubType = null;

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
   * Inidicates if we should accpect updates during next messages parsing.
   * @type {Boolean}
   * @protected
   */
  this._viewUpdatesPending = false;

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
   * Define if we want to see updates on load.
   * @type {boolean}
   * @protected
   */
  this._showUpdates = showUpdates;

  /**
   * Indicates if we are view an update thread currently.
   * @type {boolean}
   * @protected
   */
  this._isInUpdateThread = false;

  /**
   * Indicates if an update thread is beeing opend at the moment.
   * @type {Boolean}
   * @protected
   */
  this._isShowingMessagesUpToThread = false;

  /**
   * Scroll to new messages after parsing.
   * @type {Boolean}
   * @protected
   */
  this._scrollToNewMessageOnParsing = true;

  /**
   * Current window/chat scrollTop position. (used when in update thread)
   * @type {Number}
   * @protected
   */
  this._currentChatBottomMessageScrollTop = 0;

  /**
   * Regular window/chat scrollTop position. (used regularly)
   * @type {Number}
   * @protected
   */
  this._regularChatBottomMessageScrollTop = 0;

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
   * A jQuery reference to the container element for sidebar breakpoints.
   * @type {jQuery}
   * @protected
   */
  this._$sidebarResourcesContainer = $('.chat-sidebar-resources');

  /**
   * A jQuery reference to the container element for sidebar breakpoints header.
   * @type {jQuery}
   * @protected
   */
  this._$sidebarResourcesHeaderContainer = $('.chat-sidebar-resources-header');

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

  /**
   * Equation preview.
   * @type {*|jQuery|HTMLElement}
   */
  this.equationPreview = $('.preview');

  this.sidebarCourseLink = $('aside.chat-sidebar header a');

  // Attach scroll stopped listener, which emmits 'scrollStopped' event on $(window) object.
  CUI.utils.attachScrollStoppedEmitter();

  // Add event listeners
  this._addEventListeners();

  // Update fullscreen icon if fullscreen is active
  if(screenfull.isFullscreen) this._$fullscreenToggle.addClass('active');

  // Show chat
  this._showChat();

  return this;
};

/**
 * Static namespace.
 */

/**
 * Messages placement positions.
 */
CUI.ChatPresenter.messagePlacement = CUI.ChatPresenter.messagePlacement || {};
CUI.ChatPresenter.messagePlacement.top = "top";
CUI.ChatPresenter.messagePlacement.bottom = "bottom";

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
    data: {chat_id: this._chatID},
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
    data: {chat_id: this._chatID},
    cache: false,
    context: this
  }).done(this._parseProgress).fail(function(){
    throw new Error('CUI.ChatPresenter._getProgress(): Could not load progress.');
  });
};

/**
 * Loads resources of the unit and sends the response to {@link CUI.ChatPresenter#_parseResources}.
 * @protected
 */
CUI.ChatPresenter.prototype._getResources = function(){
  // Get progress
  $.ajax({
    url: this._resourcesUrl,
    method: 'GET',
    dataType: 'json',
    data: {chat_id: this._chatID},
    cache: false,
    context: this
  }).done(this._parseResources).fail(function(){
    throw new Error('CUI.ChatPresenter._getResources(): Could not load resources.');
  });
};

/**
 * Loads a user's next set of messages and input type.
 * @protected
 * @param {Object} params - Parameters object.
 * @param {string} params.url - A url for loading a user's next set of messages and input type.
 * @param {Boolean} params.parseUpdateMessages - A flag indicating to parse update messages.
 */
CUI.ChatPresenter.prototype._requestMessages = function(params){
  params = params || {};
  // Get messages and input
  $.ajax({
    url: params.url,
    method: 'GET',
    dataType: 'json',
    data: {chat_id: this._chatID},
    cache: false,
    context: this
  }).done(function(data){
    // Update resources
    this._getResources();
    // Update progress
    this._getProgress();
    // Update the current input type in the chat
    if(data.input) this._setInput(data.input);
    else throw new Error("CUI.ChatPresenter._requestMessages(): No data.input.");

    // Update chat with new messages
    if(data.addMessages) {
      this._parseMessages(data, {
        scrollToFirst: this._scrollToNewMessageOnParsing,
        parseUpdateMessages: params.parseUpdateMessages
      });
      if (!this._scrollToNewMessageOnParsing) {
        this._scrollToNewMessageOnParsing = true;
      }
    } else {
      throw new Error("CUI.ChatPresenter._requestMessages(): No data.addMessages.");
    }

    // Hide spinner
    this._hideLoading();
  }).fail(function(){ throw new Error("CUI.ChatPresenter._requestMessages(): Failed to load messages."); });
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

  input.selected = this._messagesContainer.getMessageSelectedValues();
  input.chat_id = this._chatID;

  // Add selected elements to input
  // if (this._inputType == 'options' &&
  //     this._includeSelectedValuesFromMessages.length &&
  //     this._inputSubType == 'choices' &&
  //     !Object.keys(input.selected).length
  // ) {
  //     this._inputIsEnabled = true;
  //     this._showNotification("Choose a correct answer!zjhb zkjzbdfmz bmdfjh");
  //     return;
  // }

  if (this._inputSubType === 'canvas') {
    var svgContainer = $('.draw-svg-container:last');
    if(svgContainer.length) {
        svgContainer[0].dispatchEvent(new CustomEvent('disable-canvas'));
    }
  }

  // Show loading
  this._showLoading();

  // Post input to server
  $.ajax({
    url: this._inputUrl,
    method: 'PUT',
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(input),
    cache: false,
    context: this
  }).done(function(response){
    // Check that nextMessagesUrl is in response
    if(response && response.nextMessagesUrl && response.input && !response.input.doWait){
        // Load next set of messages
        this._requestMessages({url: response.nextMessagesUrl});
        // set flag to true, because we need to show messages
        this._needShowMsg = true;
    }else if(response && response.input && response.input.doWait) {
      if(this._needShowMsg){
       /* parse response to understand should we do more requests or not.
        * this.setInput function will look into response.input.doWait parameter
        * and if doWait is true will call setTimeout function with needed parameters.
        */
        this._requestMessages({url: response.nextMessagesUrl});
        // set to false cause we already shown messages.
        this._needShowMsg = false;
      }else{
        this._setInput(response.input);
      }
    }else if(response.error){
      // Enable input
      this._inputIsEnabled = true;

      // enable canvas
      if (this._inputSubType === 'canvas') {
          $('.draw-svg-container:last')[0].dispatchEvent(new CustomEvent('enable-canvas'));
      }

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
    // enable canvas
    if (this._inputSubType === 'canvas') {
        $('.draw-svg-container:last')[0].dispatchEvent(new CustomEvent('enable-canvas'));
    }

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
  var text;
  switch(this._inputSubType) {
    case 'numbers':
      text = this._$inputContainer.find('.chat-input-text').find('input').val();
      break;
    case 'canvas':
      input.attachment = 'data:image/svg+xml;base64,' + btoa(this._$inputContainer.find('.chat-input-custom').find('input').val());
      text = this._$inputContainer.find('.chat-input-text').find('textarea').val();
      break;
    default:
      // reset text in textarea
      text = this._$inputContainer.find('.chat-input-text').find('textarea').val();
      this._$inputContainer.find('.chat-input-text').find('textarea').val('');
      break;
  }
  // Add text to input object if set
  input.text = text;
  input.chat_id = this._chatID;

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
  input.chat_id = this._chatID;

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
        this._requestMessages({url: response.nextMessagesUrl});
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
 * Update a "Back to previous breakpoint thread" button.
 * @protected
 * @param {Object} info - previous breakpoint info.
 * @param {number} info.threadId - breakpoint hread ID.
 * @param {string} info.html -  breakpoint title.
 * @param {string} info.type -  breakpoint type one of CUI.ChatBackToBreakpointButtonModel.ItemType.
 */
CUI.ChatPresenter.prototype._updateBackToBreakpointButton = function(info) {
  if (info.threadId < 0) {
    if (this._backToBreakpointButton) {
      this._backToBreakpointButton.destroy();
      this._backToBreakpointButton = null;
    }
  } else {
    var model = new CUI.ChatBackToBreakpointButtonModel(info);

    if (this._backToBreakpointButton) {
      this._backToBreakpointButton.update(model);
    } else {
      this._backToBreakpointButton = new CUI.ChatBackToBreakpointButtonPresenter(model);
    }

    this._$messagesContainer.prepend(this._backToBreakpointButton.$el);
  }
};

/**
 * Update a "To next breakpoint thread" button.
 * @protected
 * @param {Object} info - to next breakpoint info.
 * @param {number} info.threadId - breakpoint hread ID.
 * @param {string} info.html -  -reakpoint title.
 * @param {string} info.type -  breakpoint type one of CUI.ChatBackToBreakpointButtonModel.ItemType.
 */
CUI.ChatPresenter.prototype._updateToNextBreakpointButton = function(info) {
  info = info || {
    threadId: -1,
    html: ''
  };

  if (info.threadId < 0) {
    this._inputContainer.removeNextThreadButton();
  } else {
    this._inputContainer.placeNextThreadButton(info, $.proxy(onChangeThreadButtonClickHandler, this));
  }
};

/**
 * Set current thread Id
 * @protected
 * @param {Object} params           - all neccessary parameters.
 * @param {Number} params.threadID  -
 * @param {Boolean} params.setUpdatesThreadId
 */
CUI.ChatPresenter.prototype._setCurrentThreadId = function(params) {
  params = params || {};

  if (!params.threadId) throw new Error('CUI.ChatPresenter.prototype._setCurrentThreadId(): threadId parameter is missing!');

  this._currentThreadId = params.threadId;

};

/**
 * TODO: During resource parsing currentThreadId is treated incorrectly!
 */

/**
 * Manualy update current sidebar breakpoint.
 * @protected
 */
CUI.ChatPresenter.prototype._updateCurrentSidebarBreakpoint = function() {
  $('.chat-sidebar > section > ul > li').each($.proxy(function(i, breakpoint) {
    var $breakpoint = $(breakpoint);
    var breakpiontThreadId = $breakpoint.data('thread-id');

    if ($breakpoint.hasClass('is-active')) {
      if (breakpiontThreadId !== this._currentThreadId) {
        $breakpoint.toggleClass('is-active');
      }
    } else {
      if (breakpiontThreadId === this._currentThreadId) {
        $breakpoint.toggleClass('is-active');
      }
    }
  }, this));
};

/**
 * Gets called when the history has loaded to initialize and show the chat.
 * @protected
 */
CUI.ChatPresenter.prototype._showChat = function(){
  // Fade out preloader
  var timeline = new TimelineMax();
  var $messagesContainer = this._messagesContainer.$root;

  // Show chat
  $messagesContainer.show();
  this._$sidebar.show();
  this._$inputBar.show();
  timeline.fromTo($messagesContainer, 1.2, {opacity: 0}, {opacity: 1, ease: Power1.easeInOut, force3D: 'auto', clearProps: 'transform'});
  timeline.from(this._$inputBar, 0.7, {bottom: -85, ease: Power1.easeInOut, force3D: 'auto', clearProps: 'transform'}, 0.3);

  //Scroll to chat
  var top = $messagesContainer.offset().top;
  TweenLite.to(window, this._getScrollTime(top), {scrollTo: {y: top, autoKill: false}, ease: Power2.easeInOut, onComplete: $.proxy(function(){
    // Get message history
    this._getHistory();

    // Update progress
    this._getProgress();
    this._getResources();
  }, this)});

  if(CUI.config.is_test || CUI.config.is_preview) {
    this.sidebarCourseLink.attr('href', '');
  };
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
      var threadsCompletedCount = 0;

      // Add new breakpoints
      /**
       * TODO: remove it eventually
      var compoundUpdatesCounter = 0;
      */

      // Set current thread id to the first breakpoint threadId on first load
      if (this._currentThreadId === -1) {
        this._setCurrentThreadId({threadId: data.breakpoints[0].threadId});
      }

      $.each(data.breakpoints, $.proxy(function(i, b){
        /**
       * TODO: remove it eventually
        compoundUpdatesCounter += b.updatesCount;
        */
        // Create breakpoint from template

        b.isCurrent = b.threadId === this._currentThreadId;

        breakpoint = new CUI.SidebarBreakpointPresenter(new CUI.SidebarBreakpointModel(b));

        if (b.isDone) {
          threadsCompletedCount++;
        }

        // Add reference to breakpoint
        this._sidebarBreakpoints.push(breakpoint);

        // Add breakpoint in sidebar
        this._$sidebarBreakpointsContainer.append(breakpoint.$el);
      }, this));

      if (!data.is_live && threadsCompletedCount == this._sidebarBreakpoints.length){
        this._$sidebarToggle.trigger('resources');
      }
    }
    /**
    * TODO: remove it eventually
    if ( compoundUpdatesCounter > 0 ) {
      $('.chat-counter').html(compoundUpdatesCounter);
      $('.chat-counter').show();
    }
    else if ( compoundUpdatesCounter == 0 ) {
      $('.chat-counter').hide();
    }
    */
  }else{
    throw new Error('CUI.ChatPresenter._parseProgress(): No data.progress');
  }
};

/**
 * Get info of a previous thread in realtion to the provided one.
 * @protected
 * @param {number} threadId - an ID of a thread to get previous thread Info for.
 *
 * @returns {Object}        - {threadId: -1, html: '', type: ''} is returned in case of failure, real data otherwise.
 */
CUI.ChatPresenter.prototype._getPreviousThreadInfo = function(threadId) {
  var previousItem = {
    threadId: -1,
    html: '',
  };
  var itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.none;
  var breakpoints = this._sidebarBreakpoints;
  var resources = this._sidebarResources;

  for (var i = 0; i < breakpoints.length; i++) {
    var currentBreakpoint = breakpoints[i].getInfo();

    if (currentBreakpoint.threadId === threadId) {
      itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.breakpoint;
      break;
    }

    previousItem = breakpoints[i].getInfo();
  }

  // Item was not found among the breakpoints.
  if (itemType == CUI.ChatBackToBreakpointButtonModel.ItemType.none) {
    for (var i = 0; i < resources.length; i++) {
      var currentResource = resources[i].getInfo();

      if (currentResource.threadId === threadId) {
        if (i == 0) {
          itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.breakpoint;
        } else {
          itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.resource;
        }

        break;
      }

      previousItem = resources[i].getInfo();
    }
  }

  previousItem.type = itemType;
  return previousItem;
};

/**
 * Get info of a thread with threadId.
 * @protected
 * @param {number} threadId - an ID of a thread to get Info for.
 *
 * @returns {Object}        - {threadId: -1, html: '', type: 'none'} is returned in case of failure, real data otherwise.
 */
CUI.ChatPresenter.prototype._getThreadInfo = function(threadId) {
  var foundItem = {
    threadId: -1,
    html: '',
  };
  var itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.none;
  var breakpoints = this._sidebarBreakpoints;
  var resources = this._sidebarResources;

  for (var i = 0; i < breakpoints.length; i++) {
    var currentBreakpoint = breakpoints[i].getInfo();

    if (currentBreakpoint.threadId == threadId) {
      itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.breakpoint;
      foundItem = breakpoints[i].getInfo();
      break;
    }
  }

  // Item was not found among the breakpoints.
  if (itemType == CUI.ChatBackToBreakpointButtonModel.ItemType.none) {
    for (var i = 0; i < resources.length; i++) {
      var currentResource = resources[i].getInfo();

      if (currentResource.threadId == threadId) {
        itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.resource;
        foundItem = resources[i].getInfo();
        break;
      }
    }
  }

  foundItem.type = itemType;
  return foundItem;
}


/**
 * Get info of a next thread in realtion to the provided one.
 * @protected
 * @param {number} threadId - an ID of a thread to get next thread Info for.
 *
 * @returns {Object}        - {threadId: -1, html: '', type: ''} is returned in case of failure, real data otherwise.
 */
CUI.ChatPresenter.prototype._getNextThreadInfo = function(threadId) {
  var previousItem = {
    threadId: -1,
    html: '',
  };
  var itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.none;
  var breakpoints = this._sidebarBreakpoints;
  var resources = this._sidebarResources;

  for (var i = resources.length - 1; i >= 0; i--) {
    var currentResource = resources[i].getInfo();

    if (currentResource.threadId === threadId) {
      itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.resource;
      break;
    }

    previousItem = resources[i].getInfo();
  }

  // Item was not found among the resources.
  if (itemType == CUI.ChatBackToBreakpointButtonModel.ItemType.none) {
    var lastElementIndex = breakpoints.length - 1;

    for (var i = lastElementIndex; i >= 0; i--) {
      var currentBreakpoint = breakpoints[i].getInfo();

      if (currentBreakpoint.threadId === threadId) {
        if (i == lastElementIndex) {
          itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.resource;
        } else {
          itemType = CUI.ChatBackToBreakpointButtonModel.ItemType.breakpoint;
        }

        break;
      }

      previousItem = breakpoints[i].getInfo();
    }
  }

  previousItem.type = itemType;

  return previousItem;
};

/**
 * Get a list of all thread brekapoints with updates.
 * @protected
 *
 * @returns {Array<CUI.SidebarBreakpointPresenter>} - array of objects with {@link CUI.SidebarBreakpointPresenter}.
 */
CUI.ChatPresenter.prototype._getThreadsWithUpdates = function() {
  var breakpointsWithUpdates = new Array();

  this._sidebarBreakpoints.forEach(function(breakpoint) {
    if (breakpoint.getInfo().updatesCount) {
      breakpointsWithUpdates.push(breakpoint);
    }
  });

  return breakpointsWithUpdates;
};

  /**
 * Parses resources data and updates the list of breakpoints in the sidebar.
 * @protected
 * @param {object} data               - An object containing the user's progress.
 * @param {number} data.progress      - The user's progress 0 - 1.
 * @param {Array} data.breakpoints    - An array of breakpoints to display in the sidebar.
 */
CUI.ChatPresenter.prototype._parseResources = function(data){
  var breakpoint;

    if(data){
      // Add breakpoints to the sidebar
      if(data.breakpoints instanceof Array && data.breakpoints.length > 0){
        // Remove existing breakpoints
        $.each(this._sidebarResources, $.proxy(function(i, b){
          b.destroy();
        }, this));

        // Show resources header.
        // If no resources - hide resources header. Needed for live chat.
        this._$sidebarResourcesHeaderContainer.show();

        // Reset breakpoints Array
        this._sidebarResources = [];

        // Set current thread id to the first breakpoint threadId on first load
        // if (this._currentThreadId === -1) {
        //   console.log('')
        //   this._setCurrentThreadId({threadId: data.breakpoints[0].threadId});
        // }

        // Add new breakpoints
        $.each(data.breakpoints, $.proxy(function(i, b){

          b.isCurrent = b.threadId === this._currentThreadId;

          // Create breakpoint from template
          breakpoint = new CUI.SidebarResourcePresenter(new CUI.SidebarResourceModel(b));

          // Add reference to breakpoint
          this._sidebarResources.push(breakpoint);

          // Add breakpoint in sidebar
          this._$sidebarResourcesContainer.append(breakpoint.$el);
        }, this));
      } else {
        // If no resources - hide resources header. Needed for live chat.
        this._$sidebarResourcesHeaderContainer.hide();
      }
    }
  else{
    throw new Error('CUI.ChatPresenter._parseResources(): No data');
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
  if(data.addMessages) this._parseMessages(data, {scrollToFrist: false});
  else throw new Error("CUI.ChatPresenter._parseHistory(): No data.addMessages.");

  // Enable input
  this._hideLoading();

  // Get extras settings
  var extras = data.extras || {};

  // If we're in the middle of going through a thread with updates
  if (extras.updates && extras.updates.threadId) {
    var threadId = extras.updates.threadId;
    var threadMessages = this._messagesContainer.getThreadsRelatedMessages([threadId]);

    if (threadMessages.length > 0) {
      var lastMessageId = threadMessages[threadMessages.length - 1].data('message-id');

      // Scroll to updates messages and update curren scroll position
      this._scrollToUpdatesMessage(threadId, lastMessageId, true);
    }
  }

  // Show updates if needed (usually is triggered by a url hash #updates)
  if (this._showUpdates) {
    if (CUI.config.updated_thread_id !== -1) {
      this._getThreadUpdates($("li[data-thread-id="+CUI.config.updated_thread_id+"]"));
    }

    this._showUpdates = false;
  }
};

/**
 *
 */
CUI.ChatPresenter.prototype._scrollToUpdatesMessage = function(threadId, messageId, updateCurrentScrollPosition) {
  var scrollParams = new Object();

  this._updatesThreadId = threadId;
  this._setCurrentThreadId({threadId});
  this._updateCurrentSidebarBreakpoint();

  scrollParams.id = messageId;
  scrollParams.messagePlacement = CUI.ChatPresenter.messagePlacement.bottom;
  // scrollParams.updateCurrentScrollPosition = true;
  scrollParams.updateCurrentScrollPosition = updateCurrentScrollPosition;
  scrollParams.onScrollFinished = $.proxy(function() {
    // Showing update messages for the first time.
    this._showMessagesUpToThread(this._updatesThreadId, {firstTime: true});
    this._inputContainer.threadNavBar.setState(CUI.ThreadNavBar.state.showSubsequentThreads);
  }, this);

  this._scrollToMessage(scrollParams);
};

CUI.ChatPresenter.prototype._isLastUpdatedThreadMesaage = function(messageModel) {
  return messageModel.html === 'Now you can move to the next lesson';
};

/**
 * Adds, updates, and removes messages in the chat.
 * @protected
 * @param {Object} data                         - An object containing messages and what input type do display.
 * @param {Array} data.addMessages              - An array with message objects that will be added to the chat.
 * @param {Array} [data.updateMessages]         -  An array with message objects that will be updated in the chat.
 * @param {Array} [data.deleteMessages]         - An array of message ids for messages that will be removed from the chat.
 * @param {Object} params                       - An object containing extra parameters.
 * @param {boolean} params.scrollToFirst        - Scroll to first new message.
 * @param {Boolean} params.parseUpdateMessages  - Parse update messages (hide subsequent threads).
 */
CUI.ChatPresenter.prototype._parseMessages = function(data, params){
  params = params || {};
  var newMessages = [];

  // Add new messages
  if(data.addMessages instanceof Array && data.addMessages.length > 0){
    $.each(data.addMessages, $.proxy(function(i, m){
      var model;

      // Create a model based on type
      if (m.type === 'breakpoint') {
        model = new CUI.ChatBreakpointModel(m);
      } else {
        if (m.type === 'message') {
          model = new CUI.ChatMessageModel(m);
        } else if (m.type === 'media') {
          model = new CUI.ChatMediaModel(m);
        } else throw new Error("CUI.ChatPresenter._parseMessages(): Invalid m.type.");
      }

      // Add message to chat
      var $newMessage = this._messagesContainer.addMessage(model);
      if ($newMessage) {
        newMessages.push($newMessage);
      }
    }, this));
  }else{
    throw new Error("CUI.ChatPresenter._parseMessages(): No data.addMessages.");
  }

  // Update messages
  if(data.updateMessages instanceof Array && data.updateMessages.length > 0){
    $.each(data.updateMessages, $.proxy(function(i, m){
      var model;

      // Create a model based on type
      if(m.type === 'message') {
        model = new CUI.ChatMessageModel(m);
      } else if(m.type === 'media') {
        model = new CUI.ChatMediaModel(m);
      } else if(m.type === 'breakpoint') {
        model = new CUI.ChatBreakpointModel(m);

      } else throw new Error("CUI.ChatPresenter._parseMessages(): Invalid m.type.");

      //Update messages
      this._messagesContainer.updateMessage(model);
    }, this));
  }

  // Delete messages
  if(data.deleteMessages instanceof Array && data.deleteMessages.length > 0){
    $.each(data.deleteMessages, $.proxy(function(i, id){
      this._messagesContainer.removeMessage(id);
    }, this));
  }

  // Animate new messages
  TweenMax.from(newMessages, 0.7, {opacity: 0, scale: 0.9, ease: Power1.easeOut, force3D: true, clearProps: 'transform', onComplete: function(){
    // Draw equations after animation has completed
    MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
  }});


  // Scroll to first new message, update scroll position and resume scroll detection
  if (params.scrollToFirst) {
    if (this._viewUpdatesPending) {
      this._viewUpdatesPending = false;

      var $lastMessage = newMessages[newMessages.length - 1];
      var lastMessageId = $lastMessage.data('message-id');

      this._updatesThreadId = $lastMessage.data('thread-id');

      // Scroll to message & update current chat bottom position
      this._scrollToUpdatesMessage(this._updatesThreadId, lastMessageId, true);
    } else {
      var scrollParams = new Object;

      scrollParams.id = newMessages[0].data('message-id');
      scrollParams.messagePlacement = CUI.ChatPresenter.messagePlacement.top;
      scrollParams.updateScrollPosition = true;

      this._scrollToMessage(scrollParams);
    }
  } else {
      // When returning from an 'updates' thread we can revieve messages from the previous thread
      // So we figure out the latest thread of the newMessages and scroll to the first one of them
      var latestThreadId = newMessages[newMessages.length - 1].data('thread-id');
      var latestThreadMessages = newMessages.filter(function($message) {
        return $message.data('thread-id') === latestThreadId;
      });

      var scrollParams = new Object;
      scrollParams.id = latestThreadMessages[0].data('message-id');
      scrollParams.messagePlacement = CUI.ChatPresenter.messagePlacement.top;
      scrollParams.updateScrollPosition = true;

      this._scrollToMessage(scrollParams);
  }
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
   var scrollToPos = $(window).scrollTop();
   $(document).one(screenfull.raw.fullscreenchange, function() {
        $(window).scrollTop(scrollToPos);
    });
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
 * Show only messages related to the specified thread ID.
 * @protected
 * @param {number} threadId   - The ID of a thread to display messages of.
 */
CUI.ChatPresenter.prototype._showThreadMessages = function(threadId){
  var $messageElementToScrollTo = null;
  threadId = parseInt(threadId);

  this._messagesContainer.getAllMessageElements().each(function(){
    var $messageElement = $(this);

    if ($messageElement.data('thread-id') === threadId) {
      $messageElement.show();

      if (!$messageElementToScrollTo && $messageElement.hasClass('chat-breakpoint')) {
        $messageElementToScrollTo = $messageElement;
      }
    } else {
      $messageElement.hide();
    }
  });

  var scrollToMessageId = $messageElementToScrollTo ? $messageElementToScrollTo.data('message-id') : -1;
  if (scrollToMessageId >= 0) {
    // Scroll to message and update scroll position
    this._scrollToMessage({
      id: scrollToMessageId,
      updateScrollPosition: true
    });
  }
};

/**
 * Get an object with two lists of all messages split to the ones
 * related to sidebar breakpoints up to current threadID and the rest.
 * @private
 * @param {Number} threadId
 * @returns {Object}
 */
CUI.ChatPresenter.prototype._getMessagesOfBreakpointsSplitBy = function(threadId) {
  var sliceIndex = -1;

  for (var i = 0; i < this._sidebarBreakpoints.length; i++) {
    var currentBreakpoint = this._sidebarBreakpoints[i];

    if (currentBreakpoint.getInfo().threadId === threadId) {
      sliceIndex = i + 1;
      break;
    }
  }

  var relatedThreadIds = this._sidebarBreakpoints.slice(0, sliceIndex).map(function(breakpoint) {
    return breakpoint.getInfo().threadId;
  });
  var subsequentThreadIds = this._sidebarBreakpoints.slice(sliceIndex).map(function(breakpoint) {
    return breakpoint.getInfo().threadId;
  })

  var relatedBreakpoints = this._messagesContainer.getThreadsRelatedChatBreakpoints(relatedThreadIds);
  var subsequentBreakpoints = this._messagesContainer.getThreadsRelatedChatBreakpoints(subsequentThreadIds);

  var relatedMessages = this._messagesContainer.getThreadsRelatedMessages(relatedThreadIds);
  var subsequentMessages = this._messagesContainer.getThreadsRelatedMessages(subsequentThreadIds);

  return {relatedMessages, subsequentMessages, relatedBreakpoints, subsequentBreakpoints};
};

/**
 * Show only messages related to the specified thread ID and previous threads.
 * @protected
 * @param {number} threadId           - A thread ID.
 * @param {Object} params             - An object containing extra parameters.
 * @param {Boolean} params.firstTime  - Open/filter messages for the first time.
 */
CUI.ChatPresenter.prototype._showMessagesUpToThread = function(threadId, params) {
  params = params || {};
  this._isInUpdateThread = true;
  threadId = parseInt(threadId);
  this._flowPreviousThreadId = this._currentThreadId;
  // this._currentThreadId = threadId;
  this._setCurrentThreadId({threadId});

  this._$splitMessages = this._getMessagesOfBreakpointsSplitBy(threadId);

  this._$splitMessages.relatedMessages.forEach(function($message){
    $message.show();
  });
  this._$splitMessages.relatedBreakpoints.forEach(function($breakpoint) {
    $breakpoint.show();
  });

  var hideSubsequentChatItems = $.proxy(function() {

    this._$splitMessages.subsequentMessages.forEach(function($message){
      $message.hide();
    });
    this._$splitMessages.subsequentBreakpoints.forEach(function($breakpoint){
      $breakpoint.hide();
    });
  }, this);

  if (this._$splitMessages.relatedMessages.length > 0 || this._$splitMessages.relatedBreakpoints.length > 0) {
    // Opening a thread with updates for the first time.
    if (params.firstTime) {
      hideSubsequentChatItems();
    } else {
      //Scroll to the last message and update scroll position
      var scrollToMessageId = this._$splitMessages.relatedMessages[this._$splitMessages.relatedMessages.length - 1].data('message-id');

      this._scrollToMessage({
        id: scrollToMessageId,
        messagePlacement: CUI.ChatPresenter.messagePlacement.bottom,
        updateScrollPosition: true,
        updateCurrentScrollPosition: params.updateCurrentScrollPosition,
        onScrollFinished: hideSubsequentChatItems
      });
    }
  } else {
    hideSubsequentChatItems();
  }
};

/**
 * Show (unhide) the messages that were hidden with _showMessagesUpToThread
 * @protected
 * @param {bool} scrollToLastMessage - indicate to scroll all the way down to the last message.
 */
CUI.ChatPresenter.prototype._showSubsequentThreadMessages = function(scrollToLastMessage) {
  this._$splitMessages.subsequentMessages.forEach(function($message){
    $message.show()
  });
  this._$splitMessages.subsequentBreakpoints.forEach(function($breakpoint) {
    $breakpoint.show();
  });

  var scrollToMessageId;

  if (scrollToLastMessage) {
    scrollToMessageId = this._messagesContainer.getAllMessageElements().last().data('message-id');

    this._scrollToMessage({
      id: scrollToMessageId,
      messagePlacement: CUI.ChatPresenter.messagePlacement.top,
      updateScrollPosition: true
    });
  } else {
    // First message of the first thread.
    var firstSubsequentThreadId = this._$splitMessages.subsequentBreakpoints[0].data('thread-id');
    var firstSubsequentMessage = this._messagesContainer.getThreadsRelatedMessages([firstSubsequentThreadId])[0][0];

    scrollToMessageId = $(firstSubsequentMessage).data('message-id');

    this._scrollToMessage({
      id: scrollToMessageId,
      messagePlacement: CUI.ChatPresenter.messagePlacement.bottom,
      updateScrollPosition: false,
    });
  }


};

CUI.ChatPresenter.prototype._scrollToResourceMessage = function(id, threadId, updateScrollPosition){
  var message;
  var $message;
  var top;

  this._setCurrentThreadId({threadId});
  this._updateCurrentSidebarBreakpoint();

  message = this._messagesContainer.getMessage(id);
  // Check that message exists
  if(message){
    $message = message.$el;
    // this._showThreadMessages(threadId);
    top = $message.offset().top - 60;
    this._tweenWindowScroll(top, updateScrollPosition ? $.proxy(this._updateChatBottomMessageScroll, this) : undefined);
  } else {
    // this._getMessages({url: this._resourcesUrl + ul + '/'});
    this._requestMessages({url: this._resourcesUrl + threadId + '/'});
  }
};

/**
 * Scrolls to a message in the chat.
 * @protected
 * @param {Object} params - function params.
 * @param {Number} params.id   - The ID of the message to scroll to.
 * @param {Boolean} params.updateScrollPosition - indicates that the "bottom/current message" position should be updated when message is scrolled into view.
 * @param {Boolean} params.updateCurrentScrollPosition - indicates that current scroll position has to be updated to.
 * @param {CUI.ChatPresenter.messagePlacement.<String>} params.messagePlacement - message placement flag: "top" or "bottom" of the chat. (default: "bottom")
 * @param {function} params.onScrollFinished - a function to call when scroll has finished.
 */
CUI.ChatPresenter.prototype._scrollToMessage = function(params){
  // {id, updateScrollPosition, messagePlacement, onScrollFinished}
  params = params || {};
  var message;
  var $message;
  var scrollToPosition;
  var messageTop;
  var topMargin = 14;
  var bottomMargin = 58 * window.devicePixelRatio;

  message = this._messagesContainer.getMessage(params.id);
  // Check that message exists
  if(message){
    $message = message.$el;
    messageTop = $message.offset().top;

    this._setCurrentThreadId({threadId: $message.data('thread-id')});

    // Only update sidbar if we recieve lesson messages.
    if (!this._resourcesAreUnlocked()) {
      this._updateCurrentSidebarBreakpoint();
    }

    switch(params.messagePlacement) {
      case CUI.ChatPresenter.messagePlacement.bottom:
        var height = $message.height();

        if (height < $window.height() + bottomMargin) {
          scrollToPosition = messageTop - $(window).height() + $message.height() + bottomMargin;
        } else {
          scrollToPosition = messageTop - topMargin;
        }
        break;

      case CUI.ChatPresenter.messagePlacement.top:
      default:
        scrollToPosition = messageTop - topMargin;
        break;
    }

    // scrollToPosition = messageTop - 14;
    this._scrollToVerticalPosition({
      positionY: scrollToPosition,
      updateScrollPosition: params.updateScrollPosition,
      updateCurrentScrollPosition: params.updateCurrentScrollPosition,
      onScrollFinished: params.onScrollFinished
    });
  }
};

/**
 * Scroll window to a given vertical position.
 * @protected
 * @param {Object} params                 -
 * @param {Number} positionY              - position to scroll to.
 * @param {Boolean} updateScrollPosition  - save scroll position of the window after scrolling is finished.
 * @param {funciton} onScrollFinished     - a callback function to be called after scrolling is finished.
 */
CUI.ChatPresenter.prototype._scrollToVerticalPosition = function(params){
  params = params || {};

  this._tweenWindowScroll(params.positionY, $.proxy(function() {
    if (params.updateScrollPosition) {
      this._updateChatBottomMessageScroll();
    }

    if (params.updateCurrentScrollPosition) {
      this._updateCurrentBottomMessageScroll();
    }

    if (params.onScrollFinished) {
      params.onScrollFinished();
    }
  }, this));
};

/**
 * Tween an actual window scroll to position.
 * @private
 */
CUI.ChatPresenter.prototype._tweenWindowScroll = function(position, onComplete) {
  var scrollTime = this._getScrollTime(position);

  TweenLite.killTweensOf(window);
  TweenLite.to(
    window,
    scrollTime,
    {
      scrollTo: position,
      ease: Power2.easeInOut,
    }
  );

  if (onComplete) {
    TweenLite.delayedCall(scrollTime, onComplete);
  }
};

/**
 * Update regular chat bottom messages scroll position.
 * @protected
 */
CUI.ChatPresenter.prototype._updateChatBottomMessageScroll = function () {
  this._regularChatBottomMessageScrollTop = $window.scrollTop();
};

/**
 * Update currrent chat bottom messages scroll position.
 * @protected
 */
CUI.ChatPresenter.prototype._updateCurrentBottomMessageScroll = function () {
  this._currentChatBottomMessageScrollTop = $window.scrollTop();
};


/**
 * Calculates the scroll animation time for window based on distance.
 * @protected
 * @param {number} scrollTo   - The new scroll position.
 * @returns {number}          - The animation time in seconds.
 */
CUI.ChatPresenter.prototype._getScrollTime = function(scrollTo){
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

/* Inner function for runWaitTimer. This function will be called inside of setTimeout.
 */
CUI.ChatPresenter.prototype._waitTimerInnerFunc = function(input){
  this._inputIsEnabled = true;
  var me = this;
  return function() {
    me._postInput({
     chat_id: input.chat_id,
     url: input.url,
     type: 'options',
     options: [],
     selected: {}
    }); //input)
  };
}

/**
 * This function handles WAIT_* nodes of fsm looking at input.doWait field.
 * If doWait field is true, it will be in cycle until doWait came to be false.
 * @protected
 * @param {} input
*/
CUI.ChatPresenter.prototype._runWaitTimer = function(input) {
  if(input.url) this._inputUrl = input.url;
   else throw new Error('CUI.ChatPresenter._setInput(): No input.url.');
   var timeout_id = window.setTimeout(this._waitTimerInnerFunc(input), 1000*2); // run after 2 seconds.
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

  $textarea = $text.find('.input-text');
  $numbers = $text.find('.input-number');

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

  this._inputSubType = input.subType;

  // Disable equations preview by default.
  $textarea.find('textarea').off();
  switch (input.subType) {
    case 'numbers':
      // Hide textarea
      $textarea.hide();
      $numbers.html($(input.html));
      // Show numbers input
      $numbers.show();
      break;
    case 'canvas':
      $numbers.hide();
      $custom.html($(input.html));
      $custom.show();
      break;
    case 'equation':
      // If subtype is equation - enable preview.
      $textarea.find('textarea').writemaths({
          position:'center top',
          previewPosition: 'center top',
          of: this.equationPreview
      });
    default:
      // Show textarea
      $textarea.show();
      // Hide numbers input
      $numbers.hide();
      // Reset textarea size
      $textarea.find('textarea').val('').attr('rows', 1);
      break;
  }

  // Create new input based on type
  if(input.doWait === true) {
   /*
   * Cycle is HERE!
   */
   this._runWaitTimer(input);
   return;
  }

  if(input.type === 'text'){
   // Set input type
   this._inputType = 'text';

   // Set input url
   if(input.url) this._inputUrl = input.url;
   else throw new Error('CUI.ChatPresenter._setInput(): No input.url.');

   // Show text input
   $text.show();

   // Automatically increase the height of the textarea when new rows are added
   $textarea.find('textarea').expandingTextarea({maxRows: 10});
  } else if(input.type === 'options'){
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
  } else if(input.type === 'custom'){
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
  } else {
   // Throw an error if type is missing or invalid
   throw new Error('CUI.ChatPresenter._setInput(): Invalid input.type');
  }

  // Set the array of ids for messages that contains selectable elements
  if(input.includeSelectedValuesFromMessages) {
    this._messagesContainer.setSelectedValuesFromMessages(input.includeSelectedValuesFromMessages);
  } else {
    this._messagesContainer.setSelectedValuesFromMessages([]);
  }
  // Enable input
  this._inputIsEnabled = true;
};

/**
 * Get updates for a specified thread.
 * @param {jQuery} $thread - a jQuery object reference to a sidebar thread breakpoint element.
 */
CUI.ChatPresenter.prototype._getThreadUpdates = function($thread) {
  this._showThreadUpdates($thread.data('thread-id'));
  this._showMessagesUpToThread($thread.data('thread-id'));
};

/**
 * Show thread with updates.
 * @param {Number} threadId   - thread ID.
 */
CUI.ChatPresenter.prototype._showThreadUpdates = function(threadId) {
  this._isShowingMessagesUpToThread = true;
  this._updatesThreadId = threadId;
  this._requestMessages({
    url: this._updatesUrl + threadId + '/',
    parseUpdateMessages: true,
  });
};

/**
 * Inidicates that resources are unlocked.
 *
 * @returns {Boolean}
 */
CUI.ChatPresenter.prototype._resourcesAreUnlocked = function() {
  return $('section > .chat-sidebar-resources > .unlocked, section > .chat-sidebar-resources > .started').length > 0;
};

/**
 * On change thread button click handler.
 * @protected
 * @params {event} e
 */
function onChangeThreadButtonClickHandler(e){
  e.preventDefault();

  var $target = $(e.currentTarget)
  var targetType = $target.data('type');

  if (targetType === CUI.ChatBackToBreakpointButtonModel.ItemType.breakpoint) {
    this._showThreadMessages($(e.currentTarget).data('thread-id'));
  } else if (targetType === CUI.ChatBackToBreakpointButtonModel.ItemType.resource) {
    var threadId = $target.data('thread-id');
    var resourceInfo = this._sidebarResources.find(function(r) {
      return r.getInfo().threadId === threadId;
    }).getInfo();

    this._scrollToResourceMessage(
      resourceInfo.id,
      resourceInfo.threadId,
      true
    );
  }

}

/**
 * Attach a listener to handle the event when window scroll has stopped.
 * @protected
 */
CUI.ChatPresenter.prototype._addWindowScrollStoppedListener = function() {
  var $window = $(window);
  // move to class
  var scrollThreshold = 20;

  $window.on('scrollStopped',$.proxy(function() {
    var bottomScrollTop;
    if (this._isInUpdateThread) {
      bottomScrollTop = this._currentChatBottomMessageScrollTop;
    } else {
      bottomScrollTop = this._regularChatBottomMessageScrollTop;
    }

    var scrolledUp = $window.scrollTop() < bottomScrollTop - scrollThreshold;
    var scrolledDown = $window.scrollTop() > bottomScrollTop + scrollThreshold;

    if (scrolledUp) {
      this._inputContainer.threadNavBar.activateScrollToQuestion();
      this._inputContainer.threadNavBar.setDownArrow();
    } else {
      if (this._isInUpdateThread) {
        this._inputContainer.threadNavBar.activateThreadControls();
      } else {
        this._inputContainer.threadNavBar.hide();
      }

      if (scrolledDown) {
        this._inputContainer.threadNavBar.setUpArrow();
      }
    }
  }, this));
};

/**
 * Adds event listeners to the chat.
 * @protected
 */
CUI.ChatPresenter.prototype._addEventListeners = function(){

  this._addWindowScrollStoppedListener();

  // Sidebar toggle
  this._$sidebarToggle.on('click', $.proxy(function(e){
    e.preventDefault();
    $(e.currentTarget).toggleClass('active');

    this._toggleSidebar();
  }, this));


  // Sidebar toggle
    this._$sidebarToggle.one('resources', $.proxy(function(e){
      if(!this._isSidebarVisible){
        $(e.currentTarget).toggleClass('active');

        this._toggleSidebar();
      }
  }, this));


  // Fullscreen toggle
  this._$fullscreenToggle.on('click', $.proxy(function(e){
    e.preventDefault();
    this._toggleFullscreen();
  }, this));

  // Delegated event listeners for input options
  this._$inputContainer.find('.chat-input-options').on('click', '.chat-option', $.proxy(function(e){
    e.preventDefault();

    var $option = $(e.currentTarget);
    var optionText = $option.text();
    var optionValue = $option.data('option-value')

    switch (optionValue) {
      case "next_thread":
        if (this._isInUpdateThread) {
          //Show all messages and scroll to the last message (true);
          this._showSubsequentThreadMessages(true);
          // A workaround since there's a goodbye message that is
          // sent from the previous thread when we're scrolling to the last active one.
          this._scrollToNewMessageOnParsing = false;
          this._isInUpdateThread = false;
          this._regularChatBottomMessageScrollTop = this._currentChatBottomMessageScrollTop;
          this._inputContainer.threadNavBar.hide();
          this._flowPreviousThreadId = -1;
          this._$splitMessages.relatedMessages.length = 0;
          this._$splitMessages.subsequentMessages.length = 0;
          this._$splitMessages.relatedBreakpoints.length = 0;
          this._$splitMessages.subsequentBreakpoints.length = 0;
        }
        break;

      case "next_update":
        if (this._isInUpdateThread) {
          this._showSubsequentThreadMessages();
        }

        this._viewUpdatesPending = true;
        break;
    }

    // Post input to server
    this._postOption(optionValue);
  }, this));

  // Delegated events for sidebar breakpoint links
  this._$sidebarBreakpointsContainer.on('click', 'li', $.proxy(function(e){
    e.preventDefault();

    var $sidebarBreakpoint = $(e.currentTarget);

    // Show only related messages and Scroll to the topmost one
    // this._showThreadMessages($(e.currentTarget).data('thread-id'));
    if ($sidebarBreakpoint.data('updates-count') > 0) {
      /**
      * Comment for a white in case we need to return it back.
      * TODO: do not forget to remove it eventually
      this._getThreadUpdates($sidebarBreakpoint);
      */
    } else {
      //Scroll to messages, don't update scroll position and turn off scroll detection until new messages are loaded.
      this._scrollToMessage({id: $sidebarBreakpoint.data('first-message-id')});
    }
  }, this));

  // Delegated events for sidebar resources links
  this._$sidebarResourcesContainer.on('click', 'li', $.proxy(function(e){
    e.preventDefault();

    // Scroll to message
    var $sidebarResource = $(e.currentTarget);

    if ($sidebarResource.hasClass('started') || $sidebarResource.hasClass('unlocked')) {
      this._scrollToResourceMessage(
        $sidebarResource.data('first-message-id'),
        $sidebarResource.data('thread-id'),
      );
    }
  }, this));

  // Text input submit
  this._$inputContainer.find('.chat-input-text-form').on('submit', $.proxy(function(e){
    e.preventDefault();

    // Validate and post text to server
    this._postText();
  }, this)).on('keyup', $.proxy(function(e){
    // Enter should add a new line instead of submitting the form
    if(e.which === 13) {
      e.preventDefault()
    }
  }, this));

  // Previous thread button
  // this._$messagesContainer.on('click', '.chat-previous-thread', $.proxy(onChangeThreadButtonClickHandler, this));

  // Overflow actions
  this._$messagesContainer.on('click', '.chat-actions li', $.proxy(function(e){
    e.preventDefault();

    // Hide actions
    $(e.currentTarget).closest('ul').stop().fadeToggle();

    // Post action
    var action = $(e.currentTarget).data('action');
    this._postAction(action);
  }, this));

  this._inputContainer.setScrollToQuestionCallback($.proxy(function() {
    if (this._isInUpdateThread) {
      this._tweenWindowScroll(this._currentChatBottomMessageScrollTop)
    } else {
      this._setCurrentThreadId({
        threadId: this._messagesContainer.getAllMessageElements().last().data('thread-id')
      });
      this._updateCurrentSidebarBreakpoint();
      this._tweenWindowScroll(this._regularChatBottomMessageScrollTop);
    }
  }, this));

  this._inputContainer.setScrollToQuestionWithUpdatesCallback($.proxy(function() {
    this._showMessagesUpToThread(this._updatesThreadId);
  }, this));

  this._inputContainer.setShowSubsequentThreadsCallback($.proxy(function() {
    this._showSubsequentThreadMessages();
  }, this));

};