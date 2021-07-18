from browser import document, aio
import chat
from javascript import JSON

Responses = {}
UnitLessons = {}
FAQs = {}
StudentErrors = {}

def index_unitlessons(l):
    'cache these data in our UnitLessons'
    for d in l:
        UnitLessons[d['ul_id']] = d

def index_faqs(l):
    'cache these data in our FAQs'
    for d in l:
        FAQs[d['faq_id']] = d


async def main(insertBeforeID=None, endmsg=''):
    'basic ORCT chat test, starting with a simple updates test'
    chatInfo = await get_chat_info()
    sidebar = show_courselet_info(chatInfo)
    chat_id = chatInfo['chat_id']
    if chatInfo['is_preview']:
        sidebar.enable_all()
        chat.post_messages((("ChatMessageTemplate", 'In this Preview mode you can go to any lesson by clicking its title in the sidebar. (Click the menu button at bottom-left to open the sidebar).'),),
                           insertBeforeID=insertBeforeID)
    finalUpdates, oldThreads = await do_courselet(chat_id, chatInfo['is_preview'], sidebar, insertBeforeID)
    if finalUpdates:
        await offer_updates(finalUpdates, oldThreads, chat_id, insertBeforeID)
    sidebar.enable_all(makeVisible=True)
    if finalUpdates is not None: # actually reached the end of the courselet
        if sidebar.has_resources():
            endmsg = '  Please look over the follow-up resources in the side panel.'
        chat.post_messages((("ChatMessageTemplate", f'Good job! You have completed everything in this courselet.{endmsg}  You can always come back to review your history or start over to answer the questions again.  You can click the course link at top-left to return to the course overview.'),),
                           insertBeforeID=insertBeforeID)
    if sidebar.is_unfinished():
        await show_resources(chat_id, chatInfo['is_preview'], sidebar, insertBeforeID)


async def show_resources(chat_id, is_preview, sidebar, insertBeforeID=None):
    'allow the student to view additional resources after finishing the courselet'
    while True:
        thread_id = await sidebar.resource_clicked()
        t, postData, updateThreads = await get_thread(chat_id, thread_id=thread_id)
        await do_thread(t, postData, {}, is_preview, sidebar, insertBeforeID)
        if not sidebar.resourceNext:
            chat.post_messages((("ChatMessageTemplate", f'You completed this resource.  You can view other lessons by clicking in the sidebar at left, or click the course link at top-left to return to the course overview.'),),
                       insertBeforeID=insertBeforeID)


async def get_chat_info(apiURL='/chat/brella/chat'):
    headers = {'Content-Type': 'application/json'}
    req = await aio.get(apiURL, headers=headers)
    return JSON.parse(req.data)


def show_courselet_info(info, defaultImage='https://www.courselets.org/static/img/student/hero.jpg'):
    image = info['courselet'].get('image', None)
    if not image:
        image = defaultImage
    header = document.select('.course-header')[0]
    header.attrs['style'] = document['SidebarCover'].attrs['style'] = f"background-image: url({image})"
    document['CourseTitle'].html = document['SBCourseTitle'].html = info['course']['title']
    document['CourseURL'].attrs['href'] = document['SidebarCourseURL'].attrs['href'] = f"/lms/courses/{info['course']['course_id']}/"
    document['InstructorCredits'].html = ', '.join([d['name'] for d in info['course']['instructors']])
    document['CourseletTitle'].html = document['SBCourseletTitle'].html = info['courselet']['title']
    description = info['courselet'].get('description', None)
    if description:
        document['CourseletDescription'].html = description
    prereqs = info['courselet'].get('prereqs', None)
    if prereqs:
        document['CourseletPrereqs'].html = prereqs
    sidebar = chat.SidebarToggler()
    for t in info.get('threads', ()):
        sidebar.add_thread(t['title'], t['thread_id'])
    for t in info.get('resources', ()):
        sidebar.add_thread(t['title'], t['thread_id'], 'SidebarResTemplate', 'SidebarResources', isResource=True)
    return sidebar

