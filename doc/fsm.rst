====================================================
Writing Guided Activities (Finite State Machines)
====================================================

What is a Guided Activity?
---------------------------

A guided activity is a series of steps that guides a user through
a process in a specified way.  Some examples:

* a *lesson sequence*: presents the lessons in a courselet to
  the student one at a time, in order, while minimizing distractions
  from the rest of the generic courselets interface.

* a *live session*: an instructor presents a series of exercises
  to students in a classroom.  The whole class does the exercises
  at the same time, synchronized by what the instructor chooses,
  in real-time.

* a *randomized trial* protocol: two distinct ways of teaching
  the same thing are defined as "treatments".  A randomized
  trial randomizes students to either one treatment or the other,
  and compares their learning gains.  Note that this depends
  strongly on controlling exactly what sequence of materials
  each student gets shown, according to the "treatment" they
  were assigned to.

Drawing a Guided Activity as a Graph of Views and Transitions
...............................................................

A guided activity can be thought of as a pathway through
some set of views (web pages) within the generic Socraticqs2 interface.

Specifically, a guided activity in Socraticqs2 is defined as a Finite State
Machine (FSM) consisting of a *graph* of *nodes* connected by *edges*:

* its *nodes* are pages or "views", that is, each node shows one
  view from the generic Socraticqs2 interface.  Each node in a FSM
  has a distinct *name*.  An FSM always begins at its 
  ``START`` node, and terminates when it reaches its ``END`` node.
  An ``FSMNode`` instance always has an ``fsm`` attribute that
  points to the ``FSM`` that it is part of.

* its *edges* are transitions from one view (node) to another.
  Concretely, on a given page there may be one or more possible
  *events* such as the user submitting an answer to a question,
  clicking the Next button, etc.  Each event in the generic interface
  has a defined name such as ``next``, ``add``, etc.
  A node can define what events will trigger which edge.
  Each edge has a distinct *name*.
  An ``FSMEdge`` instance always has ``fromNode`` and ``toNode``
  attributes that point to the nodes that it connects.

* while an FSM is running, it is represented by an ``FSMState``
  record that points to the current node, and stores any data
  associated with this running FSM instance.  An ``FSMState``
  instance always keeps an ``fsmNode`` attribute that points to
  the current ``FSMNode``.

An FSM works by intercepting events from the current view, and
redirecting the user to a different next view (node) than the
generic interface's default next view.

Controlling What Happens Next
................................

Node and edge behavior can either be defined *statically*, i.e.
a specific node always shows a fixed path, or *dynamically*,
by writing plug-in code that decides on the fly what it will do.

Static edge behavior
+++++++++++++++++++++

The simplest way to control what happens next at a given node
is simply to provide a static edge that says what node a given event
should transition to.  When an event occurs, the FSM will look for
an outgoing edge with the same name as that event, and will transition
to whatever node that edge points to.
Events with no matching edge will be ignored; i.e. no transition
will occur, and the view will remain at the current page (node).

Dynamic edge behavior
+++++++++++++++++++++++

Alternatively, an edge can decide dynamically what node it will
transition to, if plug-in code is provided for that edge.  The 
plug-in code can do whatever processing it wants, and then simply
returns a node to transition to.  
Note that this is also useful for implementing
*consequences* of an event, even if the edge always transitions to
the same target node.

Dynamic Event Mapping
++++++++++++++++++++++

In some cases it may be useful to dynamically redirect a given event 
to different edges under different circumstances.  A node can do
this by supplying plug-in code for that *event*; its plug-in code
do whatever processing it wants and call whatever edge it wants.
Note this can also be used for implementing consequences of an event.

An FSM can call other FSMs as "subroutines"
.............................................

Our FSM design is *hierarchical*, that is, an FSM node can
"call" another FSM guided activity as a "subroutine".
This is important for modular FSM design.
For example, a randomized trial FSM (that compares the effectiveness
of two "treatments") would not itself need to know how
to perform either of the treatments, because it could just call a "treatment
FSM" that performs the specified treatment, and when finished returns
control to randomized trial FSM.

This hierarchical "subroutine calling" capability is handled
by the ``FSMStack`` class, which acts as the main interface
between Socraticqs2 code and FSM code.  An ``FSMStack`` instance always
keeps a ``state`` attribute that points to the current
``FSMState``.



An Example: Lesson Sequence FSM
--------------------------------

To make this tangible, let's look at an example.  The ``lessonseq`` FSM
shows the student the sequence of core lessons for a courselet,
in the order set by the instructor.  

