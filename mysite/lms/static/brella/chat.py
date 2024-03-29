from browser import document, aio, ajax, window, alert
from javascript import JSON

def copy_to_container(templateID, containerID, msgText=None, selector=None, handler=None, 
                      container=None, insertBeforeID=None, attrs=None, attrSelector=None, **kwargs):
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
        if attrSelector:
            contentElement = message.select(attrSelector)[0]
        else:
            contentElement = message
        for k, v in attrs.items():
            contentElement.attrs[k] = v
    if not container:
        container = document[containerID]
    if insertBeforeID: # insert at this specific location
        container.insertBefore(message, document[insertBeforeID])
    else:
        container <= message # append to container's children
    try:
        window.mathjax_on_element(message.id)
    except AttributeError: # if no mathjax support, just ignore
        pass
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

def set_target_attr(parent, selector, attr, value):
    'find a single target within parent, and set an attribute'
    for target in parent.select(selector):
        target.attrs[attr] = value
        return target

def bind_event(func, d=document, selector='button[data-option-value]', event='click', data=None):
    for button in d.select(selector):
        button.bind(event, func)
        if data:
            for k, v in data.items():
                button.attrs[k] = v

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
            insertBeforeID=None, postData={}, postURL='/chat/brella/messages', blankPolicy='allow', **kwargs):
        self.insertBeforeID = insertBeforeID
        self.msgElements = post_messages(chats, insertBeforeID=insertBeforeID)
        if self.msgElements:
            self.scrollToElement = self.msgElements[-1] # ensure last chat message is visible
        self.temporary = copy_to_container(responseTemplate, responseContainer, selector=selector,
                                            handler=self.handler, **kwargs)[0]
        self.outcome = self.message = None
        self.dataAttr = dataAttr
        self.postData = postData.copy()
        self.postURL =  postURL
        self.posted = {}
        self.blankPolicy = blankPolicy
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
    async def get(self, path, history=None, ignoreHistory=False, showInChat=True):
        if history is None:
            history = {}
        if path: # no path means exclude from history mechanism
            already = self.check_history(path, history)
            if already and not ignoreHistory:
                self.close(already.get('message', ''), showInChat)
                return already.get('outcome', None)
        await self.sleep_until_data()
        self.close(self.message, showInChat) # display as chat message
        history.update(self.posted) # hand our POSTed messages back to history
        return self.outcome
    async def sleep_until_data(self, attr='outcome'):
        while getattr(self, attr, None) is None:
            await aio.sleep(1)
            if getattr(self, 'scrollToElement', False): # make sure message actually visible!
                self.scrollToElement.scrollIntoView()
                self.scrollToElement = False
        return getattr(self, attr)
    def close(self, message='', showInChat=True):
        'display output message and clean up chat input area'
        if showInChat and message:
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
        begin_post(self.postURL, postData, self.on_complete)
    async def get_server_response(self, attr):
        if self.postData.get('is_preview', False): # just instructor preview, so return fake ID
            return webfsm_id.__next__()
        return (await self.sleep_until_data('response'))[attr]
    def on_complete(self, req):
        self.response = JSON.parse(req.text)

def begin_post(url, data, func=None, headers=None, action='POST'):
    'initiate AJAX POST'
    if not headers:
        headers = {'Content-Type': 'application/json', 'X-CSRFToken': get_cookie('csrftoken')}
    req = ajax.Ajax()
    if func:
        req.bind('complete', func)
    req.open(action, url, True)
    for h, v in headers.items():
        req.set_header(h, v)
    req.send(JSON.stringify(data))
    return req

async def continue_button(chats, path='continue', postData={}, history=None, **kwargs):
    query = ChatQuery(chats, 'continue-template', dataAttr=None, selector="button", postData=postData, **kwargs)
    await query.get(path, history, showInChat=False)
    return query.msgElements # list of DOM elements output as chats

