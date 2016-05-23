ChatUI
======================

Introduction
------------

ChatUI is an new UI to learn new materials using сhat-like UI.

Student can use two different ways to get to the Courselets using ChatUI:

    - using LTI
    - using direct link containing ``enroll_code``

By default LTI student will be redirected to new ChatUI.

Instructors can get direct link for Students with ``enroll_code`` from Courselets
page edit page.



Implementing handlers with DI
-----------------------------
Chat flow controlled by currently active ``handler``.

Each handler should be placed in ``chat.services.py`` and can be injected as
dependency based on different use cases.

To create new handler developer have to follow ``ProgressHandler`` interface -
need to subclass ``ProgressHandler`` class.


Chat API
--------
Backend API for ChatUI follow https://github.com/karlwho/cui API requirements.


Enable/Disable ChatUI feature for LTI
---------
By default all LTI request from Student should be redirected to new ChatUI.

But carefully test this new feature Enable/Disable switch was added to admin.

So now this redirect is disabled by default until active ``chat_ui`` switch will be
added in ``Admin -> Waffle -> Switches`` page.
