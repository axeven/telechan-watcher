from datetime import datetime, timedelta, timezone

from flask import Flask, redirect, render_template, request, url_for

import db

app = Flask(__name__)

DISPLAY_TZ = timezone(timedelta(hours=7))


@app.template_filter("wib")
def to_wib(iso_ts):
    if not iso_ts:
        return "-"
    dt = datetime.fromisoformat(iso_ts).astimezone(DISPLAY_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S WIB")


@app.route("/")
def index():
    conn = db.get_connection()
    channels = db.list_channels(conn)
    conn.close()
    return render_template("index.html", channels=channels)


@app.route("/channel/<int:channel_id>")
def channel_detail(channel_id):
    conn = db.get_connection()
    channel = db.get_channel(conn, channel_id)
    messages = db.list_messages(conn, channel_id)
    conn.close()
    if channel is None:
        return "Channel not found", 404
    return render_template("channel.html", channel=channel, messages=messages)


@app.route("/channel/<int:channel_id>/label", methods=["POST"])
def update_label(channel_id):
    label = request.form.get("label", "").strip()
    if label:
        conn = db.get_connection()
        db.update_label(conn, channel_id, label)
        conn.close()
    return redirect(url_for("channel_detail", channel_id=channel_id))


@app.route("/channel/<int:channel_id>/pause", methods=["POST"])
def pause_channel(channel_id):
    conn = db.get_connection()
    db.set_paused(conn, channel_id, True)
    conn.close()
    return redirect(request.referrer or url_for("index"))


@app.route("/channel/<int:channel_id>/unpause", methods=["POST"])
def unpause_channel(channel_id):
    conn = db.get_connection()
    db.set_paused(conn, channel_id, False)
    conn.close()
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    db.init_db()
    app.run(host="0.0.0.0", debug=True)
