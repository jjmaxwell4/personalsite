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
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class NewPost(BlogHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        have_error = False
        password = self.request.get('password')
        params = dict(password = password)

        if password == 'secure':
            self.write('')
        else:
            params['error_password'] = "That wasn't a valid password."
            have_error = True
            self.render('login.html', **params)

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

class Login(BlogHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        have_error = False
        password = self.request.get('password')
        params = dict(password = password)

        if password == 'secure':
            self.redirect('newpost', password)
        else:
            params['error_password'] = "That wasn't a valid password."
            have_error = True
            self.render('login.html', **params)

app = webapp2.WSGIApplication([('/', Home),
								('/read/', Reads),
								('/education/', Education),
								('/resume/', Resume),
                                ('/blog/?', BlogFront),
                                ('/blog/([0-9]+)', PostPage),
                                ('/blog/newpost', NewPost),
                               ('/blog/login', Login),
                               ('/ping/', Ping),
                               ],
                              debug=True)
