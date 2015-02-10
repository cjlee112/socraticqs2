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

Assuming you have Python and Pandoc installed::

  pip install Django
  pip install pypandoc
  pip install django-crispy-forms
  pip install wikipedia

Getting the Socraticqs2 source code
.....................................

To do development work, first go to our Github repository 
https://github.com/cjlee112/socraticqs2
and Fork the repository (you'll need a Github account to do this).  
This creates your own repository in your Github account, which you
can make changes to, and issue pull requests for us to incorporate
your changes.

If you use Github for Windows or Mac, you can just click the Clone to Desktop
link on the webpage for your fork (repository).  Otherwise you can just
click github's HTTPS clone URL box for the repo, and clone the repo
to your computer in your usual way, e.g. via the command line::

  git clone https://github.com/cjlee112/socraticqs2.git

Update paths in settings.py
.............................

Unfortunately, Django obligates us to give absolute paths to
the database and template files, which are of course specific
to an individual computer.  Hence you will have to edit the
file ``socraticqs2/mysite/mysite/settings.py``: search for
the string ``/home/user`` (two instances) and replace with a
path appropriate for your computer.

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

Pulling the latest code using Github for Windows / Mac
.......................................................

Using Github for Windows / Mac
++++++++++++++++++++++++++++++++

Github for Windows / Mac doesn't work with multiple remotes --
it only synchronizes against your GitHub fork. There are two
ways to get the latest updates from *our* code on Windows / Mac:

* **Through terminal**

#. On GitHub, navigate to our cjlee112/socraticqs2 repository.

#. In the right sidebar of the repository page, copy the clone URL for the repository.

#. Open Terminal and change directories to the location of the fork you cloned.

#. Add a new remote named 'upstream' using the origin repository::

    git remote add upstream https://github.com/cjlee112/socraticqs2.git

#. To verify the new upstream repository you've specified for your fork, use command line::

    git remote -v

   you suppose to see the following lines::

     upstream  https://github.com/cjlee112/socraticqs2.git (fetch)
     upstream  https://github.com/cjlee112/socraticqs2.git (push)

#. Now you are able to fetch the branches and their respective commits from the upstream repository::

    $ git fetch upstream

   Also, you can merge the change from upstream/master to your local master branch. This brings your fork's master branch into sync with the upstream repository::

    $ git merge upstream/master

* **Using GitHub desktop client**

  Unfortunately, this is less user friendly. However, you can achieve the same goad by doing following:

#. Go to the setting tab of your fork.

#. Change the "Primary remote repository" to the upstream repo you want to use.(ie, https://github.com/cjlee112/socraticqs2.git)

#. Press "Update Remote"
#. Press "Sync Branch"
#. Change the "Primary remote repository" back to the original forked repo you were using.
#. Press "Update Remote"

Using standard Git
+++++++++++++++++++

Using a standard Git setup, this process is much easier.  Assuming
that you cloned our repo (so that Git's ``remote`` repo points to 
our repo), you can pull our latest changes by simply typing::

  git pull origin master

Or if you want simply to fetch our latest changes (without actually
merging them into your current branch), so that you can look at them,
just type::

  git fetch origin

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

   * every time you run ``makemigrations`` ANOTHER migration file
     is added, and they ALL are required for the migration to work.
     Multiple migration files increase the risk of errors either in 
     your committing them or other people attempting to apply them.
     So ideally, when you change the models to introduce a new feature,
     you want that to be represented by a single new migration file.

   * Because of this, in theory you shouldn't
     run ``makemigrations`` / ``migrate`` until
     *after* you are pretty sure your model changes are final.  
     But you can't even test your changes until after both steps.
     This is an unpleasant catch-22.

   * Once you change your database schema (via ``migrate``), all other
     code (i.e. not matching the new models) will NOT run.
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

  Note that I do NOT recommend adding ``mysite.db`` to Git
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