It consists of four nodes:
``LESSON``, ``ASK``, ``ASSESS``, ``ERRORS`` (in addition to the
mandatory ``START`` and ``END``).

* ``LESSON``: presents an explanation.
* ``ASK``: asks the student a question
* ``ASSESS``: shows the answer and prompts the student for a self-assessment
  of their own answer.
* ``ERRORS``: prompts the student to categorize what error(s) they made
  in their answer.

Edges:

* ``next``: Typically, the ``next`` edge must see whether the next lesson is an
  explanation (``LESSON``) or question (``ASK``), or whether we've reached
  the ``END``.  This dynamic edge behavior is implemented by supplying
  a plug-in method ``next_edge()``.  By convention, plug-in edge methods
  always consist of the *name of the edge* followed by ``_edge``.

* ``error``: if the student self-assessment indicates they got the
  answer wrong, the ``error`` event is directed to take the student
  to the ``ERRORS`` page.

Behind the scenes, there is a ``UnitStatus`` data structure that
knows how to follow the sequence of lessons in that "unit" (courselet).

An FSM is written as a simple set of class definitions for nodes,
with outgoing edges defined for each node.  Here is minimalist code for
the Lesson Sequence FSM::

  class START(object):
      '''Initialize data for viewing a courselet, and go immediately
      to first lesson. '''
      def start_event(self, node, fsmStack, request, **kwargs):
          'event handler for START node'
          unit = fsmStack.state.get_data_attr('unit')
          fsmStack.state.title = 'Study: %s' % unit.title
          unitStatus = UnitStatus(unit=unit, user=request.user)
          unitStatus.save()
          fsmStack.state.set_data_attr('unitStatus', unitStatus)
          return fsmStack.state.transition(fsmStack, request, 'next',
                                           useCurrent=True, **kwargs)
      next_edge = next_lesson
      # node specification data goes here
      title = 'Start This Courselet'
      edges = (
              dict(name='next', toNode='LESSON', title='View Next Lesson'),
          )
  
  class LESSON(object):
      '''View a lesson explanation. '''
      next_edge = next_lesson
      # node specification data goes here
      path = 'ct:lesson'
      title = 'View an explanation'
      edges = (
              dict(name='next', toNode='LESSON', title='View Next Lesson'),
          )
      
  class ASK(object):
      # node specification data goes here
      path = 'ct:ul_respond'
      title = 'Answer this question'
      edges = (
              dict(name='next', toNode='ASSESS', title='Go to self-assessment'),
          )
  
  class ASSESS(object):
      next_edge = next_lesson
      # node specification data goes here
      path = 'ct:assess'
      title = 'Assess your answer'
      edges = (
              dict(name='next', toNode='LESSON', title='View Next Lesson'),
              dict(name='error', toNode='ERRORS', title='Classify your error'),
          )
  
  class ERRORS(object):
      next_edge = next_lesson
      # node specification data goes here
      path = 'ct:assess_errors'
      title = 'Classify your error(s)'
      edges = (
              dict(name='next', toNode='LESSON', title='View Next Lesson'),
          )
  
  class END(object):
      # node specification data goes here
      path = 'ct:unit_tasks_student'
      title = 'Courselet core lessons completed'
      help = '''Congratulations!  You have completed the core lessons for this
      courselet.  See below for suggested next steps for what to study now in
      this courselet.'''

Notes:

* *start event*: whenever an FSM first starts, its ``START`` node is sent
  a ``start`` event.  This FSM defines a ``start_event()`` method on
  its ``START`` node, to receive this event and perform initialization
  of the data which the FSM must store (on its ``FSMState`` data).
  Specifically the method uses the ``FSMState`` ``get_data_attr()``
  and ``set_data_attr()`` methods for binding data to the ``FSMState``.

* Note that this code represents a *specification* of the FSM,
  not the actual storage of the FSM in the database.  Specifically,
  the nodes need do nothing more than specify what data needs
  to be saved for each node, and provide its plug-in code.
  Hence these are just generic Python class objects, not
  ``FSMNode`` objects.  We will describe later how to *load*
  such an FSM specification into the database.

* outgoing edges from a node *must* be specified in its ``edges`` attribute.
  Providing plug-in code for an edge is *optional*, and always follows
  the naming convention ``EDGENAME_edge()``, where ``EDGENAME`` is the
  name of the edge.

