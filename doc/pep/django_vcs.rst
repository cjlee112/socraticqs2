
Django Version Collaboration System for Courselets
---------------------------------------------------------------------

Basic goals
+++++++++++++++

* Git-like VCS for text+metadata rather than code
* Application model is community-remix-forest rather than code-pyramid.
* stored in standard database (rather than files)
* Integrates VCS capabilities into standard online platform (Django)
* KISS: sweetspot of core VCS benefits without Git's complexity, for non-Git-users
* Designed for courselets active-learning materials, which consists of one datatype (Lesson) and two levels of container (Unit and Course), all three under VC.

VCS layers
++++++++++++

* **Lesson**

  * Lesson is a *commit*
  * UnitLesson is a *branch* (HEAD pointer)

* **Unit**: a repository of UnitLessons

  * Unit is a commit
  * CourseUnit is branch

* **Course**: a repository of CourseUnits

  * Course is a commit
  * CourseBranch is a branch

Some simplifying assumptions:

* In general, we store VCS tree structure directly on commit objects (with **parent** and **mergeParent** pointers).

* In general, commits are "snapshots" of content (i.e. exact same form as the "working tree"), with no special attempt to compress or diff its storage.  Our content is typically a short text (<8k?), so this seems like a reasonable simplification in the era of cheap big storage.

* it follows that branch (HEAD) can point to content that is not yet permanently committed, i.e. owner can go on modifying that content until they decide it's ready to commit (or another event, e.g. fork, forces a commit).


Collaboration Philosophy
+++++++++++++++++++++++++

* Instructors are not expected to understand the Git version control model, especially complex concepts like branches and rebasing.

* instead, Unit provides intuitive freedom to modify a lesson however you want for this Unit, without affecting any other units.

* anyone can fork anything (creating new branch within that repository), but only the "master" branch owned by the instructor is shown to users as the "official version" of that repository.

* user can fork to create a new branch at several different levels

  * fork a Lesson either within same Unit or a different Unit.
  * fork a Unit either within same Course or a different Course.  Forking a Unit in turn forks all the Lessons within that Unit.
  * fork a Course either as new public course or private branch.  Forking a Course in turns forks all the Units within that Course.

* in general, searches will operate only on "master" content (e.g. Lessons pointed to by UnitLessons with isMaster=True).

* following the Git model of "fine-grained" commit history will make automatic merge much more useful (by giving users easy control over what changes to accept).  This seems like the Git sweet-spot, i.e. the part that's both easiest for users to understand, and most useful for them.  Besides, disk-space is not really an issue...  Policy:

  * if user provides a Commit Message after modifying an object, commit it permanently.
  * various views should warn the instructor: "you have not committed a snapshot of the current version.  If you are done changing it (for the moment), please commit it by entering a Commit Message on the Edit tab".

* automatically commit when operationally appropriate.  While the user should be encouraged to commit fine-grained changes, we will commit automatically on various events:

  * checkout by someone other than Lesson owner (addedBy) will commit it, since otherwise changes by different people would get mixed in the same commit.
  * fork
  * publish
  * Response
  * course over (future commitTime): consider allowing commitTime to be set to a future date, so that it will automatically be considered committed at that time.  Also consider inheriting future commitTime from container (e.g. if Unit has future commitTime, creating a new UnitLesson in this Unit should inherit that future commitTime).

* when someone first forks a lesson, ask them to review it carefully for typos or errors, and to make corrections (on the parent branch).  Hopefully this will mostly eliminate the need for propagating pull requests to "upstream" branches.  (Then ask them if they want to change the focus, audience or substance significantly, which adds a "cut" edge.)

* in general, everyone on "the same branch" (see bridge-cut description below) will receive pull requests for each other's changes.

* goal is for auto-merge with manual resolution: top-down view of diffs lets you drill down.  If you need to intervene manually for some parts of the merge, you do so for those specific part(s).  Finally you can just accept the top-level merge and it will merge everything else automatically.

Proposed data model
---------------------

* **commitTime** indicates commit status

  * NULL indicates uncommitted
  * commitTime in the future indicates uncommitted.  If container has future commitTime, new HEADs created in this container should inherit this future commitTime.
  * commitTime in the past indicates committed.

* **treeID, isMaster, branch** multiple-HEAD model: within a given container (e.g. Unit) we can have many versions of something (with same treeID), one of which will have isMaster=True, and also distinguished by owner (addedBy) and branch name.  This model applies at several levels:

  * UnitLesson: represents HEAD pointer for a Lesson
  * CourseUnit: represents HEAD pointer for a Unit
  * CourseBranch: represents HEAD pointer for a Course

