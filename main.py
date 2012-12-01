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

class Projects(BaseHandler):
    def get(self):
        self.render('projects.html')

class Resume(BaseHandler):
    def get(self):
        self.render('resume.html')

class Quotes(BaseHandler):
    def get(self):
        self.render('quotes.html')

###### Blog ######
def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '</p> <p>&nbsp&nbsp&nbsp&nbsp')
        return render_str("post.html", p = self)

    def render_snipit(self):
        self.content = self.content.replace('\n', '</p> <p>&nbsp&nbsp&nbsp&nbsp')
        snipit = ' '.join(self.content.split(' ')[:100])+" ..."
        self._render_text = snipit
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
            greeting = ("Only Administrators Should be Back Here! (<a href=\"%s\">sign out</a>)" %
                        ( users.create_logout_url("")))
        else:
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url(""))

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
								('/projects/', Projects),
								('/resume/', Resume),
                                ('/blog/?', BlogFront),
                                ('/blog/([0-9]+)', PostPage),
                                ('/blog/([0-9].*)/edit', Edit),
                                ('/blog/newpost', NewPost),
                               ('/login', Login),
                               ('/ping/', Ping),
                               ('/quotes/', Quotes)
                               ],
                              debug=True) 
