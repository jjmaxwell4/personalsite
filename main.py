#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import re

import webapp2
import jinja2

from google.appengine.ext import db
from google.appengine.api import users

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

#Global user/admin used for Login Purposes
user = users.get_current_user()
admin = users.is_current_user_admin()

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class Home(BaseHandler):
    def get(self):
        self.render('home.html')

class Ping(BaseHandler):
    def get(self):
        self.render('ping.html')

class Reads(BaseHandler):
    def get(self):
        self.render('read.html')

class Education(BaseHandler):
    def get(self):
        self.render('education.html')

class Resume(BaseHandler):
    def get(self):
        self.render('resume.html')

###### Blog ######
def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class BlogFront(BlogHandler):
    def get(self):
        admin = users.is_current_user_admin()
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts, admin = admin)

class PostPage(BlogHandler):
    def get(self, post_id):
        admin = users.is_current_user_admin()
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post, admin = admin)

class NewPost(BlogHandler):
    def get(self):
        if users.is_current_user_admin():
            self.render('newpost.html')

    def post(self):
        have_error = False

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content and users.is_current_user_admin():
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

class Login(BlogHandler):
    def get(self):
        admin = users.is_current_user_admin()
        if admin:
            greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                        (user.nickname(), users.create_logout_url("/blog")))
        else:
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/blog"))

        self.response.out.write("<html><body>%s</body></html>" % greeting)

class Edit(BlogHandler):
    def get(self, post_id):
        if users.is_current_user_admin():
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)   
            subject = post.subject
            content = post.content
            self.render("newpost.html", subject=subject, content=content)   

    def post(self, post_id):
        have_error = False

        subject = self.request.get('subject')
        content = self.request.get('content')


        if subject and content and users.is_current_user_admin():
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)   
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/%s' % str(post.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)  

app = webapp2.WSGIApplication([('/', Home),
								('/read/', Reads),
								('/education/', Education),
								('/resume/', Resume),
                                ('/blog/?', BlogFront),
                                ('/blog/([0-9]+)', PostPage),
                                ('/blog/([0-9].*)/edit', Edit),
                                ('/blog/newpost', NewPost),
                               ('/blog/login', Login),
                               ('/ping/', Ping),
                               ],
                              debug=True)