* in a given course, master Unit, UnitLesson, Course IDs will not change.  I.e. when we add a Unit to a course with isMaster=True, we create a new Unit object (possibly cloned from an existing Unit in another course), and we keeping using that object in that course thereafter (unless of course the user deletes the unit from the course).  Similarly, whenever we add a UnitLesson with isMaster=True to a Unit (e.g. cloned from another Unit), we always add it as a newly created UnitLesson object, and we keep using that object in that Unit thereafter (unless of course the user deletes it).

* UnitLesson **isMaster=True** indicates what version will actually be shown in that Unit.  This allows many alternate versions (including student users') in the same Unit, all but one of which have isMaster=False.  This field must be indexed in the db properly!!  Note that to keep public IDs stable, once a UnitLesson has isMaster=True, it becomes the public ID.  Another way of saying this: you will never reset it to isMaster=False (in order to set some other UnitLesson.isMaster=True), because that would change the public ID of this Lesson in this Unit.  Instead you just change what Lesson this UnitLesson points to (and possibly its branch name).

* Unit and Course should use **commitID** as the key value for pointing to parent(s), rather than just using primary key in the usual way.  This is a solid technical solution for allowing us to keep stable both the public ID and the parent pointer(s).  commitID rules:

  * for an uncommitted object, commitID=NULL.
  * for a newly committed object, commitID=self.pk
  * when a committed object is cloned for checkout (see below), the commitID is copied to the commit-clone, and the original object (now checked out) is set to commitID=NULL to reflect that it is now checked out (uncommitted).

  We will have to supply a get_parent() method that looks up parent object by commitID.

  Note this issue does not apply to Lesson, because Lesson ID is never public (what's publicly visible is the UnitLesson ID).

* Implies a fork-commit-checkout-clone pattern for Unit and Course if isMaster=True:

  * when someone forks an object, we must commit it.
  * when the owner wants to modify (checkout) the committed object, if it has isMaster=True, then we must clone it in a special way to preserve the HEAD ID.  Specifically, we create a clone of the committed HEAD object, remove the commit lock from our HEAD object, and make it point to the clone as its parent.  This preserves the tree structure while allowing us to continue editing the same HEAD ID.  Note that we only have to do this in the specific case where owner wants to modify (checkout) a *committed* isMaster=True object.

Structural Segmentation Policies
---------------------------------

The Git/GitHub pull-request model is not suitable for Courselets, because its "code-pyramid" model is all about convergence to a "master" who can be relied on to decide what changes to accept.  In the Courselets community-remix-forest, by contrast, that will not work, because there is no such "master"; even more fundamentally, divergence (segmentation) is as valuable as convergence.  What we want is for segmentation to emerge naturally and with minimal effort from users, e.g. I should automatically receive pull-requests from within my "segment", but not outside.

We will achieve this via a mechanism of edges added onto a VCS tree that explicitly represent what "pull policy" a user wants to apply in the future to a given subtree:

* emergent segmentation via bridge vs. cut edges: generalize Git's concept of "merge strategy" to indicate whether you want to receive future pull requests or not.  E.g.

  * suggest merging future pull-requests from this subtree (typically this would be associated with merging in last state of this subtree)
  * offer option to merge ...
  * hide ... (typically this would be associated with merge -s ours operation)
  * NULL (no preference)

  You could also suggest flow the other direction:

  * suggest merging my commits to this subtree
  * offer option to merge ...
  * hide ...
  * NULL (no preference)

  For a given user considering possible things to merge into his branch, his PULL setting always overrides other people's PUSH settings.

  Operates the same as recursive merge search, i.e. backtrack both HEADS until you find a common merge origin, bridge, or cut, whichever comes first.  Bridge propagates the pull-request; cut blocks it.

* useful to extract the clique-structure of which HEADs are convergent (get each other's changes) vs. divergent (do not).

* can consider the PUSH-edge version of this to be a generalization of pull-requests.  That is, you can either suggest your changes to everyone (by adding PUSH edge from your HEAD to root of the tree), or to a specific branch / subtree.

Automatic Merge
---------------------

Use my Word interval nested containment list 3-way merge algorithm.

* line-based diff (e.g. Git) cannot merge changes in the same paragraph
* Git cannot handle re-ordering / remixing; after a block of text is moved, changes within it can no longer be merged.

VCS User Interface
---------------------

* presumably there will be a new tab "Versions" or "History" that shows gitg-like diagram of commits and HEADs.  Allows user to click to view a diff, or switch branches etc.

* user who gets a pull-request can of course reject changes (selectively). (imagine this as table of commits with checkboxes so you can accept all, none, or subset.

* can propagate pull requests to downstream branches, but only if they map cleanly onto that branch.