async def get_thread(chat_id, completedThread=None, oldThreads=None, threadURL='/chat/brella/threads',
                     thread_id=None):
    params = dict(chat_id=chat_id)
    if completedThread is not None:
        params['completedThread'] = completedThread
    elif thread_id is not None:
        params['thread_id'] = thread_id
    headers = {'Content-Type': 'application/json'}
    req = await aio.get(threadURL, headers=headers, data=params)
    if req.status == 204:
        return None, None, None
    data = JSON.parse(req.data)
    if 'answer' in data:
        data['question']['answer_id'] = data['answer']['ul_id']
        index_unitlessons((data['question'], data['answer']))
        if 'faq_answers' in data['answer']:
            index_faqs(data['answer']['faq_answers'])
        if 'faqs' in data['answer']:
            index_faqs(data['answer']['faqs'])
        data['answer']['faq_answers'] = index_faq_answers(data['answer'])
    if 'errormodels' in data:
        index_unitlessons(data['errormodels'])
    if oldThreads and 'updates' in data:
        updateThreads = index_updates(data['updates'], oldThreads)
    else:
        updateThreads = None
    postData = create_post_data(data['chat_id'], data['thread_id'])
    return data, postData, updateThreads


def create_post_data(chat_id, thread_id):
    return dict(chat_id=chat_id, thread_id=thread_id)


def index_faq_answers(data):
    'index instructor answers by faq_id of FAQ they answer'
    faq_answers = {}
    for fd in data.get('faq_answers', ()):
        faq_answers[fd.get('parent_id', 0)] = fd
    return faq_answers


def index_updates(updates, oldThreads):
    updateThreads = {}
    for path, data in updates.items():
        thread_id = data['thread_id']
        try:
            if path.startswith('faqs.helpful.'):
                index_faqs((data,))
                if oldThreads[thread_id][path]['outcome'] == 'yes': # student wants to receive answer to this FAQ
                    updateThreads.setdefault(thread_id, {})[path] = data
            elif path not in oldThreads[thread_id]: # student has not yet seen this EM or FAQ
                updateThreads.setdefault(thread_id, {})[path] = data
                if path.startswith('faqs.'):
                    index_faqs((data,))
                elif path.startswith('errormodels.'):
                    index_unitlessons((data,))
        except KeyError:
            pass
    return updateThreads
            


async def do_courselet(chat_id, is_preview=False, sidebar=None, insertBeforeID=None):
    'complete a multi-thread courselet'
    oldThreads = {}
    finalUpdates = {}
    t, postData, updateThreads = await get_thread(chat_id)
    while t:
        await do_thread(t, postData, oldThreads, is_preview, sidebar, insertBeforeID)
        if is_preview and sidebar.resourceNext: # instructor clicked in sidebar, so exit lesson sequence
            return None, None # no updates in preview mode anyway!
        t, postData, updateThreads = await get_thread(chat_id, t['thread_id'], oldThreads)
        if updateThreads and not is_preview:
            showLater = await offer_updates(updateThreads, oldThreads, chat_id, insertBeforeID)
            for thread_id, updates in showLater.items(): # save for display at end of courselet
                finalUpdates.setdefault(thread_id, {}).update(updates)
    return finalUpdates, oldThreads


async def do_thread(t, postData, oldThreads, is_preview=False, sidebar=None, insertBeforeID=None):
    if is_preview: # mark postData to block all POST messages.  This is just instructor preview!!
        postData['is_preview'] = is_preview
    if t['kind'] == 'orct':
        wantsHelp, msgs = await do_orct_cycle(t, postData, t['history'], sidebar, insertBeforeID)
        if wantsHelp:
            t['history']['insertBeforeID'] = msgs[0].id
            oldThreads[t['thread_id']] = t['history'] # student wants more help on this thread
    else:
        await show_explanation(t, postData, t['history'], sidebar, insertBeforeID)
    sidebar.set_on_sidebar(t['thread_id'], status='done')


