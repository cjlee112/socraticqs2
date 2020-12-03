from browser import aio
import chat
import json

async def main(threadURL='faqdemo.json', insertBeforeID=None):
    'basic ORCT chat cycle, starting with a simple updates test'
    scenario = chat.DemoScenario() # activate demo Start button
    req = await aio.get(threadURL)
    threadData = json.loads(req.data)
    await offer_updates(update_test, threadData['updates'], 'TestAfterPoint')
    mainThread = threadData['main']
    if scenario.scenarios['NoEMscenaro']:
        errmods = []
    else:
        errmods = chat.filter_by_kind(mainThread, 'errormodel')
    if scenario.scenarios['NoFAQscenaro']:
        faqs = []
    else:
        faqs = chat.filter_by_kind(mainThread, 'faq')
    await show_explanations(chat.filter_by_kind(mainThread, 'intro'), insertBeforeID)
    s = await pose_orct(chat.filter_by_kind(mainThread, 'orct')[0], insertBeforeID)
    stati = ()
    if s != 'same':
        if errmods:
            stati += await offer_errmods(errmods, insertBeforeID)
        if faqs:
            stati += await offer_faqs(faqs, insertBeforeID)
        if len(stati) == 0:
            stati += (await get_status((("ChatMessageTemplate", "How well do you feel you understand now? If you need more clarification, tell us."),),
                                       insertBeforeID),)
        if 'help' in stati:
            await solicit_faq(insertBeforeID)
    await chat.continue_button((("ChatMessageTemplate", "You've completed this question!  Let's continue to the next lesson."),),
                       insertBeforeID=insertBeforeID)

async def show_explanations(explanations, insertBeforeID=None):
    'display explanation message(s) one at a time with Continue button'
    for e in explanations:
        chat.post_messages((("ChatBreakpointTemplate", e['title']),),
                           chatSelector='span', insertBeforeID=insertBeforeID)
        await chat.continue_button((("ChatMessageTemplate", e['message']),),
                                   insertBeforeID=insertBeforeID)


async def pose_orct(orct, insertBeforeID=None):
    'ask question, student responds, self-evaluates answer'
    chat.post_messages((("ChatBreakpointTemplate", orct['title']),),
                       chatSelector='span', insertBeforeID=insertBeforeID)
    await chat.ChatInput((("ChatMessageTemplate", orct['question']),), insertBeforeID=insertBeforeID).get()
    await chat.ChatQuery((("ChatMessageTemplate", None),), 'chat-options-template', insertBeforeID=insertBeforeID).get()
    return await chat.ChatQuery((("ChatMessageTemplate", orct['answer']), ("ChatMessageTemplate", 'How close was your answer to the one shown here? '),),
                             'selfeval-options-template', insertBeforeID=insertBeforeID).get()




async def offer_errmods(errmods, insertBeforeID=None,
                        chats=(("ChatMessageTemplate", "Here are the most common blindspots people reported when comparing their answer vs. the correct answer. Check the box(es) that seem relevant to your answer (if any)."),),
                        messageStamp=''):
    'let student select Error Models to view'
    ems = await chat.MultiSelection(chats, errmods, "em-list-template", "em-choice-template", insertBeforeID=insertBeforeID).get()
    stati = ()
    for i in ems:
        stati += (await show_em(errmods[i], insertBeforeID, messageStamp),)
    return stati


async def show_em(em, insertBeforeID=None, messageStamp=''):
    'show error model and get student status'
    return await get_status((('faq-a1', f'<b>RE: {em["title"]}</b><br>{em["message"]} {messageStamp}'),
                         ("ChatMessageTemplate", f"We hope this explanation helped you.  How well do you feel you understand this blindspot now? If you need more clarifications, tell us. {messageStamp}")),
                            insertBeforeID, messageStamp)

async def get_status(chats, insertBeforeID=None, messageStamp=''):
    status = await chat.ChatQuery(chats, 'status-options-template', insertBeforeID=insertBeforeID).get()
    if status == 'help':
        chat.post_messages((("ChatMessageTemplate", f"We will try to provide more explanation for this. {messageStamp}"),),
                           insertBeforeID=insertBeforeID)
    return status



