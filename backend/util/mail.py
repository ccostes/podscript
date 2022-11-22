import logging, smtplib, ssl
from pathlib import Path
from dotenv import dotenv_values
import urllib.request
from urllib.parse import urlparse
from os.path import splitext
import mimetypes
from email.mime.image import MIMEImage
from email.message import EmailMessage

"""
Sends email
"""
env = dotenv_values('.env.local')
from_email = 'Podscript<noreply@podscript.org>'

def get_ext(url):
    """Returns the file extension for a url, or ''."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext

def publish(to_email, subject, body, image_url=None):
    message = EmailMessage()
    message['Subject'] = subject
    message["From"] = from_email
    message["To"] = to_email

    # set plain text body
    message.set_content("Plain text body")

    # add HTML
    message.add_alternative(body, subtype='html')

    # Create content-ID
    img_extension = get_ext(image_url)
    cid = '<logo' + img_extension + '>'
    with urllib.request.urlopen(image_url) as f:
        img = MIMEImage(f.read(), _subtype=mimetypes.guess_type('f' + img_extension))
        img.add_header('Content-ID', cid)
        img.add_header('Content-Disposition', 'inline', filename='logo' + img_extension)
        # attach it
        message.attach(img)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(env['GMAIL_APP_USER'], env['GMAIL_APP_PASSWORD'])
        server.sendmail(from_email, to_email, message.as_string())

def main():
    body = (Path() / 'email/email.html').read_text()
    art_url = "https://is1-ssl.mzstatic.com/image/thumb/Podcasts115/v4/1c/ac/04/1cac0421-4483-ff09-4f80-19710d9feda4/mza_12421371692158516891.jpeg/600x600bb.jpg"

    publish(
        to_email='costes.c@gmail.com', 
        subject = 'The Daily: Another Trump Campaign', 
        body=body,
        image_url=art_url
    )

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()