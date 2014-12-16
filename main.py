import webapp2
import jinja2
import logging
import os
import sys
from StringIO import StringIO
from PIL import Image
from urllib import urlopen
import urllib

from google.appengine.ext import ndb
from google.appengine.api import mail

jinja_environment = jinja2.Environment(loader=
    jinja2.FileSystemLoader(os.path.dirname(__file__)))

  
#Model that represents a Photo
#class Photo(ndb.Model): 
    #author = ndb.StringProperty()
    #image_file = ndb.StringProperty() #Contains url that directs to location in static folder
    #image_height = ndb.IntegerProperty()
    #image_width = ndb.IntegerProperty()
    
#Model that represents the tracker for the occasion, photo, and message
class Tracker(ndb.Model): 
    #photo_key = ndb.KeyProperty(kind=Photo) #Key corresponding to the photo model that user selects 
    message = ndb.TextProperty()
    occasion = ndb.StringProperty()
    image_filepath = ndb.StringProperty() #Contains url that directs to location in static folder
    image_height = ndb.IntegerProperty()
    image_width = ndb.IntegerProperty()
    #Info about the sender, or the user who is sending an ecard
    sender_name = ndb.StringProperty()
    sender_email = ndb.StringProperty()
    
    #Info about the recipient of the ecard, to be inputted by the user
    rec_name = ndb.StringProperty()
    rec_email = ndb.StringProperty()
             
#Model that represents the ecard file
#class Ecard(ndb.Model):
    #tracker_key = ndb.KeyProperty(kind=Tracker) #Key corresponding to the Tracker model 

#Model w/ information needed to send card via email 
#class Card(ndb.Model):
    #Info about the sender, or the user who is sending an ecard
    #sender_name = ndb.StringProperty()
    #sender_email = ndb.StringProperty()
    
    #Info about the recipient of the ecard, to be inputted by the user
    #rec_name = ndb.StringProperty()
    #rec_email = ndb.StringProperty()
    
class LoadHandler(webapp2.RequestHandler): #handles the Loading page
  def get(self):
    template_values = {}
    template = jinja_environment.get_template('load.html')
    self.response.write(template.render(template_values))
    

class MainHandler(webapp2.RequestHandler): #handles the Choose an Occasion page
  def get(self):
    template_values = {}
    template = jinja_environment.get_template('main.html')
    self.response.write(template.render(template_values))
    
  def post(self):
    occasion = self.request.get("occasion")
    current_tracker = Tracker(occasion = occasion)
    key = current_tracker.put()
    urlkey = key.urlsafe()
    self.redirect("/photo?key="+urlkey)
    
    

class PhotoHandler(webapp2.RequestHandler): #handles the Choose a Photo page
  def get(self):
    template_values = {}
    key = self.request.get("key")
    if key:
        urlkey = ndb.Key(urlsafe = key)
        tracker = urlkey.get()
        occasion = tracker.occasion
        template_values["templatekey"] = key
    
    if key and occasion:
        #create list of photos
        photolist = []
        path = os.path.dirname(__file__)+"/newstat/photos/"+occasion+"/"
        realpath = "/newstatic/photos/"+occasion+"/"
        
        dirs = os.listdir(path)
    
        for i in dirs: #loop through all photos in a directory
            if i.endswith(".jpg"):
                photolist.append(i)
                    
        template_values["photos"] = photolist
        template_values["occasion"] = occasion
    
    template = jinja_environment.get_template('photo.html')
    self.response.write(template.render(template_values))
    
  def post(self):
    
    key = self.request.get("key")
    if key:
        urlkey = ndb.Key(urlsafe = key)
        tracker = urlkey.get()
    
    #Code for getting information about photo
    
        image_filepath = tracker.occasion+"/"+self.request.get("image_filepath")
    #image_filepath = "bastilleday.jpg"
        image_file = Image.open(StringIO(urlopen(os.path.dirname(__file__)+"/newstat/photos/"+image_filepath).read()))
        image_height = image_file.size[1]
        image_width = image_file.size[0]
    #image_author = ""
    
        tracker.image_height = image_height 
        tracker.image_filepath = "/newstatic/photos/" + image_filepath
        tracker.image_width = image_width
        tracker.put()

    self.redirect("/message?key="+key)
    
    
    
        
class MessageHandler(webapp2.RequestHandler): #handles the Choose a Message page
    def get(self):
        template_values = {}  
        key = self.request.get("key")
        if key:
            urlkey = ndb.Key(urlsafe = key)
            tracker = urlkey.get()
            occasion = tracker.occasion
            template_values["templatekey"] = key
    
        if key and occasion:
            #create list of messages mapping to occasion
            message_file = open("newstat/messages/"+occasion+".txt")
            message_list = []
    
            for line in message_file:
                newline = '{:83s}'.format(line)
                #realline = '<br />\n'.join(newline.split('\n'))
                unicode_line = newline.decode('utf-8')
                message_list.append(unicode_line)
    
            template_values["messages"] = message_list
        
        template = jinja_environment.get_template('message.html')
        self.response.write(template.render(template_values))
    
    def post(self):
        message = self.request.get("message")
    
        key = self.request.get("key")
        urlkey = ndb.Key(urlsafe = key)
        tracker = urlkey.get()
    
        tracker.message = message
        tracker.put()
        self.redirect("/confirm?key="+key)
    
