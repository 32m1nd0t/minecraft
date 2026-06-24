import json
import os
import asyncio
import discord
from discord.ext import commands
from config import DISCORD_BOT_TOKEN, APPROVAL_CHANNEL_ID, MINECRAFT_SERVER_PATH

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def add_to_whitelist(minecraft_nick: str) -> tuple[bool, str]:
    try:
        whitelist_path = os.path.join(MINECRAFT_SERVER_PATH, "whitelist.json")

        if not os.path.exists(whitelist_path):
            with open(whitelist_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(whitelist_path, "r", encoding="utf-8") as f:
            whitelist = json.load(f)

        existing_names = [entry.get("name", "").lower() for entry in whitelist]
        if minecraft_nick.lower() in existing_names:
            return False, f"`{minecraft_nick}`은(는) 이미 화이트리스트에 등록되어 있습니다."

        whitelist.append({"uuid": "", "name": minecraft_nick})

        with open(whitelist_path, "w", encoding="utf-8") as f:
            json.dump(whitelist, f, indent=2, ensure_ascii=False)

        return True, f"`{minecraft_nick}` 화이트리스트 등록 완료!"

    except Exception as e:
        return False, f"오류 발생: {str(e)}"


class ApprovalView(discord.ui.View):
    def __init__(self, forest_nick: str, minecraft_nick: str):
        # timeout=None → 봇 재시작 후에도 버튼 살아있음
        super().__init__(timeout=None)
        self.forest_nick = forest_nick
        self.minecraft_nick = minecraft_nick

    @discord.ui.button(label="✅ 승인", style=discord.ButtonStyle.success, custom_id="btn_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        success, message = add_to_whitelist(self.minecraft_nick)

        if success:
            embed = discord.Embed(title="✅ 화이트리스트 등록 완료", color=discord.Color.green())
        else:
            embed = discord.Embed(title="⚠️ 등록 실패", color=discord.Color.yellow())

        embed.add_field(name="숲 닉네임", value=self.forest_nick, inline=True)
        embed.add_field(name="마크 닉네임", value=self.minecraft_nick, inline=True)
        embed.add_field(name="처리자", value=interaction.user.mention, inline=False)
        embed.set_footer(text=message)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ 거절", style=discord.ButtonStyle.danger, custom_id="btn_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="❌ 신청 거절됨", color=discord.Color.red())
        embed.add_field(name="숲 닉네임", value=self.forest_nick, inline=True)
        embed.add_field(name="마크 닉네임", value=self.minecraft_nick, inline=True)
        embed.add_field(name="처리자", value=interaction.user.mention, inline=False)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)


async def send_approval_request(forest_nick: str, minecraft_nick: str):
    channel = bot.get_channel(APPROVAL_CHANNEL_ID)
    if channel is None:
        print(f"[오류] 채널 ID {APPROVAL_CHANNEL_ID}를 찾을 수 없습니다.")
        return

    embed = discord.Embed(
        title="📋 화이트리스트 신청",
        description="새로운 화이트리스트 등록 요청이 들어왔습니다.",
        color=discord.Color.blue()
    )
    embed.add_field(name="🌿 숲 닉네임", value=forest_nick, inline=True)
    embed.add_field(name="⛏️ 마크 닉네임", value=minecraft_nick, inline=True)

    view = ApprovalView(forest_nick=forest_nick, minecraft_nick=minecraft_nick)
    await channel.send(embed=embed, view=view)


@bot.event
async def on_ready():
    print(f"[봇] {bot.user} 로그인 완료")

    # Flask에 event loop 주입
    import app as flask_app
    flask_app.set_bot(asyncio.get_event_loop(), bot)
    flask_app.start_flask_thread()

    print(f"[Flask] http://localhost:{flask_app.FLASK_PORT} 에서 실행 중")


def run_bot():
    bot.run(DISCORD_BOT_TOKEN)
