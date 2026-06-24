import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")
DISCORD_API = "https://discord.com/api/v10"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    forest_nick = request.form.get("forest_nick", "").strip()
    minecraft_nick = request.form.get("minecraft_nick", "").strip()

    if not forest_nick or not minecraft_nick:
        return jsonify({"success": False, "message": "모든 항목을 입력해주세요."}), 400

    ok = _send_to_discord(forest_nick, minecraft_nick)
    if ok:
        return jsonify({"success": True, "message": "신청이 완료되었습니다! 관리자 승인 후 화이트리스트에 등록됩니다."})
    return jsonify({"success": False, "message": "알림 전송에 실패했습니다. 관리자에게 문의하세요."}), 500


def _send_to_discord(forest_nick: str, minecraft_nick: str) -> bool:
    payload = {
        "embeds": [{
            "title": "📋 화이트리스트 신청",
            "description": "새로운 화이트리스트 등록 요청이 들어왔습니다.",
            "color": 0x5865F2,
            "fields": [
                {"name": "🌿 숲 닉네임", "value": forest_nick, "inline": True},
                {"name": "⛏️ 마크 닉네임", "value": minecraft_nick, "inline": True},
            ]
        }],
        "components": [{
            "type": 1,
            "components": [
                {"type": 2, "style": 3, "label": "✅ 승인", "custom_id": "btn_approve"},
                {"type": 2, "style": 4, "label": "❌ 거절", "custom_id": "btn_reject"},
            ]
        }]
    }
    resp = requests.post(
        f"{DISCORD_API}/channels/{CHANNEL_ID}/messages",
        headers={"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"},
        json=payload,
        timeout=5,
    )
    return resp.ok


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
