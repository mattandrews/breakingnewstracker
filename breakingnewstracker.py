import fix_path
import os
import sys
import cgi
import datetime
import urllib
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from lib import feedparser

class BreakingStory(db.Model):
    source = db.StringProperty()
    url = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    headline = db.StringProperty(multiline=True)
    description = db.StringProperty(multiline=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        breakingstories = getAllBreakingStories("bbc")
        for b in breakingstories:
            self.response.out.write(b.headline + ' (' + b.date.isoformat() + ') <br />')

# can be run on a cron schedule. should avoid duplication of headlines 
# (URLs aren't unique, they tend to point to bbc homepage). should be 
# optimised - currently loops through (up to) entire table of stored 
# articles to check for dupes
class FetchBreakingNews(webapp.RequestHandler):
    def get(self):

        breakingstories = getAllBreakingStories("bbc")
        feed = feedparser.parse('http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/breaking_news/rss.xml')
        articles = feed['entries']

        for a in articles:
            if not headlineInList(a['title'], breakingstories):
                breakingstory = BreakingStory()
                breakingstory.source = 'bbc'
                breakingstory.url = a['link']
                breakingstory.headline = a['title']
                breakingstory.description = a['description']
                breakingstory.put()
                self.response.out.write("added story: " + a['title'] + ' (' + a['link'] + ') <br />')

application = webapp.WSGIApplication([
    ('/', MainPage),('/fetch', FetchBreakingNews)], 
    debug=True)

def getAllBreakingStories(source):
    breakingstories = BreakingStory.all()
    breakingstories.filter("source = ", source)
    breakingstories.order("-date")
    return breakingstories

def headlineInList(headline, list):
    for l in list:
        if l.headline == headline:
            return True
    return False

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()