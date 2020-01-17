/**
 * @file Defines the class CUI.ChatMessageContainerPresenter
 */

CUI = CUI || {};

/**
 * Represents the chat message container.
 * @class
 * @param {selectors} - selectors to base the container on.
 * @param {selectors.rootSelector} - a selector for the root node.
 *
 * @returns {CUI.ChatMessagesContainerPresnter}
 */
CUI.ChatMessagesContainerPresnter = function (selectors) {
    selectors = selectors || {};

    if (!selectors.rootSelector) {
        selectors.rootSelector = '.chat-messages';
    }

    /**
     * Root node.
     * @public
     * @type {jQuery}
     */
    this.$root = $(selectors.rootSelector);

    /**
     * Chat messages.
     * @public
     * @type {Object<Number, ChatMessageModel|ChatMediaModel|ChatBreakpointModel>}
     */
    this.messages = new Object();

    /**
     * Ordered storage for chat messages.
     * @private
     * @type {Array.<Number, ChatMessageModel|ChatMediaModel|ChatBreakpointModel>}
     */
    this._orderedMessages = new Array();

    /**
     * Chat breakpoints.
     * @public
     * @type {Object<Number, ChatBreakpointModel>}
     */
    this.breakpoints = new Object();

    /**
     * Ordered storage for chat breakpoints.
     * @public
     * @type {Array.<ChatBreakpointModel>}
     */
    this._orderedBreakpoints = new Array();

    /**
     * Selected values for messages.
     * @private
     * @type {Array.<Number>}
     */
    this._selectedValuesFromMessages = new Array();

    return this;
};

/**
 * {CUI.ChatMessageContainerPresenter} static namespace.
 */
CUI.ChatMessagesContainerPresnter.selectors = {
    /**
     *
     * @param {Object} params - an object to create selector params from.
     */
    toSelectorParams: function (params) {
        var selectorParams = '';

        Object.keys(params).forEach(function (paramName) {
            selectorParams += " " + paramName + '="' + params[paramName] + '"';
        });

        if (selectorParams !== '') {
            selectorParams = '[' + selectorParams + ']';
        }

        return selectorParams;
    },

    /**
     *
     * @param {Number} id - message id
     * @param {Number} threadId - thread id
     */
    message: function (id, threadId) {
        var selector = '.chat-message'
        var params = new Object();

        if (id) {
            params['data-message-id'] = id;
        }

        if (threadId) {
            params['data-thread-id'] = threadId;
        }

        selector += CUI.ChatMessagesContainerPresnter.selectors.toSelectorParams(params);

        return selector;
    },

    /**
     *
     * @param {Number} threadId - thread id.
     */
    breakpoint: function (threadId) {
        var selector = '.chat-breakpoint';
        var params = new Object();

        if (threadId) {
            params['data-thread-id'] = threadId;
        }

        selector += CUI.ChatMessagesContainerPresnter.selectors.toSelectorParams(params);

        return selector;
    }
};

/**
 * Sets _selectedValuesFromMessages value.
 * @public
 */
CUI.ChatMessagesContainerPresnter.prototype.setSelectedValuesFromMessages = function (value) {
    this._selectedValuesFromMessages = value;
};

/**
 * Returns a list of all chat breakoint jQuery objects.
 * @public
 * @returns {Array.<jQuery>}
 */
CUI.ChatMessagesContainerPresnter.prototype.findBreakpoints = function () {
    return this.$root.find(CUI.ChatMessagesContainerPresnter.selectors.breakpoint());
};

/**
 * Returns a list of all chat message jQuery objects.
 * @public
 * @returns {Array.<jQuery>}
 */
CUI.ChatMessagesContainerPresnter.prototype.findMessages = function () {
    return this.$root.find(CUi.ChatMessagesContainerPresnter.selectors.message());
};

/**
 * Adds a message to the chat.
 * @public
 * @param {ChatMessageModel,ChatMediaModel,ChatBreakpointModel} model - a model to create the a new message from.
 */
CUI.ChatMessagesContainerPresnter.prototype.addMessage = function (model) {
    var message;

    // A tmeporary workaround, since sometimes backend tends to send a 'null' thread id
    // after you visit a thread with updates while having an active input in your current thread
    if (!model.threadId) {
        model.threadId = this.findBreakpoints().last().data('thread-id');
        console.log('Model has no threadId, will use instaed: ', model.threadId);
    }

    // Create a message presenter based on model type
    if (model instanceof CUI.ChatMessageModel) {
        message = new CUI.ChatMessagePresenter(model);
    } else if (model instanceof CUI.ChatMediaModel) {
        message = new CUI.ChatMediaPresenter(model);
    } else if (model instanceof CUI.ChatBreakpointModel) {
        message = new CUI.ChatBreakpointPresenter(model);
    } else {
        throw new Error("CUI.ChatMessagesContainerPresnter.addMessage(): Invalid model.");
    }

    var $messageElement = message.$el;

    // Add message to chat
    var messageThreadId = message._model.threadId;

    // If it's a breakpoint
    if (message instanceof CUI.ChatBreakpointPresenter) {
        var threadBreakpointSelector = CUI.ChatMessagesContainerPresnter.selectors.breakpoint(messageThreadId);
        var $threadBreakpoint = this.$root.find(threadBreakpointSelector);

        // And it's a new one, then add it
        if ($threadBreakpoint.length === 0) {
            this.$root.append($messageElement);
        } else {
            $messageElement = null;
        }
    } else {
        var threadMessagesSelector = CUI.ChatMessagesContainerPresnter.selectors.message(null, messageThreadId);
        var threadMessages = this.$root.find(threadMessagesSelector);

        //If it's not the first message of a thread, then add it after the last one
        if (threadMessages.length > 0) {
            var $lastThreadMessage = threadMessages[threadMessages.length - 1];
            $messageElement.insertAfter($lastThreadMessage);
        } else {
            this.$root.append($messageElement);
        }
    }

    // If messageElement is still present (means it's valid).
    if ($messageElement) {
        // Save a reference to the message
        this.messages[model.id] = message;
        this._orderedMessages.push(message);

        // this._messagesByThread[model.threadId] = this._messagesByThread[model.threadId] || {};
        // this._messagesByThread[model.threadId][model.id] = message;
    }

    return $messageElement;
};

