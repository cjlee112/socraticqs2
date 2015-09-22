==============================================
Getting Started with Socraticqs2 Development
==============================================

Installation and setup
-----------------------

Recommended: use virtualenv to create an isolated test environment
.....................................................................

I find it convenient to isolate my development environment from
any other Python installation, by using virtualenv.
To create an empty virtualenv (replace the path with whatever you want)::

  virtualenv /path/to/put/your/new/ve

To start working with this virtualenv in a given terminal session
(either to install pip packages into it as below, or to actually use it),
type (again replace the path with what you used in the previous step)::

  source /path/to/put/your/new/ve/bin/activate

Pre-requisites
...............

To run the Socraticqs2 development/test server on your computer,
you need various things such as:

* **Python 2.7**
* **Git**: we use Git as our version control; if you don't already have it,
  you can download either Github for Windows or Github for Mac;
  most linux package managers can install Git for you automatically.
  See further details below.
* **PostgreSQL**: back-end database for Socraticqs2.  See further details below.
* **Pandoc** (currently used for converting text to HTML): you can download
  this for Mac OS X; most linux package managers can install it automatically.
* **RabbitMQ**: an open source message broker software that implements the 
  Advanced Message Queuing Protocol (AMQP) - used by Celery.
* **Memcached**: free & open source, high-performance, distributed memory 
  object caching system.
* **Python packages** automatically installable by pip using our
  `dev_requirements.txt` requirements file:
  e.g. Django, pypandoc, django-crispy-forms,
  wikipedia etc.  This is described in detail below.

.. warning::

   On Ubuntu-like distros, you must first install some dependencies
   of the python lxml package, *before* running `pip install` below::

     sudo apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-dev



Installing Git version control software
...........................................

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

If you are not accustomed to using Git / GitHub as your primary version
control system, we suggest you review our :doc:`gitguide`.

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


Installing and configuring PostgreSQL
.....................................

Ubuntu 14.04 distribution instructions
::::::::::::::::::::::::::::::::::::::


You can check PostgreSQL installation manual for linux on official PostgreSQL `page`_.

.. _page: http://www.postgresql.org/download/linux/ubuntu/

Steps to install PostgreSQL on Ubuntu machine:

* Create the file ``/etc/apt/sources.list.d/pgdg.list``, and
  add a line for the repository 
    ::

     deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main

* Import the repository signing key, and update the package lists
  ::

   wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
     sudo apt-key add -
   sudo apt-get update

* Install postgres-9.4::
   
   sudo apt-get install postgresql-9.4

.. warning::

   On Ubuntu-like distros, you must first install postgresql-server-dev-9.4
   as a dependency to python psycopg2 package, *before* running `pip install` below::

     sudo apt-get install postgresql-server-dev-9.4

* Next we need to set default postgres user password to start development process::

   sudo -u postgres psql postgres
   postgres=# \password postgres

* Now we can exit from PostgreSQL and start to configure our Django project to use created database::

    postgres=# \q

* But one more thing we need to do is to open pg_hba.conf file::

    sudo vim /etc/postgresql/9.4/main/pg_hba.conf

* And change::

    local   all    postgres    peer

  to::

    local   all    postgres    md5

* Finally we need to restart PostgreSQL server::

    sudo service postgresql restart


In case when you don't want to have the PostgreSQL server running all the time on your computer, just to play with the Socraticqs2 code (e.g. this consumes system resources), you can start and stop PostgreSQL manually::

    sudo service postgresql stop
    sudo service postgresql start


There are couple of ways to prevent PostgreSQL to start on system boot:

1. First one is to remove system start-up links for postgres::

    ✗ sudo update-rc.d -f postgresql remove
      Removing any system startup links for /etc/init.d/postgresql ...
        /etc/rc0.d/K21postgresql
        /etc/rc1.d/K21postgresql
        /etc/rc2.d/S19postgresql
        /etc/rc3.d/S19postgresql
        /etc/rc4.d/S19postgresql
        /etc/rc5.d/S19postgresql
        /etc/rc6.d/K21postgresql

  In this case we can use default way to start postgres manually::

      sudo service postgresql start

