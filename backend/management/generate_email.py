import logging, json 
import pystache
from pathlib import Path

"""
Generate the html email content for a given episode transcript.

Expects art image be attached to the email with the same file name as the 
art_url filename on the podcast record.
"""
email_template = (Path() / 'email_template/template.html').read_text()

def generate_email(episode, image_extension, transcript):
    transcript_html = ""
    for block in transcript:
        transcript_html += "<p><strong>[" + block['speaker'] + "]</strong></p>"
        for line in block['text']:
            transcript_html += "<p>" + line + "</p>"

    template_params = {
        'episode_title': episode['title'],
        'episode_description': episode['description_html'],
        'body': transcript_html,
        'link': episode['link'],
        'image_extension': image_extension,
    }
    # logging.info(f"Rendering email html with params: {template_params}")
    email_html = pystache.render(email_template, template_params)
    return email_html

def main(transcript_file):
    episode = {
        'description_html': """<p>Days after voters rejected his vision for the country in the midterms, former President Donald J. Trump is expected to announce a third run for president.</p><p>Despite the poor results for candidates he backed, why are Republican leaders powerless to stop him?</p><p>Guest: <a href="https://www.nytimes.com/by/maggie-haberman?smid=pc-thedaily">Maggie Haberman</a>, a White House correspondent for The New York Times.</p><p>Background reading: </p><ul><li>Republicans may still win the House. But an underwhelming showing has the party wrestling with what went wrong:<a href="https://www.nytimes.com/2022/11/11/us/politics/republicans-midterm-elections.html"> Was it bad candidates, a bad message or Mr. Trump?</a></li><li>Mr. Trump has<a href="https://www.nytimes.com/2022/11/09/us/politics/trump-republicans-midterms.html"> faced unusual public attacks from across the Republican Party</a>.</li><li>Republicans pushing to move past the former president face one big obstacle:<a href="https://www.nytimes.com/2022/11/14/us/politics/trump-presidential-campaign-voters.html"> His voters</a>.</li></ul><p>For more information on today’s episode, visit <a href="http://nytimes.com/thedaily?smid=pc-thedaily">nytimes.com/thedaily</a>. Transcripts of each episode will be made available by the next workday. </p>""",
        'title': "Another Trump Campaign",
        'link': "https://www.nytimes.com/the-daily",
        'art_url': "https://is1-ssl.mzstatic.com/image/thumb/Podcasts115/v4/1c/ac/04/1cac0421-4483-ff09-4f80-19710d9feda4/mza_12421371692158516891.jpeg/600x600bb.jpg",
    }
    with open(transcript_file) as f:
        transcript = json.load(f)
    with open('email.html', 'w') as f:
        f.write(generate_email(episode=episode, transcript=transcript))

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main('transcript.json')
    