async def do_orct_cycle(mainThread, postData, history, sidebar, insertBeforeID=None):
    'perform basic ORCT chat cycle on one thread'
    postDataQ = postData.copy()
    postDataQ['ul_id'] = mainThread['question']['ul_id'] # POST messages will be about this question
    await pose_orct(mainThread, postDataQ, history, sidebar, insertBeforeID)
    s = await get_selfeval(mainThread['answer'], postDataQ, history, insertBeforeID)
    stati = ()
    if s != 'same':
        errmods = mainThread.get('errormodels', ())
        if errmods:
            stati += await offer_errmods(errmods, postDataQ, history, insertBeforeID)
        postDataA = postData.copy()
        postDataA['ul_id'] = mainThread['answer']['ul_id'] # POST messages will be about this answer
        faqs = mainThread['answer'].get('faqs', ())
        if faqs:
            stati += await offer_faqs(faqs, mainThread['answer'].get('faq_answers', {}), postDataA, history, insertBeforeID)
        if len(stati) == 0:
            stati += (await get_status((("ChatMessageTemplate", "How well do you feel you understand now? If you need more clarification, tell us."),),
                                       'status', postDataQ, history, insertBeforeID),)
        if 'help' in stati:
            await solicit_faq(postDataA, history, insertBeforeID=insertBeforeID)
    msgs = await chat.continue_button((("ChatMessageTemplate", "You've completed this question!  Let's continue to the next lesson."),),
                                      path='done', postData=postData, history=history, insertBeforeID=insertBeforeID)
    return ('help' in stati), msgs


async def show_explanation(e, postData, history, sidebar, insertBeforeID=None):
    'display explanation message with Continue button'
    postData['ul_id'] = e['ul_id']
    msgs = chat.post_messages((("ChatBreakpointTemplate", e['title']),),
                              chatSelector='span', insertBeforeID=insertBeforeID)
    sidebar.set_on_sidebar(e['thread_id'], msgs[0].id)
    await chat.continue_button(chat.get_orct_instructor_chats(e),
                               path='done', postData=postData, history=history,
                               insertBeforeID=insertBeforeID)


async def pose_orct(orct, postData, history, sidebar, insertBeforeID=None):
    'ask question, student responds, gives confidence level'
    msgs = chat.post_messages((("ChatBreakpointTemplate", orct['title']),),
                              chatSelector='span', insertBeforeID=insertBeforeID)
    sidebar.set_on_sidebar(orct['thread_id'], msgs[0].id)
    query = chat.get_orct_query_ui(orct['question'], postData=postData, insertBeforeID=insertBeforeID)
    await query.get('response', history)
    postData['response_id'] = await query.get_server_response('response_id')
    query = chat.ChatQuery((("ChatMessageTemplate", None),), 'chat-options-template', postData=postData, insertBeforeID=insertBeforeID)
    return await query.get('confidence', history)



async def get_selfeval(answer, postData, history, insertBeforeID=None):
    'get student self-evaluation of whether their answer was right'
    query = chat.ChatQuery(chat.get_orct_instructor_chats(answer) +
                           (("ChatMessageTemplate", 'How close was your answer to the one shown here? '),),
                           'selfeval-options-template', postData=postData, insertBeforeID=insertBeforeID)
    return await query.get('selfeval', history)



async def offer_errmods(errmods, postData, history, insertBeforeID=None,
                        chats=(("ChatMessageTemplate", "Here are the most common blindspots people reported when comparing their answer vs. the correct answer. Check the box(es) that seem relevant to your answer (if any)."),),
                        messageStamp=''):
    'let student select Error Models to view'
    query = chat.MultiSelection(chats, errmods, "em-list-template", "em-choice-template", postData=postData, insertBeforeID=insertBeforeID)
    ems = await query.get('errormodels', history)
    stati = ()
    for i in ems:
        postData2 = postData.copy()
        postData2['student_error_id'] = await query.get_server_response(i, 'student_error_id')
        stati += (await show_em(errmods[i], postData2, history, insertBeforeID, messageStamp),)
    return stati


async def show_em(em, postData, history, insertBeforeID=None, messageStamp=''):
    'show error model and get student status'
    if 'image' in em:
        s = f'<b>RE: {em["title"]}</b><br>{em["message"]}<br><img src="{em["image"]}"> {messageStamp}'
    else:
        s = f'<b>RE: {em["title"]}</b><br>{em["message"]} {messageStamp}'
    return await get_status((('faq-a1', s),
                         ("ChatMessageTemplate", f"We hope this explanation helped you.  How well do you feel you understand this blindspot now? If you need more clarifications, tell us. {messageStamp}")),
                            f'errormodels.status.{em["ul_id"]}', postData, history, insertBeforeID, messageStamp)


