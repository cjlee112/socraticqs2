from browser import document, aio, ajax, window
from javascript import JSON

def copy_to_container(templateID, containerID, msgText=None, selector=None, handler=None, 
                      container=None, insertBeforeID=None, attrs=None, **kwargs):
    'clone a template, inject content, and append to container'
    template = document[templateID]
    message = template.cloneNode(True) # clone its full subtree including all descendants
    message.id = webfsm_id.__next__()
    if msgText:
        if selector:
            contentElement = message.select(selector)[0]
            contentElement.html = msgText
        else:
            message.html = msgText
    if handler:
        bind_event(handler, message, selector, **kwargs)
    if attrs:
        for k, v in attrs.items():
            message.attrs[k] = v
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
    l = []
    for t, m in chats: # inject chat messages
        l.append(copy_to_container(t, chatContainer, m, chatSelector, insertBeforeID=insertBeforeID)[0])
    return l


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
            insertBeforeID=None, postData={}, postURL='/chat/brella/messages', **kwargs):
        self.insertBeforeID = insertBeforeID
        self.msgElements = post_messages(chats, insertBeforeID=insertBeforeID)
        self.temporary = copy_to_container(responseTemplate, responseContainer, selector=selector,
                                            handler=self.handler, **kwargs)[0]
        self.outcome = self.message = None
        self.dataAttr = dataAttr
        self.postData = postData.copy()
        self.postURL =  postURL
        self.posted = {}
    def handler(self, ev):
        'called when user clicks Submit'
        if self.dataAttr:
            outcome = ev.target.attrs[self.dataAttr]
        else:
            outcome = 'continue'
        self.postData['outcome'] = outcome
        self.message = self.postData['message'] = ev.target.html
        if 'path' in self.postData: # no path means DO NOT POST
            self.send_post(self.postData)
        self.outcome = outcome # don't release lock until done
    def check_history(self, path, history):
        self.postData['path'] = path
        try:
            already = self.load_history(history[path])
            self.response = already
            return already
        except KeyError:
            return None
    def load_history(self, already):
        'stub for any processing needed of history dict'
        return already
    async def get(self, path, history=None, ignoreHistory=False):
        if history is None:
            history = {}
        if path: # no path means exclude from history mechanism
            already = self.check_history(path, history)
            if already and not ignoreHistory:
                self.close(already.get('message', ''))
                return already.get('outcome', None)
        await self.sleep_until_data()
        self.close(self.message)
        history.update(self.posted) # hand our POSTed messages back to history
        return self.outcome
    async def sleep_until_data(self, attr='outcome'):
        while getattr(self, attr, None) is None:
            await aio.sleep(1)
        return getattr(self, attr)
    def close(self, message=''):
        'display output message and clean up chat input area'
        if message:
            post_messages((("StudentMessageTemplate", message),),
                          insertBeforeID=self.insertBeforeID)
        if self.temporary:
            self.temporary.remove() # delete this element from the DOM
    def send_post(self, postData):
        'initiate AJAX POST to server'
        self.posted[postData['path']] = postData.copy()
        if postData.get('is_preview', False): # just instructor preview, so no Message sent!
            return
        self.response = None
        headers = {'Content-Type': 'application/json', 'X-CSRFToken': get_cookie('csrftoken')}
        req = ajax.Ajax()
        req.bind('complete', self.on_complete)
        req.open('POST', self.postURL, True)
        for h, v in headers.items():
            req.set_header(h, v)
        req.send(JSON.stringify(postData))
    async def get_server_response(self, attr):
        if self.postData.get('is_preview', False): # just instructor preview, so return fake ID
            return webfsm_id.__next__()
        return (await self.sleep_until_data('response'))[attr]
    def on_complete(self, req):
        self.response = JSON.parse(req.text)


async def continue_button(chats, path='continue', postData={}, history={}, **kwargs):
    query = ChatQuery(chats, 'continue-template', dataAttr=None, selector="button", postData=postData, **kwargs)
    await query.get(path, history)
    return query.msgElements # list of DOM elements output as chats

class ChatInput(ChatQuery):
    'prompt user with chat messages, then await get() to receive textarea'
    def __init__(self, chats, **kwargs):
        ChatQuery.__init__(self, chats, "chat-text-template", selector="form", event='submit', **kwargs)
    def handler(self, ev):
        ev.preventDefault() # block default form GET action
        outcome = self.message = self.temporary.select("textarea")[0].value
        self.postData['message'] = self.message
        self.send_post(self.postData)
        self.outcome = outcome # don't release lock until done