class ChatInput(ChatQuery):
    'prompt user with chat messages, then await get() to receive textarea'
    def __init__(self, chats, **kwargs):
        ChatQuery.__init__(self, chats, "chat-text-template", selector="form", event='submit', **kwargs)
    def handler(self, ev):
        ev.preventDefault() # block default form GET action
        outcome = self.temporary.select("textarea")[0].value
        isBlank = (outcome.strip() == '')
        if self.blankPolicy == 'reject' and isBlank: # refuse to accept blank submission
            return
        self.postData['message'] = self.message = outcome
        if 'path' in self.postData and (not isBlank or self.blankPolicy != 'no-post'): # no path means DO NOT POST
            self.send_post(self.postData)
        self.outcome = outcome # don't release lock until done

class ChatCanvas(ChatInput):
    'prompt user with chat canvas to draw on, then await get() to receive textarea'
    def __init__(self, question, svgID='drawsvgOutput', **kwargs):
        chats = (("ChatMessageTemplate", '<p>' + question['message'] + '</p>'),)
        ChatInput.__init__(self, chats, **kwargs)
        chatBubble = self.msgElements[0].select('.chat-bubble')[0]
        self.imageURL = question['canvas']['image']
        self.canvas = copy_to_container('ChatCanvasTemplate', None, container=chatBubble)[0]
        window.start_drawsvg(self.canvas.id)
        e = self.canvas.select('.canvas')[0]
        e.attrs['style'] = f"position: relative;top: 40px;background-image: url({self.imageURL});background-size: contain;background-repeat: no-repeat;background-position: top left;"
        self.svgID = svgID
    def load_history(self, already):
        drawSVGdiv = get_disabled_draw_svg_div(self.imageURL)
        already['message'] = f'<p>{already["message"]}</p>\n{drawSVGdiv}{already["canvasSVG"]}</div>'
        self.canvas.attrs['disabled'] = '1' # no more drawing allowed
        return already
    def handler(self, ev):
        ev.preventDefault() # block default form GET action
        outcome = self.temporary.select("textarea")[0].value
        svgData = document[self.svgID].value
        drawSVGdiv = get_disabled_draw_svg_div(self.imageURL)
        self.message = f'<p>{outcome}</p>\n{drawSVGdiv}{svgData}</div>'
        self.postData['message'] = outcome
        self.postData['canvasSVG'] = svgData
        if 'path' in self.postData: # no path means DO NOT POST
            self.send_post(self.postData)
        self.canvas.attrs['disabled'] = '1' # no more drawing allowed
        self.canvas.style.display = 'none' # will be shown instead in message bubble
        self.outcome = outcome # don't release lock until done




class MultipleChoice(ChatQuery):
    'prompt user with chat messages, then await get() to receive chosen value'
    def __init__(self, chats, choices, listTemplate="em-list-template", choiceTemplate='multiple-choice-template',
                 listSelector=".chat-select-list", choiceSelector='.multiple-choice-item',
                 choiceAttr='text', chatContainer="chatSection", insertBeforeID=None, **kwargs):
        post_messages(chats, insertBeforeID=insertBeforeID)
        msg = copy_to_container(listTemplate, chatContainer, insertBeforeID=insertBeforeID)[0]
        ChatQuery.__init__(self, (), "continue-template", selector="button", insertBeforeID=insertBeforeID, **kwargs)
        self.listID = msg.id
        self.container = msg.select(listSelector)[0]
        self.chosen = None
        self.choiceSelector = choiceSelector
        self.choices = choices
        self.choiceAttr = choiceAttr
        for i,c in enumerate(choices):
            itemHtml = self.format_choice(c, choiceAttr)
            e = copy_to_container(choiceTemplate, None, itemHtml, choiceSelector, container=self.container)[0]
            e.bind('click', self.set_choice)
            e.attrs['data-selectable-value'] = str(i)
    def format_choice(self, c, textAttr='text', imageAttr='image'):
        if imageAttr in c:
            if textAttr in c:
                return f'<img class="chat-mc-img" src="{c[imageAttr]}">{c[textAttr]}'
            else:
                return f'<div class="chat-image-choice" style="background-image: url({c[imageAttr]});"></div>'
        else:
            return f'<h3>{c[textAttr]}</h3>'
    def set_choice(self, ev):
        'user clicked one of the choices'
        div = ev.currentTarget
        if self.chosen != div: # user made a new, different choice
            set_target_attr(div, '.chat-check', 'class', 
                            "chat-check chat-selectable  chat-selectable-selected")
            if self.chosen: # un-check the previous choice
                set_target_attr(self.chosen, '.chat-check', 'class', "chat-check chat-selectable")
            self.chosen = div
    def handler(self, ev):
        'send chosen index value as outcome'
        if not self.chosen: # user hasn't made a choice
            return
        outcome = int(self.chosen.attrs['data-selectable-value'])
        self.postData['outcome'] = outcome
        self.message = self.postData['message'] = self.format_choice(self.choices[outcome])
        if 'path' in self.postData: # no path means DO NOT POST
            self.send_post(self.postData)
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
                div.unbind('click') # deactivate toggle response
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