2. Second one is to change line ``auto`` to ``manual`` in ``/etc/postgresql/9.4/main/start.conf``::

    # Automatic startup configuration
    # auto: automatically start/stop the cluster in the init script
    # manual: do not start/stop in init scripts, but allow manual startup with
    #         pg_ctlcluster
    # disabled: do not allow manual startup with pg_ctlcluster (this can be easily
    #           circumvented and is only meant to be a small protection for
    #           accidents).

    auto

  In this case we prevent to start ``main`` postgres cluster and need to use next commands to ``stop|start`` pg_cluster::

      sudo pg_ctlcluster 9.4 main stop
      sudo pg_ctlcluster 9.4 main start 


More information you can find on PostgreSQL 9.4 `documentation`_ page.

.. _documentation: http://www.postgresql.org/docs/9.4/static/

Mac OS X installation
:::::::::::::::::::::

For installing PostgreSQL on Mac OS X please follow the official `instructions`_.

.. _instructions: http://www.postgresql.org/download/macosx/

One of the prefered way to install PostreSQL is `Homebrew`_::

    brew install postgres

.. _Homebrew: http://brew.sh

Postgres will be installed into ``/usr/local/var/postgres`` directory.

Information about how to start Postgres you can find by following command::

    brew info postgres

By default Homebrew create postgres role with name as your mac username.

So you need to set a password for this role::

    psql postgres
    \password your_username


Configuring Django project for using PostgreSQL
...............................................

To configure project you need to copy ``mysite/settings/local_conf_example.py`` into ``mysite/settings/local_conf.py`` and change DATABASES dict according to previously configured PostgreSQL user and db_name::

    DATABASES = {
        'default': {
          'ENGINE': 'django.db.backends.postgresql_psycopg2',
          'NAME': 'db_name',
          'USER':  'your_username', (postgres for Ubuntu default configuration proccess)
          'PASSWORD': 'your_postgres_pass',
          'HOST': '',  # leave blank for localhost
          'PORT': '',  # leave blank for localhost
        }
    }



Installing required Python Packages using pip
...............................................

Assuming you have the above pre-requisites installed, within the
`socraticqs2` directory run the following command::

  pip install -r dev_requirements.txt


Run the test suite
....................

To make sure your setup is working properly, try running the 
test suite::

  cd socraticqs2/mysite
  python manage.py test

You should see a series of tests pass successfully.

By default test suite is running on sqlite database to get a speed boost but you can change this by commenting out next lines in you local_conf.py::

    if 'test' in sys.argv or 'test_coverage' in sys.argv:
        DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'


.. warning::
   
    For Mac developer if you see ``ValueError: unknown locale: UTF-8`` do the following::

        export LC_ALL=en_US.UTF-8
        export LANG=en_US.UTF-8

    Or add this lines to your ``~/.bash_profile``


Running a test web server
...........................

You need to create a database, load it with some data,
load plugin specifications, and then
run the development web server.

You can prepare database with :doc:`fab`.

To initialize DB to run test webserver use::

    fab db.init

This task creates a new DB and transforms it into working state by the next steps:

* Drop existing DB
* Create new DB
* Apply all current Django migrations
* Load fixtures
* Deploy all FSMs

To list all available tasks use::

    fab --list

Finally, start up the development web server::

  python manage.py runserver

Start a web browser and point it at http://localhost:8000/ct/

It will prompt you to log in; the default development tester
username is ``admin`` with password ``testonly``.

User `admin` is a conventional user to use during the FSM development.

You can stop the web server by simply typing Control-C.

Security notes:

* you should not allow any outside access to localhost port 8000
  as this is insecure (e.g. an outsider could log in with the default
  credentials above and modify data in your development server).


Basic Developer Operations
---------------------------

Getting source code updates, making changes etc.
..................................................

See our :doc:`gitguide`.

Database Operations
.....................

Updating your database schema 
:::::::::::::::::::::::::::::

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
::::::::::::::::::::::::::::::::::::::::::::::

If you change the database fields for a data model in ``models.py``,
you will of course also have to change your database to match.
(Note that this means changes to the data fields that are
stored in the database; changing or adding method code on
the data classes does not change the database schema).

Django 1.7 makes this easy via its ``makemigrations`` command.