class ChatCanvas(ChatInput):
    'prompt user with chat canvas to draw on, then await get() to receive textarea'
    def __init__(self, question, svgID='drawsvgOutput', **kwargs):
        chats = (("ChatMessageTemplate", '<p>' + question['message'] + '</p>'),)
        ChatInput.__init__(self, chats, **kwargs)
        chatBubble = self.msgElements[0].select('.chat-bubble')[0]
        self.imageURL = question['canvas']['image']
        attrs = {'style': f"background-image: url({self.imageURL})"}
        self.canvas = copy_to_container('ChatCanvasTemplate', None, container=chatBubble, attrs=attrs)[0]
        window.start_drawsvg(self.canvas.id)
        self.svgID = svgID
    def load_history(self, already):
        already['message'] = f'<p>{already["message"]}</p>\n<div class="draw-svg-container" disabled="1" style="background-image: url({self.imageURL})">{already["canvasSVG"]}</div>'
        self.canvas.attrs['disabled'] = '1' # no more drawing allowed
        return already
    def handler(self, ev):
        outcome = self.temporary.select("textarea")[0].value
        svgData = document[self.svgID].value
        self.message = f'<p>{outcome}</p>\n<div class="draw-svg-container" disabled="1" style="background-image: url({self.imageURL})">{svgData}</div>'
        self.postData['message'] = outcome
        self.postData['canvasSVG'] = svgData
        self.send_post(self.postData)
        self.canvas.attrs['disabled'] = '1' # no more drawing allowed
        self.outcome = outcome # don't release lock until done




class MultiSelection(ChatQuery):
    'prompt user with chat messages, then await get() to receive multiple-selection'
    def __init__(self, chats, choices, listTemplate, choiceTemplate, listSelector=".chat-select-list", choiceSelector='h3',
                 choiceAttr='title', idAttr='ul_id', chatContainer="chatSection", insertBeforeID=None, **kwargs):
        post_messages(chats, insertBeforeID=insertBeforeID)
        msg = copy_to_container(listTemplate, chatContainer, insertBeforeID=insertBeforeID)[0]
        ChatQuery.__init__(self, (), "continue-template", selector="button", insertBeforeID=insertBeforeID, **kwargs)
        self.listID = msg.id
        self.container = msg.select(listSelector)[0]
        self.choices = choices
        self.idAttr = idAttr
        self.choiceTemplate = choiceTemplate
        self.choiceAttr = choiceAttr
        self.choiceSelector = choiceSelector
    def handler(self, ev):
        l = []
        for i, div in enumerate(document[self.listID].select('div.chat-check')):
            postData = self.postData.copy()
            if div.attrs['class'].find('chat-selectable-selected') >= 0:
                l.append(i)
                postData['outcome'] = 'yes'
            else:
                postData['outcome'] = 'no'
            if i in self.newChoices:
                postData[self.idAttr] = self.choices[i][self.idAttr]
                postData['path'] = self.paths[i]
                self.send_post(postData)
        self.outcome = l # don't release lock until done
    def toggle_choice(self, ev):
        div = ev.target
        if div.attrs['class'].find('chat-selectable-selected') >= 0:
            div.attrs['class'] = "chat-check chat-selectable"
        else:
            div.attrs['class'] = "chat-check chat-selectable  chat-selectable-selected"
    def check_history(self, path, history):
        newChoices = []
        l = []
        fullpaths = []
        for i,c in enumerate(self.choices):
            e = copy_to_container(self.choiceTemplate, None, c[self.choiceAttr], self.choiceSelector, container=self.container)[0]
            fullpath = f'{path}.{c[self.idAttr]}'
            fullpaths.append(fullpath)
            try:
                response = history[fullpath]
                setattr(self, f'response{i}', response)
                if response.get('outcome', '') == 'yes':
                    div = e.select('div.chat-check')[0]
                    div.attrs['class'] = "chat-check chat-selectable  chat-selectable-selected" # turn on check mark on this div
                    l.append(i)
            except KeyError:
                bind_event(self.toggle_choice, e, 'div')
                newChoices.append(i)
        self.paths = fullpaths
        if newChoices:
            self.newChoices = newChoices
            return None
        else:
            return dict(outcome=l)
    async def get_server_response(self, i, attr):
        if self.postData.get('is_preview', False): # just instructor preview, so return fake ID
            return webfsm_id.__next__()
        return (await self.sleep_until_data(f'response{i}'))[attr]
    def on_complete(self, req):
        response = JSON.parse(req.text)
        for i, c in enumerate(self.choices):
            if c[self.idAttr] == response[self.idAttr]:
                setattr(self, f'response{i}', response)
                return


