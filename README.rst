=================
Runscript package
=================

It is not a rare case when the project has a few tasks to run periodically or at certain times e.g. deploying the project on the server or initial generation of data for new work place. Runscript package provides simple `run` utility that you can use to run your tasks. The `run` command is nothing more than launcher of the `main()` function of one of your scripts stored in predefined directory. Also `run` utility slightly simplifies the handling of command line arguments.


Real world example
==================

Suppose you need to save some data from database into text file. For example, you have some web-site with user accounts and you want to dump the ID of each user account and also its email. Also you want to be able to choose the country of accounts to dump. Create "script/" directory in the root of your project and then create the file "script/dump.py" with content::

    import pymongo

    def setup_arg_parser(parser):
        parser.add_argument('-c', '--count')

    def main(count, **kwargs):
        with open('export/user.csv', 'w') as out:
            for user in db.user.find({'country': country}):
                out.write('%s:%s\n' % (user['_id'], user['email'])) 


Few words about what is going here. The value of `parser` option that is passed to `setup_arg_parser` is the instance of `ArgumentParser` class. You can add any option you need or just do not specify `setup_arg_parser` in you script. If you define some custom options then their values will be passed in `**kwargs` arguments to your `main` function.

OK, now you can run the following command from the console::

    $ run dump

That's all :) Of course this is not the rocket science, but I found that this simple script launcher saved me a lot of time.