def get_disabled_draw_svg_div(imageURL):
    return f'<div class="draw-svg-container" disabled="1" style="background-image: url({imageURL});background-size: contain;background-repeat: no-repeat;background-position: top left;">'


def get_orct_instructor_chats(data, msgTemplate="ChatMessageTemplate"):
    'handle minor formatting issues like image embedding'
    if 'canvas' in data:
        drawSVGdiv = get_disabled_draw_svg_div(data["canvas"]["image"])
        if 'canvasURL' in data['canvas']:
            return ((msgTemplate, f'<p>{data["message"]}</p>\n{drawSVGdiv}<div class="canvas-wrapper"><div class="canvas"><img src="{data["canvas"]["canvasURL"]}"></div></div></div>'),)
        else:
            return ((msgTemplate, f'<p>{data["message"]}</p>\n{drawSVGdiv}<div class="canvas-wrapper"><div class="canvas">{data["canvas"]["canvasSVG"]}</div></div></div>'),)
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
# "   unlocked   available  "
# "    "

class SidebarThread(object):
    def __init__(self, sidebar, title, thread_id, templateID='SidebarThreadTemplate', containerID='SidebarThreads',
                 isResource=False):
        self.thread_id = thread_id
        self.li = copy_to_container(templateID, containerID, title)[0]
        self.li.bind('click', self.handler)
        self.chatMsgID = None
        self.isResource = isResource
        self.sidebar = sidebar
        self.status = None
    def set_status(self, status, chatMsgID=None):
        self.status = status
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
        else:
            self.sidebar.set_next_resource(self.thread_id)




class SidebarToggler(object):
    def __init__(self, sidebarID='SidebarSection', togglerID='SidebarToggler', mainChatID='MainChatSection', inputbarID='ChatInputSection', resourcesID='SidebarResources'):
        self.sidebarID = sidebarID
        self.togglerID = togglerID
        self.mainChatID = mainChatID
        self.inputbarID = inputbarID
        self.resourcesID = resourcesID
        self.visible = False
        self.threads = {}
        self.resourceNext = None
        self.resourceDefer = True
        document[togglerID].bind('click', self.toggle)
    def add_thread(self, title, thread_id, *args, **kwargs):
        self.threads[thread_id] = SidebarThread(self, title, thread_id, *args, **kwargs)
    def set_on_sidebar(self, thread_id, msgID=None, status='is-active'):
        if thread_id in self.threads:
            self.threads[thread_id].set_status(status, msgID)
    def advance_chat_thread(self, chatThread, postData, ul_id=None, insertBeforeID=None):
        'show in sidebar and chat that we are starting a new thread'
        msgs = post_messages((("ChatBreakpointTemplate", chatThread['title']),),
                             chatSelector='span', insertBeforeID=insertBeforeID)
        self.set_on_sidebar(chatThread['thread_id'], msgs[0].id)
        postData = postData.copy() # leave postData from caller unchanged, to avoid side effects
        if ul_id is None:
            ul_id = chatThread['ul_id']
        postData['ul_id'] = ul_id
        return postData
    def set_next_resource(self, thread_id):
        self.resourceNext = thread_id
        if self.resourceDefer:
            alert('This lesson will be shown after you complete the current lesson.')
    def enable_all(self, makeVisible=False):
        for st in self.threads.values():
            if not st.status: # still locked, so unlock
                st.set_status('available')
        if makeVisible and not self.visible: # show sidebar so resources are visible to click
            self.toggle()
    def has_resources(self):
        for st in self.threads.values():
            if st.isResource:
                return True
    def is_unfinished(self):
        for st in self.threads.values():
            if not st.chatMsgID:
                return True
    def toggle(self, ev=None):
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
    async def resource_clicked(self):
        self.resourceDefer = False
        while not self.resourceNext:
            await aio.sleep(1)
        thread_id = self.resourceNext
        self.resourceNext = None
        self.resourceDefer = True
        return thread_id