async def get_status(chats, path, postData, history, insertBeforeID=None, messageStamp=''):
    status = await chat.ChatQuery(chats, 'status-options-template', postData=postData, insertBeforeID=insertBeforeID).get(path, history)
    if status == 'help':
        chat.post_messages((("ChatMessageTemplate", f"We will try to provide more explanation for this. {messageStamp}"),),
                           insertBeforeID=insertBeforeID)
    return status



async def offer_faqs(faqlist, faq_answers, postData, history, insertBeforeID=None):
    'let student select FAQs to view or create a new FAQ'
    chats = (("ChatMessageTemplate", "Would any of the following questions help you? Select the one(s) you wish to view."),)
    query = chat.MultiSelection(chats, faqlist, "faq-list-template", "faq-choice-template",
                                postData=postData, idAttr='faq_id', insertBeforeID=insertBeforeID)
    faqs = await query.get('faqs', history)
    stati = ()
    for i in faqs:
        stati += await show_faq(faqlist[i], faq_answers, postData, history, insertBeforeID)
    return stati


async def solicit_faq(postData, history, prefix='answer', insertBeforeID=None, messageStamp='', ignoreHistory=False):
    query = chat.ChatQuery((("ChatMessageTemplate", f"Is there anything else you're wondering about, where you'd like clarification or something you're unsure about this point? {messageStamp}"),),
                           'yesno-template', postData=postData, insertBeforeID=insertBeforeID)
    hasQuestion = await query.get(f'{prefix}.solicit_faq', history, ignoreHistory)
    if hasQuestion == 'yes':
        await create_new_faq(postData, history, prefix, insertBeforeID, messageStamp, ignoreHistory)


async def show_faq(faq, faq_answers, postData, history, insertBeforeID=None):
    'show full question and option to view answer'
    postData2 = postData.copy()
    postData2['faq_id'] = faq_id = faq["faq_id"]
    query = chat.ChatQuery((("FaqMessageTemplate", f'<b>{faq["title"]}</b><br>{faq["message"]}'),
                            ("ChatMessageTemplate", "Would the answer to this student question help you?")),
                           'yesno-template', postData=postData2, insertBeforeID=insertBeforeID)
    helpful = await query.get(f'faqs.helpful.{faq_id}', history)
    if helpful == 'yes' and faq_id in faq_answers:
        postData2['inquiry_id'] = await query.get_server_response('inquiry_id')
        return (await show_faq_answer(faq_id, faq_answers[faq_id], postData2, history, insertBeforeID),)
    return () # empty tuple means no status info


async def show_faq_answer(faq_id, answer, postData, history, insertBeforeID=None):
    'show answer and ask status'
    return await get_status((('faq-a1', f'<b>{answer["title"]}</b><br>{answer["message"]}'), 
                             ("ChatMessageTemplate", "How well do you feel you understand now? If you need more clarification, tell us.")),
                            f'faqs.status.{faq_id}', postData, history, insertBeforeID)


async def create_new_faq(postData, history, prefix='answer', insertBeforeID=None, messageStamp='', ignoreHistory=False):
    'student writes a new FAQ question'
    query = chat.ChatInput((("ChatMessageTemplate", f"First, write your question as a single sentence, as clearly and simply as you can. (You'll have a chance to explain your question fully in the next step). {messageStamp}"),),
                           postData=postData, insertBeforeID=insertBeforeID)
    title = await query.get(f'{prefix}.add_faq', history, ignoreHistory)
    postData['faq_id'] = await query.get_server_response('faq_id')
    query = chat.ChatInput((("ChatMessageTemplate", f"Next, try saying a bit more about exactly what you're unsure of, such as a simple example where you can think of two possible answers but you're not sure which one is actually right. {messageStamp}"),), 
                           postData=postData, insertBeforeID=insertBeforeID)
    text = await query.get(f'{prefix}.add_faq_text', history, ignoreHistory)
    chat.post_messages((("ChatMessageTemplate", f"We'll try to get you an answer to this. {messageStamp}"),),
                       insertBeforeID=insertBeforeID)