First make a backup copy of your current database (this is important,
because it's not obvious whether there is any easy way to "undo" a migration)::

    fab db.backup[:custom_branch_name]

It will create db backup file with suffix from you current git branch name
or from provided optional param ``custom_branch_name``::

    fab db.backup:test1
    .................
    [localhost] local: pg_dump courselets -U postgres -w > /path/to/proj/backups/backup.engine.test1
    [................

    Done.

Then simply type::

  python manage.py makemigrations ct

This will create a new migration file in ``ct/migrations``.  You then apply
this migration to your database exactly as we did in the previous section::

  python manage.py migrate ct

At this point you should be able to run the ``runserver``, etc.


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
     So you cannot actually move to manual testing your changes until
     you run both those steps.

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
     But you can't even start manual testing of your changes until after
     both steps.
     This is an unpleasant catch-22.

   * To run unittests you need to create migration according to your new
     code with no need to apply them to DB because test suite applies all
     migrations every time you run it to temporary DB.

   * Once you change your database schema (via ``migrate``), all *other*
     code versions (i.e. not matching the new schema stored in your
     database) will NOT run.
     This would destroy the key virtue of Git -- your ability to 
     have many different code branches and switch between them 
     effortlessly.

   * Because of this, to make developer life easier, we provide Fabriс ``db.init|db.backup|db.restore``
     tasks to init, backup and restore actions with DB. See :doc:`fab` section
     for details.


Recommended Migration Best Practices
::::::::::::::::::::::::::::::::::::

For all these reasons, I suggest you follow a simple discipline
whenever you are about to make model changes that will require
migration:

* BEFORE making those changes, make your DB backup and
  checkout a *new* Git branch, e.g.::

  Make DB backup::

    fab db.backup

  By default without providing any custom params to task it  will use 
  you current branch name as suffix for backup file.

  Next you can checkput to new bigchange::

    git checkout -b bigchange

  where ``bigchange`` is the name of your new branch.

  You should also do this if you are starting to work with
  someone else's experimental model changes, e.g.::

    fab db.backup
    git checkout -b bigchange
    git pull fred bigchange

  Then, if you ever want to switch back to your ``previous``
  branch, you can simply switch back to the database file
  that worked with ``previous``::

    git checkout previous

  Next you need to restore backuped DB::

    fab db.restore

  Note that you should NOT add any DB file to Git
  version control.

* Now you can freely run ``makemigrations`` + ``migrate``
  whenever you like, so you can test your changes.

* If you DB is in initial state without any new information stored in
  you can use :doc:`fab` to get DB ready to test and development::

      $ fab db.init

  This will give you a new DB with all migrations applied,
  initial data populated and all FSM deployed.

* If it turns out that you need to make *more* model
  changes (i.e. your model changes turned out to be inadequate
  for the feature you're implementing, and you haven't yet committed
  the inadequate models/migration),
  the best practice is to UNDO your migration
  and REGENERATE a new migration to replace it, like this::

    rm ct/migrations/0005_unitstatus.py
    fab db.restore 
    python manage.py makemigrations ct
    python manage.py migrate ct

  where ``ct/migrations/0005_unitstatus.py`` is your new
  migration file.

  If you migration can be backwarded you can use next flow::

    python manage.py migrate ct 0004
    rm ct/migrations/0005_unitstatus.py
    python manage.py makemigrations ct
    python manage.py migrate ct

  where 0004 is a number of your previous migration file.

   
Backing up, flushing, and restoring your local database
:::::::::::::::::::::::::::::::::::::::::::::::::::::::

You may wish to make and reload snapshots of your local database
as part of your development and testing process.  This is easy.

You can save a snapshot of your current database to a file, like this::

  python manage.py dumpdata > dumpdata/mysnap.json

You can flush (delete all data) from your database like this::

  python manage.py sqlflush|python manage.py dbshell

You can then restore a particular snapshot like this::

  python manage.py loaddata dumpdata/mysnap.json


Test project on PostgreSQL before making any PR
:::::::::::::::::::::::::::::::::::::::::::::::

You can develop project using sqlite db but before creating
any PR you need to init PostgreSQL DB to ensure
your code not breaking anything.

* You can create and populate db with :doc:`fab`::

    fab db.init

This will create and populate db with fixture. Then deploy all FSMs.

* Run all tests::

    python manage.py test

* Run test server and start Course from home page.
* Go to Activity Page and restore Activity.
* Go to Activity Page and cancel Activity.


Running Celery periodic tasks
:::::::::::::::::::::::::::::

We are using Celery to delete obsolete Temorary users.

To start the celery beat service use::

    celery worker -A mysite --loglevel=INFO -B

Previous command we need to call inside socraticqs2/mysite directory.
