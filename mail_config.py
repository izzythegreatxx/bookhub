'''
Configuration for Flask-Mail, including initialization of the Mail object for sending emails in the application.
This module sets up the mail configuration and provides a Mail instance that can be imported and used in other parts of the application, 
such as in authentication routes for sending verification emails.
'''

from flask_mail import Mail

mail = Mail()