* a node typically specifies which generic view it will display
  via its ``path`` attribute.  Paths are given using the Django
  URL "name" convention ``APPNAME:VIEWNAME``; in our case ``ct``
  is the name of our Django app, and the set of all VIEW names are listed in
  ``ct/urls.py``.

* note that a full-blown FSM specification would typically give
  a lot more useful node attributes such as a docstring description, ``help``
  etc. that provide the user helpful guidance.  See the ``FSMNode``
  reference docs below for details.
  
Here is the code for the ``next_lesson()`` edge method used by many of
these nodes.  It uses ``UnitStatus`` and ``UnitLesson`` methods to 
determine what the next view should be::

  def next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
      'edge method that moves us to right state for next lesson (or END)'
      fsm = edge.fromNode.fsm
      unitStatus = fsmStack.state.get_data_attr('unitStatus')
      if useCurrent:
          nextUL = unitStatus.get_lesson()
      else:
          nextUL = unitStatus.start_next_lesson()
      if not nextUL:
          return fsm.get_node('END')
      elif nextUL.is_question():
          return fsm.get_node(name='ASK')
      else: # just a lesson to read
          return edge.toNode

Finally, an FSM specification typically ends with a brief
``FSMSpecification`` initialization that makes it easy to load
the specification into the database.  Here is an example for
the ``lessonseq`` specification::

  def get_specs():
      'get FSM specifications stored in this file'
      spec = FSMSpecification(name='lessonseq', hideTabs=True,
              title='Take the courselet core lessons',
              pluginNodes=[START, LESSON, ASK, ASSESS, ERRORS, END],
          )
      return (spec,)

* this first provides a number of ``FSM`` attributes such as its
  *name*, user interface properties (in this case it specifies that
  the tabbed interface should be hidden while this FSM is running), etc.
* it also lists the complete set of nodes in the FSM.

* to actually load an ``FSMSpecification`` into the database,
  simply call its ``save_graph()`` method with the username who should
  "own" this FSM.  (Typically, this would be an admin user)::

    fsmSpec.save_graph('admin')

* Any time an FSM structure or attributes changes, it must be reloaded
  to the database this way, to take effect.

* note that FSM specifications and plug in code must be stored in
  Python source code files in the ``mysite/ct/fsm_plugin/`` directory.


FSM Reference Documentation
-----------------------------

FSM
....

**Important attributes to set in your FSM specification:**

.. attribute:: name

   the ID by which the FSM will be called.  That is, FSMs are invoked
   by name.  For example, when the user indicates they want to study
   the sequence of lessons in a courselet, the generic Socraticqs2
   UI searches for an FSM named ``lessonseq``.

.. attribute:: title

   The title which will be displayed by default for the FSM,
   unless its plug-in code ``start_event()`` explicitly overrides that
   by writing a new value to the ``FSMState.title`` for this running
   FSM instance.

.. attribute:: description

   An explanation of what this Guided Activity does for the user,
   to be displayed in the Activity Center UI etc.

.. attribute:: help

   More detailed info to help the user understand what this FSM is for.

.. attribute:: hideTabs

   If set True, hide the generic tabbed interface while this FSM is running.

.. attribute:: hideLinks

   If set True, block hyperlinks from being clickable while this FSM is running.

.. attribute:: hideNav

   If set True, hide the generic navigation bar options while this FSM
   is running.

**Useful methods**:

.. method:: get_node(name)

   Get node in this FSM with specified *name*.

.. classmethod:: save_graph(klass, fsmData, nodeData, edgeData, username, oldLabel='OLD')

   **this is a low-level call; in general you should use the higher
   level call FSMSpecification.save_graph() instead**.
   Store FSM specification from node, edge graph
   by renaming any existing
   FSM with the same name, and creating new FSM.
   Note that ongoing activities
   using the old FSM will continue to work (following the old FSM spec),
   but any new activities will be created using the new FSM spec
   (since they request it by name).
   Returns the newly created ``FSM`` object.

FSMNode
........

**Important attributes to set in your FSM specification:**

.. attribute:: name

   Note that you set this in an FSM specification by simply
   naming the class definition that you write for a node.

.. attribute:: description

   Provides an explanation of what this step in the Guided Activity
   does for the user, to display in the Activity Center UI, etc.
   Note that you set this by simply giving a **docstring** in
   the class definition that you write for a node.

.. attribute:: title

   Title for the current step to be displayed in the Activity Center
   UI etc.

.. attribute:: help

   Instructions for this step that will be displayed to the user
   as an overlay at the top of the current page, *in addition* to
   the generic instructions that are always shown on that page.
   This enables you to customize very clearly what you want the
   user to look at and do when performing this step.