async def offer_updates(updateThreads, historyThreads, chat_id, insertBeforeID=None, **kwargs):
    'offer student updates for any threads that have new updates'
    showLater = {}
    for thread_id, updates in updateThreads.items():
        wantUpdates = await offer_update(thread_id, updates, insertBeforeID)
        if wantUpdates == 'yes':
            insertBeforeID = historyThreads[thread_id]['insertBeforeID']
            toggler = chat.HistoryToggle(insertBeforeID)
            await show_updates(updates, historyThreads[thread_id], chat_id, thread_id, insertBeforeID, **kwargs)
            toggler.close()
        else:
            showLater[thread_id] = updates
    return showLater


async def offer_update(thread_id, updates, insertBeforeID=None):
    'let student view or skip display of updates'
    question = UnitLessons[thread_id]
    return await chat.ChatQuery((("ChatMessageTemplate", f"I have posted new messages to help you in the thread '{question['title']}'. Would you like to view these updates now?<BR><BR><i>If you don't want to view them now, I'll ask you again once you have completed this courselet.</i>"),),
                        'yesno-template', insertBeforeID=insertBeforeID).get(None) # no path means do not record in message history


async def show_updates(updates, history, chat_id, thread_id, insertBeforeID, messageStamp='<span class="chat-new-msg">new</span>'):
    'present updates for a specific thread'
    postData = create_post_data(chat_id, thread_id)
    postDataQ = postData.copy()
    postDataQ['response_id'] = history['confidence']['response_id'] # needed for creating new StudentError records
    stati = ()
    errmods = [updates[path] for path in updates if path.startswith('errormodels.')]
    if errmods:
        chats = (("ChatMessageTemplate", f"I've added explanations for some new blindspot(s) that caused people trouble on this question. Check any box(es) that seem relevant to what you were thinking. {messageStamp}"),)
        stati += await offer_errmods(errmods, postDataQ, history, chats=chats, insertBeforeID=insertBeforeID, messageStamp=messageStamp)
    faq_answers = [updates[path] for path in updates if path.startswith('faqs.helpful.')]
    for answer in faq_answers:
        faq = FAQs[answer['parent_id']]
        postDataA = postData.copy()
        try:
            postDataA['inquiry_id'] = history[f'faqs.status.{faq["faq_id"]}']["inquiry_id"] # needed for saving new status
        except KeyError: # unusual case: if FAQ authored by this student, no need for inquiry_id
            postDataA['faq_id'] = faq['faq_id'] # needed for saving new status
        stati += (await get_status((("ChatMessageTemplate", f"Below is my answer to the question you raised RE: the following issue {messageStamp}"),    
                        ("FaqMessageTemplate", f'<b>{faq["title"]}</b><br>{faq["message"]}'),
                        ("ChatMessageTemplate", f'<b>{answer["title"]}</b><br>{answer["message"]} {messageStamp}'),
                        ("ChatMessageTemplate", f'How well do you feel you understand now? If you need more clarification, tell us. {messageStamp}')),
                        f'faqs.status.{answer["faq_id"]}', postDataA, history, insertBeforeID, messageStamp),)
    if len(stati) == 0:
        stati += (await get_status((("ChatMessageTemplate", f"How well do you feel you understand now? If you need more clarification, tell us. {messageStamp}"),),
                                   'update.status', postDataQ, history, insertBeforeID, messageStamp),)
    if 'help' in stati:
        postDataA = postData.copy()
        postDataA['ul_id'] = UnitLessons[thread_id]['answer_id'] # needed for creating new FAQ
        await solicit_faq(postDataA, history, 'update', insertBeforeID, messageStamp, ignoreHistory=True)
    await chat.continue_button((("ChatMessageTemplate", f'You have completed all updates for this thread. {messageStamp}'),),
                               path=None, postData=postData, history=history, insertBeforeID=insertBeforeID)


aio.run(main())

