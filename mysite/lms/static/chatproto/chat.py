from browser import document, aio

def copy_to_container(templateID, containerID, msgText=None, selector=None, handler=None, 
                      container=None, insertBeforeID=None, **kwargs):
    'clone a template, inject content, and append to container'
    template = document[templateID]
    message = template.cloneNode(True) # clone its full subtree including all descendants
    message.id = webfsm_id.__next__()
    if msgText:
        contentElement = message.select(selector)[0]
        contentElement.html = msgText
    if handler:
        bind_event(handler, message, selector, **kwargs)
    if not container:
        container = document[containerID]
    if insertBeforeID: # insert at this specific location
        container.insertBefore(message, document[insertBeforeID])
    else:
        container <= message # append to container's children
    document.scrollingElement.scrollTop = document.scrollingElement.scrollHeight # scroll to bottom
    return message, container

def post_messages(chats, chatContainer="chatSection", chatSelector='.chat-bubble',
                    insertBeforeID=None):
    'post one or more messages to the chat'
    for t, m in chats: # inject chat messages
        copy_to_container(t, chatContainer, m, chatSelector, insertBeforeID=insertBeforeID)


def set_visibility(targetID, visible=True, displayStyle='block'):
    'show or hide a specific DOM container'
    target = document[targetID]
    if visible:
        target.style.display = displayStyle
    else:
        target.style.display = 'none'

def bind_event(func, d=document, selector='button[data-option-value]', event='click'):
    for button in d.select(selector):
        button.bind(event, func)

def generate_id(stemFormat='webfsm%d'):
    'generate unique IDs for webfsm DOM elements'
    i = 1
    while True:
        yield stemFormat % (i,)
        i += 1

webfsm_id = generate_id() # get iterator

def filter_by_kind(messages, kind):
    return [d for d in messages if d['kind'] == kind]

############################################################

class ChatQuery(object):
    'prompt user with chat messages, then await get() to receive button click'
    def __init__(self, chats, responseTemplate="chat-options-template", responseContainer="chat-input-container",
            dataAttr='data-option-value', selector='button[data-option-value]',
            insertBeforeID=None):
        self.insertBeforeID = insertBeforeID
        post_messages(chats, insertBeforeID=insertBeforeID)
        self.temporary = copy_to_container(responseTemplate, responseContainer, selector=selector,
                                            handler=self.handler)[0]
        self.outcome = self.message = None
        self.dataAttr = dataAttr
    def handler(self, ev):
        if self.dataAttr:
            self.outcome = ev.target.attrs[self.dataAttr]
        else:
            self.outcome = 'continue'
        self.message = ev.target.html
    async def get(self):
        while True:
            await aio.sleep(1)
            if self.outcome is not None:
                self.close()
                return self.outcome
    def close(self):
        if self.message:
            post_messages((("StudentMessageTemplate", self.message),),
                          insertBeforeID=self.insertBeforeID)
        if self.temporary:
            self.temporary.remove() # delete this element from the DOM


async def continue_button(chats, **kwargs):
    return await ChatQuery(chats, 'continue-template', dataAttr=None, selector="button", **kwargs).get()

class ChatInput(ChatQuery):
    'prompt user with chat messages, then await get() to receive textarea'
    def __init__(self, chats, **kwargs):
        ChatQuery.__init__(self, chats, "chat-text-template", selector="button", **kwargs)
    def handler(self, ev):
        self.outcome = self.message = self.temporary.select("textarea")[0].value

class MultiSelection(ChatQuery):
    'prompt user with chat messages, then await get() to receive multiple-selection'
    def __init__(self, chats, choices, listTemplate, choiceTemplate, listSelector=".chat-select-list", choiceSelector='h3',
                 choiceAttr='title', chatContainer="chatSection", insertBeforeID=None, **kwargs):
        post_messages(chats, insertBeforeID=insertBeforeID)
        msg = copy_to_container(listTemplate, chatContainer, insertBeforeID=insertBeforeID)[0]
        container = msg.select(listSelector)[0]
        for c in choices:
            e = copy_to_container(choiceTemplate, None, c[choiceAttr], choiceSelector, container=container)[0]
            bind_event(self.toggle_choice, e, 'div')
        ChatQuery.__init__(self, (), "continue-template", selector="button", insertBeforeID=insertBeforeID, **kwargs)
        self.listID = msg.id
    def handler(self, ev):
        l = []
        for i, div in enumerate(document[self.listID].select('div.chat-check')):
            if div.attrs['class'].find('chat-selectable-selected') >= 0:
                l.append(i)
        self.outcome = l
    def toggle_choice(self, ev):
        div = ev.target
        if div.attrs['class'].find('chat-selectable-selected') >= 0:
            div.attrs['class'] = "chat-check chat-selectable"
        else:
            div.attrs['class'] = "chat-check chat-selectable  chat-selectable-selected"


class HistoryToggle(object):
    def __init__(self, insertBeforeID, updateFlagger='UpdateFlagger', updateToggler='UpdateToggler'):
        self.target = document[insertBeforeID]
        self.controller = document[updateFlagger]
        self.msgToggler = document[updateToggler]
        set_visibility(updateFlagger)
        self.set_toggle()
        bind_event(self.handler, selector='#' + updateToggler)
    def handler(self, ev):
        self.set_toggle(not self.visible)
    def set_toggle(self, visible=False):
        if visible:
            self.msgToggler.text = '↑ Hide Subsequent Threads'
            self.target.scrollIntoView({'block': "center"})
            #document.scrollingElement.scrollTop = document.scrollingElement.scrollHeight # scroll to bottom
        else:
            self.msgToggler.text = '↓ Show Subsequent Threads'
        self.visible = visible
        container = self.target.parent
        toggle = False
        for c in container.children:
            if c.id == self.target.id:
                toggle = True
            if toggle:
                set_visibility(c.id, visible)
    def close(self):
        set_visibility(self.controller.id, False)
        self.set_toggle(True)


class DemoScenario(object):
    def __init__(self, formID='DemoScenarios', showIDs=('chatSection', 'ChatInputSection'),
                 buttonSelector='button', checkboxSelector='input'):
        self.formID = formID
        self.showIDs = showIDs
        self.checkboxSelector = checkboxSelector
        self.scenarios = {}
        self.show(True)
        bind_event(self.start, document[formID], buttonSelector)
    def start(self, ev):
        for e in document[self.formID].select(self.checkboxSelector):
            self.scenarios[e.id] = e.checked
        self.show(False)
        ev.target.unbind('click')
    def show(self, visible=True):
        set_visibility(self.formID, visible)
        for targetID in self.showIDs:
            set_visibility(targetID, not visible)

        


################################################################
# distinct states:
# * pose a question, get response from chat-input-text
# * show text message, wait to Continue
# * request a choice via multiple-choice buttons
# * request a selection via multiple-selection list