def get_orct_query_ui(question, **kwargs):
    'return the proper query UI object for this subkind of ORCT'
    if 'canvas' in question:
        return ChatCanvas(question, **kwargs)
    else:
        return ChatInput(get_orct_instructor_chats(question), **kwargs)


def get_orct_instructor_chats(data, msgTemplate="ChatMessageTemplate"):
    'handle minor formatting issues like image embedding'
    if 'canvas' in data:
        if 'canvasURL' in data['canvas']:
            return ((msgTemplate, f'<p>{data["message"]}</p>\n<div class="draw-svg-container" disabled="1" style="background-image: url({data["canvas"]["image"]})"><div class="canvas-wrapper"><div class="canvas"><img src="{data["canvas"]["canvasURL"]}"></div></div></div>'),)
        else:
            return ((msgTemplate, f'<p>{data["message"]}</p>\n<div class="draw-svg-container" disabled="1" style="background-image: url({data["canvas"]["image"]})"><div class="canvas-wrapper"><div class="canvas">{data["canvas"]["canvasSVG"]}</div></div></div>'),)
    elif 'image' in data:
        return ((msgTemplate, f'<p>{data["message"]}</p>\n<img src="{data["image"]}">'),)
    else:
        return ((msgTemplate, data['message']),)


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


def get_cookie(attr):
    'extract specified cookie value from javascript'
    for s in window.document.cookie.split(';'):
        k, v = s.strip().split('=')
        if k == attr:
            return v
        


########### sidebar data
# sidebar thread class options
# "   unlocked   done  "
# "   unlocked    is-active "
# "    "

class SidebarThread(object):
    def __init__(self, title, thread_id, templateID='SidebarThreadTemplate', containerID='SidebarThreads'):
        self.thread_id = thread_id
        self.li = copy_to_container(templateID, containerID, title)[0]
        self.li.bind('click', self.handler)
        self.chatMsgID = None
    def set_status(self, status, chatMsgID=None):
        self.li.attrs['class'] = f"   unlocked   {status}  "
        if chatMsgID:
            self.chatMsgID = chatMsgID
    def set_count(self, count):
        self.li.attrs['data-updates-count'] = f"{count}"
    def handler(self, ev):
        'scroll this thread into view'
        if self.chatMsgID:
            e = document[self.chatMsgID]
            e.scrollIntoView({'block': "center"})


def set_on_sidebar(sidebar, thread_id, msgID=None, status='is-active'):
    if sidebar and thread_id in sidebar:
        sidebar[thread_id].set_status(status, msgID)


class SidebarToggler(object):
    def __init__(self, sidebarID='SidebarSection', togglerID='SidebarToggler', mainChatID='MainChatSection', inputbarID='ChatInputSection'):
        self.sidebarID = sidebarID
        self.togglerID = togglerID
        self.mainChatID = mainChatID
        self.inputbarID = inputbarID
        self.visible = False
        document[togglerID].bind('click', self.toggle)
    def toggle(self, ev):
        sidebar = document[self.sidebarID]
        toggler = document[self.togglerID]
        mainChat = document[self.mainChatID]
        inputbar = document[self.inputbarID]
        if self.visible:
            self.visible = False
            mainChat.attrs['style'] = "display: block; opacity: 1; padding-left: 0px;"
            sidebar.style.left = '-320px'
            toggler.attrs['class'] = 'sidebar-toggle'
            inputbar.attrs['style'] = "display: block; bottom: 0px; padding-left: 0px;"
        else:
            self.visible = True
            mainChat.attrs['style'] = "display: block; opacity: 1; padding-left: 320px;"
            sidebar.style.left = '0px'
            toggler.attrs['class'] = 'sidebar-toggle active'
            inputbar.attrs['style'] = "display: block; bottom: 0px; padding-left: 320px;"


################################################################
# distinct states:
# * pose a question, get response from chat-input-text
# * show text message, wait to Continue
# * request a choice via multiple-choice buttons
# * request a selection via multiple-selection list
