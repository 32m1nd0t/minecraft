import os
import requests
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")
INQUIRY_CHANNEL_ID = os.environ.get("DISCORD_INQUIRY_CHANNEL_ID")
DISCORD_API = "https://discord.com/api/v10"

for _var, _val in [("DISCORD_BOT_TOKEN", BOT_TOKEN), ("DISCORD_CHANNEL_ID", CHANNEL_ID), ("DISCORD_INQUIRY_CHANNEL_ID", INQUIRY_CHANNEL_ID)]:
    if not _val:
        print(f"[경고] 환경변수 {_var} 가 설정되지 않았습니다.")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
@limiter.limit("5 per minute; 20 per hour")
def submit():
    forest_nick = request.form.get("forest_nick", "").strip()
    minecraft_nick = request.form.get("minecraft_nick", "").strip()

    if not forest_nick or not minecraft_nick:
        return jsonify({"success": False, "message": "모든 항목을 입력해주세요."}), 400
    if len(minecraft_nick) > 16:
        return jsonify({"success": False, "message": "마크 닉네임은 16자 이하여야 합니다."}), 400
    if len(forest_nick) > 50:
        return jsonify({"success": False, "message": "숲 닉네임이 너무 깁니다."}), 400

    ok = _send_to_discord(forest_nick, minecraft_nick)
    if ok:
        return jsonify({"success": True, "message": "신청이 완료되었습니다! 관리자 승인 후 화이트리스트에 등록됩니다."})
    return jsonify({"success": False, "message": "알림 전송에 실패했습니다. 관리자에게 문의하세요."}), 500


def _send_to_discord(forest_nick: str, minecraft_nick: str) -> bool:
    if not BOT_TOKEN or not CHANNEL_ID:
        print("[오류] DISCORD_BOT_TOKEN 또는 DISCORD_CHANNEL_ID 환경변수 누락")
        return False
    payload = {
        "allowed_mentions": {"parse": []},
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


@app.route("/inquiry")
def inquiry():
    return render_template("inquiry.html")


@app.route("/inquiry/submit", methods=["POST"])
@limiter.limit("5 per minute; 20 per hour")
def inquiry_submit():
    forest_nick = request.form.get("forest_nick", "").strip()
    minecraft_nick = request.form.get("minecraft_nick", "").strip()
    content = request.form.get("content", "").strip()

    if not forest_nick or not content:
        return jsonify({"success": False, "message": "필수 항목을 입력해주세요."}), 400
    if len(content) > 1000:
        return jsonify({"success": False, "message": "문의 내용은 1000자 이하로 입력해주세요."}), 400
    if len(forest_nick) > 50:
        return jsonify({"success": False, "message": "숲 닉네임이 너무 깁니다."}), 400

    ok = _send_inquiry_to_discord(forest_nick, minecraft_nick, content)
    if ok:
        return jsonify({"success": True, "message": "문의가 전달되었습니다! 관리자 확인 후 답변드릴게요."})
    return jsonify({"success": False, "message": "전송에 실패했습니다. 다시 시도해주세요."}), 500


def _send_inquiry_to_discord(forest_nick: str, minecraft_nick: str, content: str) -> bool:
    if not BOT_TOKEN or not INQUIRY_CHANNEL_ID:
        print("[오류] DISCORD_BOT_TOKEN 또는 DISCORD_INQUIRY_CHANNEL_ID 환경변수 누락")
        return False
    fields = [{"name": "숲 닉네임", "value": forest_nick, "inline": True}]
    if minecraft_nick:
        fields.append({"name": "마크 닉네임", "value": minecraft_nick, "inline": True})
    fields.append({"name": "문의 내용", "value": content, "inline": False})

    payload = {
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": "문의 접수",
            "color": 0xEB459E,
            "fields": fields,
        }]
    }
    resp = requests.post(
        f"{DISCORD_API}/channels/{INQUIRY_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"},
        json=payload,
        timeout=5,
    )
    return resp.ok


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
