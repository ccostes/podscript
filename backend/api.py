from flask import Flask, request, render_template
from db import connect
from storage import get_podcasts, import_feed, get_episode, update_episode_state, get_episodes_with_state, update_feeds
"""
Exposes the storage layer via a REST API
"""
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/update")
def update():
    app.logger.info(f"Updating feeds")
    with connect() as connection:
        update_feeds(connection=connection)
    return '', 204

@app.route("/podcasts")
def list_podcasts():
    with connect() as connection:
        return get_podcasts(connection=connection)

@app.route("/podcasts", methods=['POST'])
def add_podcast():
    url = request.get_json()['url']
    app.logger.info(f"adding feed, url: {url}")
    with connect() as connection:
        import_feed(connection=connection, url=url)
    return '', 204


@app.route("/episodes/<id>")
def retrieve_episode(id):
    with connect() as connection:
        return get_episode(connection=connection, id=id)

@app.route("/episodes/<id>/state", methods=['PUT'])
def put_episode_state(id):
    new_state = request.get_json()['state']
    app.logger.info(f"Updating state for episode {id} to {new_state}")
    with connect() as connection:
        updated = update_episode_state(connection=connection, id=id, new_state=new_state)
        return updated

@app.route("/episodes/state/<state>")
def episodes_by_state(state):
    with connect() as connection:
        return get_episodes_with_state(connection=connection, state=state)