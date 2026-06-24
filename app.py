import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from config import FLASK_PORT

app = Flask(__name__)

# 봇의 event loop를 저장 (bot.py에서 주입)
_bot_loop: asyncio.AbstractEventLoop = None
_bot_instance = None

def set_bot(bot_loop, bot_obj):
    global _bot_loop, _bot_instance
    _bot_loop = bot_loop
    _bot_instance = bot_obj


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    forest_nick = request.form.get("forest_nick", "").strip()
    minecraft_nick = request.form.get("minecraft_nick", "").strip()

    if not forest_nick or not minecraft_nick:
        return jsonify({"success": False, "message": "모든 항목을 입력해주세요."}), 400

    if _bot_loop is None or _bot_instance is None:
        return jsonify({"success": False, "message": "봇이 아직 준비되지 않았습니다. 잠시 후 다시 시도해주세요."}), 503

    from bot import send_approval_request
    asyncio.run_coroutine_threadsafe(
        send_approval_request(forest_nick, minecraft_nick),
        _bot_loop
    )

    return jsonify({"success": True, "message": "신청이 완료되었습니다! 관리자 승인 후 화이트리스트에 등록됩니다."})


def run_flask():
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False)


def start_flask_thread():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