.. attribute:: path

   specifies which generic view it will display
   via its ``path`` attribute.  Paths are given using the Django
   URL "name" convention ``APPNAME:VIEWNAME``; in our case ``ct``
   is the name of our Django app, and the set of all VIEW names are listed in
   ``ct/urls.py``.

.. attribute:: doLogging

   If set True, records entry and exit timestamps for the user's
   visit to this view.  Log data are saved as ``ActivityEvent``
   records.  If the current FSMState instance already has
   an ``activity`` attribute pointing to the current ``ActivityLog``,
   the event will be marked as part of that ``ActivityLog``.
   Otherwise, an ``ActivityLog`` whose name matches the current
   FSM will be used (or created, if it does not already exist),
   and also set as the current ``FSMState.activity``.

   Note that ``Response`` and ``StudentError`` data created 
   while an FSM is running are also automatically time stamped
   and bound to the current ``FSMState.activity``.


**Plug-in code**:

You can supply three types of plug-in methods on a Node specification
class:

* **path method**: if a node must determine its URL dynamically, you
  can supply a ``get_path()`` method to do so.  It must return a 
  URL string of the form ``'/ct/some/path/'``.  Note the trailing
  ``/``, required by convention in Django.  The method definition must be
  of the following form::

    class FOO(object):
        def get_path(self, node, state, request, **kwargs):
            'get URL for next steps in this unit'
            unitStatus = state.get_data_attr('unitStatus')
            return unitStatus.unit.get_study_url(request.path)

* **event method**: if a node needs to determine dynamically
  what edge to trigger in response to a given event, you can
  supply a method named ``EVENTNAME_event()`` to do so
  (where ``EVENTNAME`` is the name of the event you want it
  to intercept).  It should call the desired edge transition
  directly, and return the result.  The method definition must be
  of the following form::

    class FOO(object):
        def start_event(self, node, fsmStack, request, **kwargs):
            'event handler for START node'
            unit = fsmStack.state.get_data_attr('unit')
            fsmStack.state.title = 'Study: %s' % unit.title
            unitStatus = UnitStatus(unit=unit, user=request.user)
            unitStatus.save()
            fsmStack.state.set_data_attr('unitStatus', unitStatus)
            return fsmStack.state.transition(fsmStack, request, 'next',
                                             useCurrent=True, **kwargs)

* **edge method**: if an edge needs to do something (such as save
  state data or decide dynamically what node to transition to),
  you can do so by supplying a method named ``EDGENAME_edge()``,
  where ``EDGENAME`` is the name of the edge it should intercept.
  It must return an ``FSMNode`` to transition to.
  The method definition must be of the following form::

    class FOO(object):
        def next_edge(self, edge, fsmStack, request, **kwargs):
            # ... do some processing here, save some data on fsmStack.state...
            return edge.toNode # finally return target node


FSMState
.........

Represents the current state of a running FSM instance.

**useful attributes you can read / write from plug-in code**:

.. attribute:: user

   The user running this FSM instance.  Do not change this directly.

.. attribute:: fsmNode

   The current node.  Do not change this directly.

.. attribute:: activity

   The current ``ActivityLog`` for logging timestamp data to.
   You can set this directly, e.g. in ``start`` event plug-in code.

.. attribute:: title

   The title which will be displayed for the FSM.

.. attribute:: hideTabs

   If set True, hide the generic tabbed interface while this FSM is running.

.. attribute:: hideLinks

   If set True, block hyperlinks from being clickable while this FSM is running.

.. attribute:: hideNav

   If set True, hide the generic navigation bar options while this FSM
   is running.

.. attribute:: unitLesson

   records what lesson or question the FSM is currently working
   with.  This is so useful that it is part of the database definition
   of ``FSMState``.

   Other arbitrary data can be saved using
   the ``FSMState.data`` JSON blob storage using the following methods.

**useful methods you can call from plug-in code**:

.. method:: get_data_attr(attr)

   Retrieve the named attribute *attr* from the ``FSMState.data``
   JSON blob, or ``KeyError`` if it does not exist.

.. method:: set_data_attr(attr, value)

   Store *value* as the named attribute *attr* on the ``FSMState.data``
   JSON blob.

.. method:: get_all_state_data()

   Get a dictionary of named attributes from the current state,
   including both the ``unitLesson`` attribute, and attributes
   stored in the ``FSMState.data`` JSON blob.

