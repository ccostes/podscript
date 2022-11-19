import logging, smtplib, ssl
from pathlib import Path
from dotenv import dotenv_values
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
"""
Sends email
"""
env = dotenv_values('.env.local')
from_email = 'Podscript<noreply@podscript.org>'

def publish(to_email, subject, body, image_url):
    message = MIMEMultipart('mixed')
    message['Subject'] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.attach(MIMEText(body, "html"))

    with urllib.request.urlopen(image_url) as f:
        img = MIMEImage(f.read())
    img_path = Path() / image_url
    img.add_header('Content-ID', f'<{img_path.name}>')
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