################################################################
# distinct states:
# * pose a question, get response from chat-input-text
# * show text message, wait to Continue
# * request a choice via multiple-choice buttons
# * request a selection via multiple-selection list


#####################################################################
# Named View UI for displaying tables

class NamedViewTableUI(object):
    def __init__(self, apiURL, namedViews, initialView=None, containerID="StudentResponses",
                 templateID="ResponseRowTemplate", menuID='NamedViewMenu',
                 viewMoreID='ViewMoreTrigger', loadingID='LoadInProgress'):
        self.apiURL = apiURL
        self.namedViews = namedViews
        self.containerID = containerID
        self.templateID = templateID
        self.menuID = menuID
        self.viewMoreID = viewMoreID
        self.loadingID = loadingID
        set_visibility(viewMoreID, False)
        document[viewMoreID].bind('click', self.get_more)
        s = ''
        for k,v in namedViews.items():
            if k == initialView:
                s += f'<option value="{k}" selected>{v["title"]}</option>\n'
            else:
                s += f'<option value="{k}">{v["title"]}</option>\n'
        menu = document[menuID]
        menu.html = s
        menu.bind('change', self.begin_view)
        if initialView:
            self.begin_view(None, initialView)
    def begin_view(self, ev, viewName=None):
        if not viewName:
            viewName = document[self.menuID].value
        self.viewName = viewName
        v = self.namedViews[viewName]
        document[self.containerID].clear()
        self.get_data(self.apiURL, v['params'])
    def get_data(self, apiURL=None, params=None, headers={'Content-Type': 'application/json'}):
        set_visibility(self.loadingID)
        set_visibility(self.viewMoreID, False)
        req = ajax.Ajax()
        req.bind('complete', self.on_complete)
        if apiURL:
            params = params.copy()
            params['namedView'] = self.viewName
            url = apiURL + '?' + '&'.join([f'{t[0]}={t[1]}' for t in params.items()])
        else:
            url = self.nextURL
        req.open('GET', url, True)
        for h, v in headers.items():
            req.set_header(h, v)
        req.send()
    def on_complete(self, req):
        tranche = JSON.parse(req.text)
        self.nextURL = tranche.get('next', None)
        fmt = self.namedViews[self.viewName]['formatter']
        for row in tranche['results']:
            copy_to_container(self.templateID, self.containerID, fmt(row), None)
        set_visibility(self.loadingID, False)
        if self.nextURL:
            set_visibility(self.viewMoreID)
    def get_more(self, ev):
        'user clicked View More, so get next page of results'
        if self.nextURL:
            self.get_data()
    def toggle_item(self, ev):
        pass

def time_since_fmt(secsPast):
    'pretty-print timedelta seconds in the simplest time unit'
    secsPast = float(secsPast)
    if secsPast >= 2 * 31536000:
        return f'{int(secsPast / 31536000)} years ago' 
    elif secsPast >= 5270400:
        return f'{int(secsPast / 2592000)} months ago' 
    elif secsPast >= 1209600:
        return f'{int(secsPast / 604800)} weeks ago'
    elif secsPast >= 2 * 86400:
        return f'{int(secsPast / 86400)} days ago'
    elif secsPast >= 2 * 3600:
        return f'{int(secsPast / 3600)} hours ago'
    elif secsPast >= 2 * 60:
        return f'{int(secsPast / 60)} minutes ago'
    else:
        return f'{int(secsPast)} seconds ago'


#####################################################################
# paginated GET support

async def get_all_pages(url, params):
    headers = {'Content-Type': 'application/json'}
    req = await aio.get(url, headers=headers, data=params)
    results = []
    while req:
        tranche = JSON.parse(req.data)
        results += tranche['results']
        nextURL = tranche.get('next', None)
        if nextURL:
            req = await aio.get(nextURL, headers=headers)
        else:
            req = None
    return results


def load_new_page(exitURL):
    'force this browser window to load a whole new page'
    window.location.assign(exitURL)


