
Git Usage Guide
----------------------

Pulling the latest code updates
.......................................................

Using standard Git
+++++++++++++++++++

Assuming you used our Git setup instructions above
(so that your local repository's ``upstream`` remote points to 
our repo), you can pull our latest changes from a specific branch
(e.g. ``master``) by simply typing::

  git pull upstream master

Or if you want simply to fetch our latest changes (without actually
merging them into your current branch), so that you can look at them,
just type::

  git fetch upstream

You can then use your graphical viewer (e.g. ``gitg`` or SourceTree)
to view the latest ``upstream`` commits prior to merging them into
your own branch(es).

Using Github for Windows / Mac
++++++++++++++++++++++++++++++++

Github for Windows / Mac doesn't work with multiple remotes --
it only synchronizes against your GitHub fork. Working around
this limitation, there are two
ways to get the latest updates from *our* GitHub fork:

via the command line
:::::::::::::::::::::::

#. If this is the first time you are pulling from our repository,
   you will need to add a "remote" telling Git the URL of our
   repository, like so::

     git remote add upstream https://github.com/cjlee112/socraticqs2.git

   You can verify the new ``upstream`` repository has been added,
   by listing all the existing remotes::

     git remote -v

   You should see the following lines (in addition to your other remotes)::

     upstream  https://github.com/cjlee112/socraticqs2.git (fetch)
     upstream  https://github.com/cjlee112/socraticqs2.git (push)

#. Now you are able to pull or fetch the branches and their respective
   commits from the upstream repository, using the standard Git commands
   listed in the previous section, e.g.::

     $ git fetch upstream

   Once you've fetched ``upstream`` commits, you can merge them
   (e.g. from ``upstream/master``) to your current local branch::

     $ git merge upstream/master

   This brings your current branch into sync with ``upstream/master``.

Using GitHub desktop client
:::::::::::::::::::::::::::::::

Unfortunately, this is less user friendly. However, you can achieve the same goal by doing following:

#. Go to the setting tab of your fork.

#. Change the "Primary remote repository" to the upstream repo you want to use.(ie, https://github.com/cjlee112/socraticqs2.git)

#. Press "Update Remote"
#. Press "Sync Branch"
#. Change the "Primary remote repository" back to the original forked repo you were using.
#. Press "Update Remote"

Making source-code changes
............................

We strongly recommend that you take advantage of Git's easy
revision control "branches" to create a new "experimental" branch
for any changes you want to try, e.g. via the command-line::

  git checkout -b try

This creates a new branch called ``try``, forked from your
current branch (for the purpose of argument, let's assume it
was called ``previous``).  Now make and commit whatever
changes you want.  

* As long as your latest changes have been committed, you can
  instantly switch to another branch, like so::

    git checkout previous

* If you decide you want to merge your changes from ``try`` into
  your current branch, just type::

    git merge try

  If you now have no further need for ``try``, because all its commits
  have been merged into your current branch, type::

    git branch -d try

* If you decide you want to abandon (completely delete)
  the changes you made on ``try``, just type::

    git branch -D try

* If you decide to abandon your latest commit (undo its changes, and
  delete the commit), you can type::

    git reset --hard HEAD^

  In general, if you want to "reset" your branch to a previous commit
  (abandoning subsequent changes), just type::

    git reset --hard 7a529

  where ``7a529`` is the commit ID you want to go back to.

See a Git tutorial to learn more about all its great capabilities.

Some best practices to follow
................................

* don't push "junk" commits to your public (GitHub) repository.
  Instead clean up your branch to get rid of unwanted commits
  (using methods like the above), before pushing it to GitHub.
* once your branch is "clean", make sure the test suite passes
  before you push your branch to GitHub.
* When you branch is clean and all tests pass, you can push
  it to GitHub so others can access it.  For example, to push
  your ``try`` branch::

    git push origin try

* Git can do just about anything to help you clean up or reorganize
  your branches, but its complexities may initially seem
  mystifying.  When in doubt about how to get Git to do what you
  want, search Google for a tutorial, or ask us for help.
  
