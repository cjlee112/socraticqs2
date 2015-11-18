Installation and setup using Docker
-----------------------------------

Docker gives conviniet and simple way to install projest on the local machine.

 First of all you have to do 2 important steps:

* Get your own copy of the Socraticqs2 source code. To do that you have to go to
  our Github repository https://github.com/cjlee112/socraticqs2 and Fork the
  repository (you'll need a Github account to do this). This creates your own
  repository in your Github account, which you can make changes to, and issue
  pull requests for us to incorporate your changes.  Next clone the repository
  to your local computer, one of two ways:

  **via the command line**: click the "HTTPS clone URL" *copy to clipboard*
  button on your GitHub repository page, and paste it into a terminal
  command like so (substitute your correct clone URL)::

    git clone https://github.com/YOURNAME/socraticqs2.git

  This will clone the repository to a new directory ``socraticqs2/``
  in your current directory.  We recommend you also add our main
  repository as a "remote" repository called ``upstream``::

    cd socraticqs2
    git remote add upstream https://github.com/cjlee112/socraticqs2.git

  **via Github for Windows or Mac**: you can just click the Clone to Desktop
  link on the webpage for your fork (repository).
* Install Docker on your machine, you can download it from https://www.docker.com.

      **For not Linux users only**
      After installing Docker it will make you docker-machine for your images, named
      'default' if you want to create you specific docker machine you can do it with
      command
      ::
          docker-machine create --driver virtualbox <name-of-your-machine>

      You can see the machine you have created by running the
      ::
          docker-machine ls

      To connect Docker to 'default' or your machine, run:
      ::
         eval "$(docker-machine env <name-of-machine>)"

When you get your Docker installation done. You have to go to **socraticqs2**
folder and run:
::
    docker-compouse up

After that you'll get two Docker containers: one for the project and one for
the Postgres database. While making containers, file
/mysite/mysite/settings/docker_conf.py is copying into file local_conf.py if
you already have local_conf.py file it will leave your file without changes.
If you want to use your local_conf.py, but want to connect to Docker database
container you have to add such database preferences to your local_conf.py:
::
    DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.postgresql_psycopg2',
       'NAME': 'postgres',
       'USER': 'postgres',
       'HOST': 'db',
       'PORT': 5432,
              }
   }

To get connect to the runnig project on Linux machine you can just go to link
::
    http://127.0.0.1:8000

To get connect to it from **OSX** or **Windows** you have, at first, get IP of
your Docker machine
::
    docker-machine ip <name-of-machine>

And connect usig this IP address:
::
    http://<ip-adress>:8000

One more thing you have to do befor start to use Socraticqs2 is migrations.
To do migrations you have to shut down containers and rum command
::
    docker-compose run web python manage.py migrate

In such a way you can run any command related to the project inside the Docker
container. Also you can start Fabric deployment tool to get databases
into initial state.