/**
 * Updates a message in the chat.
 * @protected
 * @param {ChatMessageModel|ChatMediaModel|ChatBreakpointModel} model   - The new model for the message.
 */
CUI.ChatMessagesContainerPresnter.prototype.updateMessage = function (model) {
    var currentMessage;

    // Select existing message
    currentMessage = this.messages[model.id];

    // Update message
    if (currentMessage) {
        currentMessage.update(model);
    } else {
        throw new Error('CUI.ChatMessagesContainerPresnter.prototype.updateMessage(): Message with id "' + model.id + '" does not exist.');
    }
};

/**
 * Removes message. (FOR COMPATIBILITY, IS POSSIBLY ABSOLETE, REQUIRES INVESITAGTION)
 */
CUI.ChatMessagesContainerPresnter.prototype.removeMessage = function (id) {
    var currentMessage = this.messages[id];

    if (currentMessage) {
        var messageOrderIndex = this._orderedMessages.indexOf(currentMessage);
        this._orderedMessages.splice(messageOrderIndex, 1);

        currentMessage.destroy();
    }

    return Boolean(currentMessage)
};

/**
 * Finds selected values within messages.
 * @protected
 * @returns {object}
 */
CUI.ChatMessagesContainerPresnter.prototype.getMessageSelectedValues = function () {
    var selected = {};

    // Loop through messages with selectables and look for selected elements
    $.each(this._selectedValuesFromMessages, $.proxy(function (i, messageID) {
        var $message;
        var $selectedSelectables;

        // Check that the message exists in the DOM
        if (this.messages[messageID]) {
            $message = this.messages[messageID].$el;

            // Find selected elements in message
            $selectedSelectables = $message.find('.chat-selectable.chat-selectable-selected, .chat-selectable:checked');

            // Add selected values to selected array
            if ($selectedSelectables.length) {
                $.each($selectedSelectables, function (ii, s) {
                    var $selectable = $(s);
                    var attribute = $selectable.data('selectable-attribute');
                    var value = $selectable.data('selectable-value');

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
 * Returns a message by it's id.
 * @public
 * @returns {Number} id - message id.
 */
CUI.ChatMessagesContainerPresnter.prototype.getMessage = function (id) {
    return this.messages[id];
};

/**
 * Gets a list of all chat elements (messages, breakpoints).
 * @public
 * @returns {Array.<jQuery>}
 */
CUI.ChatMessagesContainerPresnter.prototype.getAllMessageElements = function () {
    var allElementsSelector = CUI.ChatMessagesContainerPresnter.selectors.message();
    allElementsSelector += ',' + CUI.ChatMessagesContainerPresnter.selectors.breakpoint();

    return this.$root.find(allElementsSelector);
};

/**
 * Get all messages relate to an array of threadIds.
 * @private
 * @param {Array<Number>} threads - an array of thread ids to get messages for.
 * @returns {Array} - an array of all related messages.
 */
CUI.ChatMessagesContainerPresnter.prototype.getThreadsRelatedMessages = function (threads) {
    var relatedMessages = new Array();

    threads.forEach($.proxy(function (threadId) {
        console.log('Messages for threadId: ', threadId);
        var threadMesssagesSelector = CUI.ChatMessagesContainerPresnter.selectors.message(null, threadId);
        var threadMessages = this.$root.find(threadMesssagesSelector);

        if (threadMessages.length) {
            relatedMessages = relatedMessages.concat(threadMessages);
        }
    }, this));

    return relatedMessages;
};

/**
 * Gets all chat breakpoints related to each of the threadIds in the provided array.
 * @private
 * @param {Array<Number>} threads - an array of thread ids to get messages for.
 * @returns {Array} - an array of all related chat breakpoints.
 */
CUI.ChatMessagesContainerPresnter.prototype.getThreadsRelatedChatBreakpoints = function (threads) {
    var relatedChatBreakpoints = new Array();

    threads.forEach($.proxy(function (threadId) {
        var threadBreakpointsSelector = CUI.ChatMessagesContainerPresnter.selectors.breakpoint(threadId);
        var $threadChatBreakpoint = this.$root.find(threadBreakpointsSelector).first();

        if ($threadChatBreakpoint.length) {
            relatedChatBreakpoints.push($threadChatBreakpoint);
        }
    }, this));

    return relatedChatBreakpoints;
};