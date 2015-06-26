==============================================
Getting Started with Socraticqs2 Development
==============================================

Installation and setup
-----------------------

Pre-requisites
...............

To run the Socraticqs2 development/test server on your computer,
you need:

* Python 2.7
* Django 1.7 or higher
* Pandoc (currently used for converting text to HTML): you can download
  this for Mac OS X; most linux package managers can install it automatically.
* several Python packages installable by pip: pypandoc, django-crispy-forms,
  wikipedia

We also use Git as our version control; if you don't already have it,
you can download either Github for Windows or Github for Mac;
most linux package managers can install Git for you automatically.

Optional: use virtualenv to create an isolated test environment
................................................................

I find it convenient to isolate my development environment from
any other Python installation, by using virtualenv.
To create an empty virtualenv (replace the path with whatever you want)::

  virtualenv /path/to/put/your/new/ve

To start working with this virtualenv in a given terminal session
(either to install pip packages into it as below, or to actually use it),
type (again replace the path with what you used in the previous step)::

  source /path/to/put/your/new/ve/bin/activate

Installing Django etc.
........................

.. warning::

   On Ubuntu-like distros, you must first install some dependencies
   of the python lxml package, *before* running `pip install` below::

     sudo apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-dev

Assuming you have Python and Pandoc installed::

  pip install -r dev_requirements.txt


Git version control software
.....................................

We use `Git <http://www.git-scm.com>`_ and 
`GitHub <https://github.com>`_ for working on Socraticqs2 development.
You'll first need to get Git: 

* for Windows and Mac, you can download it from
  `the Git website <http://www.git-scm.com>`_ (command-line interface,
  recommended).  We also recommend installing a graphical
  interface for viewing Git code revision history such as
  `SourceTree <http://www.sourcetreeapp.com>`_.
* Alternatively, you can download the 
  GitHub for Windows / Mac app from GitHub (more limited, in our humble
  opinion).
* On Linux, your package manager can install (and update) Git
  for you automatically.  We recommend installing both the command
  line tools (``git``) and a graphical interface (``gitg``).

Getting the Socraticqs2 source code
.....................................