async def offer_faqs(faqlist, insertBeforeID=None):
    'let student select FAQs to view or create a new FAQ'
    chats = (("ChatMessageTemplate", "Would any of the following questions help you? Select the one(s) you wish to view."),)
    faqs = await chat.MultiSelection(chats, faqlist, "faq-list-template", "faq-choice-template", insertBeforeID=insertBeforeID).get()
    stati = ()
    for i in faqs:
        stati += await show_faq(faqlist[i], insertBeforeID)
    return stati

async def solicit_faq(insertBeforeID=None):
    hasQuestion = await chat.ChatQuery((("ChatMessageTemplate", "Is there anything else you're wondering about, where you'd like clarification or something you're unsure about this point?"),),
                        'yesno-template', insertBeforeID=insertBeforeID).get()
    if hasQuestion == 'yes':
        await create_new_faq(insertBeforeID)


async def show_faq(faq, insertBeforeID=None):
    'show full question and option to view answer'
    helpful = await chat.ChatQuery((("FaqMessageTemplate", f'<b>{faq["title"]}</b><br>{faq["question"]}'),
                     ("ChatMessageTemplate", "Would the answer to this student question help you?")), 'yesno-template', insertBeforeID=insertBeforeID).get()
    if helpful == 'yes' and 'answer' in faq:
        return (await show_faq_answer(faq['answer'], insertBeforeID),)
    return () # empty tuple means no status info


async def show_faq_answer(answer, insertBeforeID=None):
    'show answer and ask status'
    return await get_status((('faq-a1', answer), ("ChatMessageTemplate", "How well do you feel you understand now? If you need more clarification, tell us.")),
                            insertBeforeID)


async def create_new_faq(insertBeforeID=None, messageStamp=''):
    'student writes a new FAQ question'
    title = await chat.ChatInput((("ChatMessageTemplate", f"First, write your question as a single sentence, as clearly and simply as you can. (You'll have a chance to explain your question fully in the next step). {messageStamp}"),), insertBeforeID=insertBeforeID).get()
    text = await chat.ChatInput((("ChatMessageTemplate", f"Next, try saying a bit more about exactly what you're unsure of, such as a simple example where you can think of two possible answers but you're not sure which one is actually right. {messageStamp}"),), insertBeforeID=insertBeforeID).get()
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


async def update_test(updates, insertBeforeID, messageStamp='<span class="chat-new-msg">new</span>'):
    'a trivial test of display a simple'
    stati = ()
    errmods = chat.filter_by_kind(updates, 'errormodel')
    if errmods:
        chats = (("ChatMessageTemplate", f"I've added explanations for some new blindspot(s) that caused people trouble on this question. Check any box(es) that seem relevant to what you were thinking. {messageStamp}"),)
        stati += await offer_errmods(errmods, chats=chats, insertBeforeID=insertBeforeID, messageStamp=messageStamp)
    for faq in chat.filter_by_kind(updates, 'faq'):
        stati += (await get_status((("ChatMessageTemplate", f"Below is my answer to the question you raised RE: the following issue {messageStamp}"),    
                        ("FaqMessageTemplate", f'<b>{faq["title"]}</b><br>{faq["question"]}'),
                        ("ChatMessageTemplate", f'{faq["answer"]} {messageStamp}'),
                        ("ChatMessageTemplate", f'How well do you feel you understand now? If you need more clarification, tell us. {messageStamp}')),
                        insertBeforeID, messageStamp),)
    if len(stati) == 0:
        stati += (await get_status((("ChatMessageTemplate", f"How well do you feel you understand now? If you need more clarification, tell us. {messageStamp}"),),
                                   insertBeforeID, messageStamp),)
    if 'help' in stati:
        hasQuestion = await chat.ChatQuery((("ChatMessageTemplate", f"Is there anything else you're wondering about, where you'd like clarification or something you're unsure about this point? {messageStamp}"),),
                        'yesno-template', insertBeforeID=insertBeforeID).get()
        if hasQuestion == 'yes':
            await create_new_faq(insertBeforeID, messageStamp=messageStamp)
    await chat.continue_button((("ChatMessageTemplate", f'You have completed all updates for this thread. Click on Continue below to view your next thread "Efficiency Concerns: When to Include an ORCT?". {messageStamp}'),),
                       insertBeforeID=insertBeforeID)


aio.run(main())