class ConfirmHandler(webapp2.RequestHandler): #handles the preview/confirm page
  def get(self):
        template_values = {}  
        previewtemplate_values = {}  
        key = self.request.get("key")
        if key:
            urlkey = ndb.Key(urlsafe = key)
            tracker = urlkey.get()
            template_values["templatekey"] = key
            previewtemplate_values["image_filepath"] = tracker.image_filepath
            template_values["image_filepath"] = tracker.image_filepath
            previewtemplate_values["image_height"] = tracker.image_height
            template_values["image_height"] = tracker.image_height
            previewtemplate_values["image_width"] = tracker.image_width
            template_values["image_width"] = tracker.image_width
            previewtemplate_values["message"] = tracker.message
            template_values["message"] = tracker.message
        
        previewtemplate = jinja_environment.get_template('preview.html')
        previewtemplate.render(previewtemplate_values) 
        template = jinja_environment.get_template('confirm.html')   
        self.response.write(template.render(template_values))
       
  def post(self):
    key = self.request.get("key")
    urlkey = ndb.Key(urlsafe = key)
    self.redirect("/final?key="+key)    
    
class FinalHandler(webapp2.RequestHandler): #handles the final page with send information
  def get(self):
        template_values = {}  
        key = self.request.get("key")
        if key:
            urlkey = ndb.Key(urlsafe = key)
            tracker = urlkey.get()
            template_values["tracker"] = tracker
            template_values["templatekey"] = key
            
        template = jinja_environment.get_template('final_confirmation.html')
        self.response.write(template.render(template_values))
       
  def post(self):
    key = self.request.get("key")
    urlkey = ndb.Key(urlsafe = key)
    tracker = urlkey.get()
    previewtemplate_values ={}
    sender_name = self.request.get("sender_name")
    sender_email = self.request.get("sender_email")
    rec_name = self.request.get("rec_name")
    rec_email = self.request.get("rec_email")
    
    user_address = rec_email
    sender_address = sender_email #use ecard.cssi@gmail.com but display in body the sender's email
    subject = "Someone sent you a Kinetic e-card!"
    
    previewtemplate_values["image_filepath"] = "http://mls-ecard.appspot.com/"+tracker.image_filepath
    previewtemplate_values["message"] = tracker.message
    previewtemplate_values["image_height"] = tracker.image_height
    previewtemplate_values["image_width"] = tracker.image_width
    previewtemplate = jinja_environment.get_template('preview.html')

    body = sender_name+" (their email is "+sender_email+" ) sent you a Kinetic ecard! Please click this link: "+ "http://mls-ecard.appspot.com/"+"preview?key="+key
    #mail.send_mail(sender_address, user_address, subject, body) 
    email = mail.EmailMessage(sender="meghabs@gmail.com", subject=sender_name+" sent you a Kinetic e-card!", to=user_address, body = body)
    email.send()
    key = self.request.get("key")
    urlkey = ndb.Key(urlsafe = key)
    self.redirect("/sent?key="+key)
    
class SentHandler(webapp2.RequestHandler): #handles the final display page
  def get(self):
        template_values = {}  
        key = self.request.get("key")
        if key:
            urlkey = ndb.Key(urlsafe = key)
            tracker = urlkey.get()
            template_values["tracker"] = tracker
            template_values["templatekey"] = key
            
        template = jinja_environment.get_template('sent_mail.html')
        self.response.write(template.render(template_values))

class PreviewHandler(webapp2.RequestHandler): #handles the link people sent
    def get(self):
        key = self.request.get("key")
        if key:
            urlkey = ndb.Key(urlsafe = key)
            tracker = urlkey.get()
            template_values = {}
            template_values["image_filepath"] = "http://mls-ecard.appspot.com/"+tracker.image_filepath
            template_values["message"] = tracker.message
            template_values["image_height"] = tracker.image_height
            template_values["image_width"] = tracker.image_width
            template = jinja_environment.get_template('framepreview.html')
            self.response.write(template.render(template_values))
        else:
            self.response.write("Not found!")
    
    

routes = [
    ('/photo', PhotoHandler),
    ('/message', MessageHandler),
    ('/preview', PreviewHandler),
    ('/final', FinalHandler),
    ('/confirm', ConfirmHandler),
    ('/sent', SentHandler),
    ('/main', MainHandler),
    ('/.*', LoadHandler)
]

app = webapp2.WSGIApplication(routes, debug=True)
