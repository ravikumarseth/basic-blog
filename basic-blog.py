import webapp2
import os
import jinja2
import re
import libs.bcrypt

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class BlogPost(db.Model):
    title = db.StringProperty(required = True)
    blog = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    ids = db.IntegerProperty()

class MainPage(Handler):
    def get(self):
        blogs = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC")
        self.render("blogList.html", blogs=blogs)

class NewPost(Handler):
    def render_newpost(self, title="", blog="", error=""):
        arts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC")
        self.render("newpost.html", title=title, blog=blog, error=error)

    def get(self):
        self.render_newpost()

    def post(self):
        title = self.request.get("subject")
        blog = self.request.get("content")

        if title and blog:
            num = 0
            for c in title:
                num += ord(c)
            BlogPost(key_name=str(num), title=title, blog=blog, ids= num).put()
            self.redirect('/blog/%d' % int(num))
        else:
            error = "We need both title and blog content!!"
            self.render_newpost(title, blog, error)

class Blog(Handler):
    def get(self, key):
        blogPost = BlogPost.get_by_key_name(key)
        title = blogPost.title
        blog = blogPost.blog
        self.render("blog.html", title=title, blog=blog)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

def valid_username(username):
    return USER_RE.match(username)
def valid_password(password):
    return PASS_RE.match(password)
def valid_email(email):
    return EMAIL_RE.match(email)

class SignupPage(Handler):
    def get(self):
        self.render('signup_page.html', first_login="1")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        username_valid = username and valid_username(username)
        password_valid = password and valid_password(password)
        email_valid = email and valid_email(email)
        verify_valid = verify and (password == verify)

        if(username and username_valid and password and password_valid and verify and verify_valid):
            self.response.headers.add_header('Set-Cookie', 'username=%s' % str(username))
            self.response.headers.add_header('Set-Cookie', 'pass=%s|%s' % (str(password), libs.bcrypt.hashpw(password, libs.bcrypt.gensalt())))
            self.redirect('/welcome_page')
        else:
            self.render('signup_page.html', verify_valid = verify_valid, username = username, password = password, username_valid = username_valid, password_valid = password_valid)

class WelcomePage(Handler):
    def get(self):
        username = self.request.cookies.get('username')
        passs = self.request.cookies.get('pass')
        if passs:
            hashed = passs.split("|")[1]
            password = passs.split("|")[0]
            h = libs.bcrypt.hashpw(password, hashed)
        if (username and passs and (valid_username(username)) and (h == hashed)):
            self.render("welcome_page.html", username=username)
        else:
            self.redirect('/signup')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newpost', NewPost),
    ('/blog/(\d+)', Blog),
    ('/signup', SignupPage),
    ('/welcome_page', WelcomePage)
], debug=True)