To get your own copy of the Socraticqs2 code, 
first go to our Github repository 
https://github.com/cjlee112/socraticqs2
and Fork the repository (you'll need a Github account to do this).  
This creates your own repository in your Github account, which you
can make changes to, and issue pull requests for us to incorporate
your changes.  Next clone the repository to your local computer,
one of two ways:

* **via the command line**: click the "HTTPS clone URL" *copy to clipboard*
  button on your GitHub repository page, and paste it into a terminal
  command like so (substitute your correct clone URL)::

    git clone https://github.com/YOURNAME/socraticqs2.git

  This will clone the repository to a new directory ``socraticqs2/``
  in your current directory.  We recommend you also add our main
  repository as a "remote" repository called ``upstream``::

    cd socraticqs2
    git remote add upstream https://github.com/cjlee112/socraticqs2.git

* **via Github for Windows or Mac**: you can just click the Clone to Desktop
  link on the webpage for your fork (repository).

Run the test suite
....................

To make sure your setup is working properly, try running the 
test suite::

  cd socraticqs2/mysite
  python manage.py test ct

You should see a series of tests pass successfully.

Running a test web server
...........................

You need to create a database, load it with some data, and
run the development web server.  You first create the 
database::

  python manage.py migrate

Next load it with some example data that we supply in the
repository::

  python manage.py loaddata dumpdata/debug.json

Finally, start up the development web server::

  python manage.py runserver

Start a web browser and point it at http://localhost:8000/ct/

It will prompt you to log in; the default development tester
username is ``admin`` with password ``testonly``.  

You can stop the web server by simply typing Control-C.

Security notes:

* you should not allow any outside access to localhost port 8000
  as this is insecure (e.g. an outsider could log in with the default
  credentials above and modify data in your development server).


Basic Developer Operations
---------------------------

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
+++++++++++++++++++++++++++++++

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
  

Database Operations
.....................

Updating your database schema 
++++++++++++++++++++++++++++++

If upstream code changes (i.e. made by someone else, and pulled
into your local repo) alter the database schema, you will have to
update your developer database to match.  You will typically notice this
in two ways:

* upstream code changes introduced new migration files in ``ct/migrations/``.
  These files tell Django how to update your database schema.

* when you try to run the testsuite or ``runserver``, you will get
  an error message saying that your database schema does not match
  the current data models.

To migrate your database to the new schema, type::

  python manage.py migrate ct

Altering the database schema (models) yourself
++++++++++++++++++++++++++++++++++++++++++++++++

If you change the database fields for a data model in ``models.py``,
you will of course also have to change your database to match.
(Note that this means changes to the data fields that are
stored in the database; changing or adding method code on
the data classes does not change the database schema).

Django 1.7 makes this easy via its ``makemigrations`` command.

First make a backup copy of your current database (this is important,
because it's not obvious whether there is any easy way to "undo" a migration)::

  cp mysite.db mysite.db.previous

Then simply type::

  python manage.py makemigrations ct

This will create a new migration file in ``ct/migrations``.  You then apply
this migration to your database exactly as we did in the previous section::

  python manage.py migrate ct

At this point you should be able to run the testsuite, ``runserver``, etc.


.. warning::
   You must commit your new migration file at the same time
   as you commit your schema changes in ``models.py``, so that others can
   update their database to match the new models.  E.g. using command-line
   Git, you'd type something like::

     git add ct/models.py
     git add ct/migrations/0005_unitstatus.py
     git commit -m 'added UnitStatus to models'

   where ``ct/migrations/0005_unitstatus.py`` is the new migration file
   created by ``makemigrations`` to represent the changes you made to 
   ``models.py``.

.. warning::
   There are several limitations that make migrations somewhat unwieldy.
   You need to be aware of the following "gotchas" lurking here:

   * once you change a model in ``models.py``, your code will no longer
     run until you successfully run ``makemigrations`` + ``migrate``.
     So you cannot actually test your changes until you run both those steps.

   * every time you run ``makemigrations`` on another change to
     your data models, ANOTHER migration file
     will be added, and EVERY migration file will be
     required for the migration to work.
     Multiple migration files increase the risk of errors either in 
     your committing them or other people attempting to apply them.
     So ideally, when you change the models to introduce a new feature,
     you want that to be represented by a single new migration file.

   * Because of this, in theory you shouldn't
     run ``makemigrations`` / ``migrate`` until
     *after* you are pretty sure your model changes are final.  
     But you can't even test your changes until after both steps.
     This is an unpleasant catch-22.

   * Once you change your database schema (via ``migrate``), all *other*
     code versions (i.e. not matching the new schema stored in your
     database) will NOT run.
     This would destroy the key virtue of Git -- your ability to 
     have many different code branches and switch between them 
     effortlessly.

Recommended Migration Best Practices
+++++++++++++++++++++++++++++++++++++

For all these reasons, I suggest you follow a simple discipline
whenever you are about to make model changes that will require
migration:

* BEFORE making those changes, save a copy of your current
  database file and checkout a *new* Git branch, e.g.::

    cp mysite.db mysite.db.previous
    git checkout -b bigchange

  where ``previous`` is the name of your previous branch,
  and ``bigchange`` is the name of your new branch.
  You should also do this if you are starting to work with
  someone else's experimental model changes, e.g.::

    cp mysite.db mysite.db.previous
    git checkout -b bigchange
    git pull fred bigchange

  Then, if you ever want to switch back to your ``previous``
  branch, you can simply switch back to the database file
  that worked with ``previous``::

    git checkout previous
    cp mysite.db.previous mysite.db

  Note that you should NOT add ``mysite.db`` to Git
  version control.

* Now you can freely run ``makemigrations`` + ``migrate``
  whenever you like, so you can test your changes.

* If it turns out that you need to make *more* model
  changes (i.e. your model changes turned out to be inadequate
  for the feature you're implementing, and you haven't yet committed
  the inadequate models/migration),
  the best practice is to UNDO your migration
  and REGENERATE a new migration to replace it, like this::

    rm ct/migrations/0005_unitstatus.py
    cp mysite.db.previous mysite.db
    python manage.py makemigrations ct
    python manage.py migrate ct

  where ``ct/migrations/0005_unitstatus.py`` is your new
  migration file, and ``mysite.db.previous`` is a copy of
  your database file from before you applied this new migration.

   

Backing up, flushing, and restoring your local database
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You may wish to make and reload snapshots of your local database
as part of your development and testing process.  This is easy.

You can save a snapshot of your current database to a file, like this::

  python manage.py dumpdata > dumpdata/mysnap.json

You can flush (delete all data) from your database like this::

  python manage.py sqlflush|python manage.py dbshell

You can then restore a particular snapshot like this::

  python manage.py loaddata dumpdata/mysnap.json



