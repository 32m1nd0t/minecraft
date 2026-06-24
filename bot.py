import json
import os
import discord
from discord.ext import commands
from config import DISCORD_BOT_TOKEN, MINECRAFT_SERVER_PATH

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

        if any(e.get("name", "").lower() == minecraft_nick.lower() for e in whitelist):
            return False, f"`{minecraft_nick}`은(는) 이미 등록되어 있습니다."

        whitelist.append({"uuid": "", "name": minecraft_nick})

        with open(whitelist_path, "w", encoding="utf-8") as f:
            json.dump(whitelist, f, indent=2, ensure_ascii=False)

        return True, f"`{minecraft_nick}` 등록 완료!"

    except Exception as e:
        return False, f"오류: {e}"


class ApprovalView(discord.ui.View):
    """봇 재시작 후에도 버튼이 유지되는 persistent view."""

    def __init__(self):
        super().__init__(timeout=None)

    def _get_nicks(self, message: discord.Message) -> tuple[str, str]:
        if not message.embeds:
            return "알 수 없음", "알 수 없음"
        fields = message.embeds[0].fields
        forest = next((f.value for f in fields if "숲" in f.name), "알 수 없음")
        mc = next((f.value for f in fields if "마크" in f.name), "알 수 없음")
        return forest, mc

    @discord.ui.button(label="✅ 승인", style=discord.ButtonStyle.success, custom_id="btn_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        forest_nick, minecraft_nick = self._get_nicks(interaction.message)
        success, msg = add_to_whitelist(minecraft_nick)

        embed = discord.Embed(
            title="✅ 화이트리스트 등록 완료" if success else "⚠️ 등록 실패",
            color=discord.Color.green() if success else discord.Color.yellow(),
        )
        embed.add_field(name="숲 닉네임", value=forest_nick, inline=True)
        embed.add_field(name="마크 닉네임", value=minecraft_nick, inline=True)
        embed.add_field(name="처리자", value=interaction.user.mention, inline=False)
        embed.set_footer(text=msg)

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ 거절", style=discord.ButtonStyle.danger, custom_id="btn_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        forest_nick, minecraft_nick = self._get_nicks(interaction.message)

        embed = discord.Embed(title="❌ 신청 거절됨", color=discord.Color.red())
        embed.add_field(name="숲 닉네임", value=forest_nick, inline=True)
        embed.add_field(name="마크 닉네임", value=minecraft_nick, inline=True)
        embed.add_field(name="처리자", value=interaction.user.mention, inline=False)

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


@bot.event
async def on_ready():
    # persistent view 등록 — 봇 재시작 후에도 기존 버튼 응답 가능
    bot.add_view(ApprovalView())
    print(f"[봇] {bot.user} 로그인 완료 — whitelist 경로: {MINECRAFT_SERVER_PATH}")


if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
