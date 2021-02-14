from browser import aio
import chat
from javascript import JSON

async def main(chat_id=10, insertBeforeID=None):
    'basic ORCT chat test, starting with a simple updates test'
    await do_courselet(chat_id, insertBeforeID)

async def get_thread(chat_id, completedThread=None, threadURL='/chat/brella/threads'):
    params = dict(chat_id=chat_id)
    if completedThread is not None:
        params['completedThread'] = completedThread
    headers = {'Content-Type': 'application/json'}
    req = await aio.get(threadURL, headers=headers, data=params)
    data = JSON.parse(req.data)
    postData = dict(chat_id=data['chat_id'], thread_id=data['thread_id'])
    return data, postData



async def do_courselet(chat_id, insertBeforeID=None):
    'complete a multi-thread courselet'
    t, postData = await get_thread(chat_id)
    while t:
        if t['kind'] == 'base':
            await show_explanation(t, postData, t['history'], insertBeforeID)
        elif t['kind'] == 'orct':
            await do_orct_cycle(t, postData, t['history'], insertBeforeID)
        t, postData = await get_thread(chat_id, t['thread_id'])


async def do_orct_cycle(mainThread, postData, history, insertBeforeID=None):
    'perform basic ORCT chat cycle on one thread'
    errmods = mainThread.get('errormodels', ())
    faqs = mainThread['answer'].get('faqs', ())
    s = await pose_orct(mainThread, postData, history, insertBeforeID)
    s = await get_selfeval(mainThread['answer'], postData, history, insertBeforeID)
    if s != 'same':
        stati = ()
        if errmods:
            stati += await offer_errmods(errmods, postData, history, insertBeforeID)
        if faqs:
            stati += await offer_faqs(faqs, postData, history, insertBeforeID)
        if len(stati) == 0:
            stati += (await get_status((("ChatMessageTemplate", "How well do you feel you understand now? If you need more clarification, tell us."),),
                                       'status', postData, history, insertBeforeID),)
        if 'help' in stati:
            await solicit_faq(postData, history, insertBeforeID=insertBeforeID)
    await chat.continue_button((("ChatMessageTemplate", "You've completed this question!  Let's continue to the next lesson."),),
                       path='done', postData=postData, history=history, insertBeforeID=insertBeforeID)


async def show_explanation(e, postData, history, insertBeforeID=None):
    'display explanation message with Continue button'
    chat.post_messages((("ChatBreakpointTemplate", e['title']),),
                           chatSelector='span', insertBeforeID=insertBeforeID)
    await chat.continue_button(chat.get_orct_instructor_chats(e),
                               path='done', postData=postData, history=history,
                               insertBeforeID=insertBeforeID)


async def pose_orct(orct, postData, history, insertBeforeID=None):
    'ask question, student responds, gives confidence level'
    postData['ul_id'] = orct['question']['ul_id']
    chat.post_messages((("ChatBreakpointTemplate", orct['title']),),
                       chatSelector='span', insertBeforeID=insertBeforeID)
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
    return await get_status((('faq-a1', f'<b>RE: {em["title"]}</b><br>{em["message"]} {messageStamp}'),
                         ("ChatMessageTemplate", f"We hope this explanation helped you.  How well do you feel you understand this blindspot now? If you need more clarifications, tell us. {messageStamp}")),
                            f'errormodels.status.{em["ul_id"]}', postData, history, insertBeforeID, messageStamp)


async def get_status(chats, path, postData, history, insertBeforeID=None, messageStamp=''):
    status = await chat.ChatQuery(chats, 'status-options-template', postData=postData, insertBeforeID=insertBeforeID).get(path, history)
    if status == 'help':
        chat.post_messages((("ChatMessageTemplate", f"We will try to provide more explanation for this. {messageStamp}"),),
                           insertBeforeID=insertBeforeID)
    return status



async def offer_faqs(faqlist, postData, history, insertBeforeID=None):
    'let student select FAQs to view or create a new FAQ'
    chats = (("ChatMessageTemplate", "Would any of the following questions help you? Select the one(s) you wish to view."),)
    query = chat.MultiSelection(chats, faqlist, "faq-list-template", "faq-choice-template",
                                postData=postData, idAttr='faq_id', insertBeforeID=insertBeforeID)
    faqs = await query.get('answer.faqs', history)
    stati = ()
    for i in faqs:
        stati += await show_faq(faqlist[i], postData, history, insertBeforeID)
    return stati


async def solicit_faq(postData, history, prefix='answer', insertBeforeID=None):
    query = chat.ChatQuery((("ChatMessageTemplate", "Is there anything else you're wondering about, where you'd like clarification or something you're unsure about this point?"),),
                           'yesno-template', postData=postData, insertBeforeID=insertBeforeID)
    hasQuestion = await query.get(f'{prefix}.solicit_faq', history)
    if hasQuestion == 'yes':
        await create_new_faq(postData, history, insertBeforeID)


