feed2pod
===

You have: a site with a feed, which has some podcasty elements. But not enough of them for your podcast client to actually use it.

You'd like: to fix this.

This script is very personal-use. I have a few feeds I want to do this to. I'm not actively going for the general case so long as those work. If you find this useful and want to make it work on feeds which are currently broken: go nuts, submit a pull request, I'll accept it.

Setup
---

You need Python 3.

My recommended setup process is:

    $ pyvenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

...adjust as needed. Just make sure the dependencies from `requirements.txt` get installed somehow.

Usage
---

    $ python3 feed2pod.py [[URL]] > feed.xml

A new file will appear named `feed.xml`.

You'll need to put it somewhere a podcast client can access it.