async def show_faq(faq, postData, history, insertBeforeID=None):
    'show full question and option to view answer'
    query = chat.ChatQuery((("FaqMessageTemplate", f'<b>{faq["title"]}</b><br>{faq["question"]}'),
                            ("ChatMessageTemplate", "Would the answer to this student question help you?")),
                           'yesno-template', postData=postData, insertBeforeID=insertBeforeID)
    helpful = await query.get(f'faqs.helpful.{faq["faq_id"]}', history)
    if helpful == 'yes' and 'answer' in faq:
        return (await show_faq_answer(faq, postData, history, insertBeforeID),)
    return () # empty tuple means no status info


async def show_faq_answer(faq, postData, history, insertBeforeID=None):
    'show answer and ask status'
    return await get_status((('faq-a1', f'<b>{faq["answerTitle"]}</b><br>{faq["answer"]}'), 
                             ("ChatMessageTemplate", "How well do you feel you understand now? If you need more clarification, tell us.")),
                            f'faqs.status.{faq["faq_id"]}', postData, history, insertBeforeID)


async def create_new_faq(postData, history, insertBeforeID=None, messageStamp=''):
    'student writes a new FAQ question'
    query = chat.ChatInput((("ChatMessageTemplate", f"First, write your question as a single sentence, as clearly and simply as you can. (You'll have a chance to explain your question fully in the next step). {messageStamp}"),),
                           postData=postData, insertBeforeID=insertBeforeID)
    title = await query.get('answer.add_faq', history)
    query = chat.ChatInput((("ChatMessageTemplate", f"Next, try saying a bit more about exactly what you're unsure of, such as a simple example where you can think of two possible answers but you're not sure which one is actually right. {messageStamp}"),), 
                           postData=postData, insertBeforeID=insertBeforeID)
    text = await query.get('answer.add_faq_text', history)
    chat.post_messages((("ChatMessageTemplate", f"We'll try to get you an answer to this. {messageStamp}"),),
                       insertBeforeID=insertBeforeID)



async def offer_updates(updateFunc, updates, insertBeforeID, **kwargs):
    'let student view or skip display of updates'
    wantUpdates = await chat.ChatQuery((("ChatMessageTemplate", '''You have completed this thread. I have posted new messages to help you in the thread "Active Learning Approaches for Conceptual Understanding?". Would you like to view these updates now?<BR><BR><i>If you don't want to view them now, I'll ask you again once you have completed your next thread.</i>'''),),
                        'yesno-template').get()
    if wantUpdates != 'yes':
        return
    toggler = chat.HistoryToggle(insertBeforeID)
    await updateFunc(updates, insertBeforeID, **kwargs)
    toggler.close()


async def update_test(updates, postData, history, insertBeforeID, messageStamp='<span class="chat-new-msg">new</span>'):
    'a trivial test of display a simple'
    stati = ()
    errmods = chat.filter_by_kind(updates, 'errormodel')
    if errmods:
        chats = (("ChatMessageTemplate", f"I've added explanations for some new blindspot(s) that caused people trouble on this question. Check any box(es) that seem relevant to what you were thinking. {messageStamp}"),)
        stati += await offer_errmods(errmods, postData, history, chats=chats, insertBeforeID=insertBeforeID, messageStamp=messageStamp)
    for faq in chat.filter_by_kind(updates, 'faq'):
        stati += (await get_status((("ChatMessageTemplate", f"Below is my answer to the question you raised RE: the following issue {messageStamp}"),    
                        ("FaqMessageTemplate", f'<b>{faq["title"]}</b><br>{faq["question"]}'),
                        ("ChatMessageTemplate", f'<b>{faq["answerTitle"]}</b><br>{faq["answer"]} {messageStamp}'),
                        ("ChatMessageTemplate", f'How well do you feel you understand now? If you need more clarification, tell us. {messageStamp}')),
                        f'faqs.status.{faq["faq_id"]}', postData, history, insertBeforeID, messageStamp),)
    if len(stati) == 0:
        stati += (await get_status((("ChatMessageTemplate", f"How well do you feel you understand now? If you need more clarification, tell us. {messageStamp}"),),
                                   'update.status', postData, history, insertBeforeID, messageStamp),)
    if 'help' in stati:
        await solicit_faq(postData, history, prefix='update', insertBeforeID=insertBeforeID)
    await chat.continue_button((("ChatMessageTemplate", f'You have completed all updates for this thread. Click on Continue below to view your next thread "Efficiency Concerns: When to Include an ORCT?". {messageStamp}'),),
                       path='update.done', postData=postData, history=history, insertBeforeID=insertBeforeID)


aio.run(main())

