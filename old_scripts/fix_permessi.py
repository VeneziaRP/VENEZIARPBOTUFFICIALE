import discord
from discord import app_commands
from discord.ext import commands

# Permessi minimi utili al bot (non tocca altri ruoli, solo quello del bot)
BOT_OVERWRITE = discord.PermissionOverwrite(
    view_channel=True,
    read_message_history=True,
    send_messages=True,
    send_messages_in_threads=True,
    embed_links=True,
    attach_files=True,
    add_reactions=True,
    use_application_commands=True,
    connect=True,
    speak=True
)

class FixPermessi(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="fix_permessi_bot",
        description="Dà al bot i permessi minimi in tutte le categorie e canali"
    )
    async def fix_permessi_bot(self, itx: discord.Interaction):
        guild = itx.guild
        bot_member: discord.Member = guild.me
        bot_role = bot_member.top_role
        if not bot_role:
            return await itx.response.send_message("❌ Non trovo il ruolo del bot.", ephemeral=True)

        await itx.response.defer(ephemeral=True, thinking=True)

        ok, fail = 0, 0
        details = []

        for ch in guild.channels:  # include categorie, testo, vocali, ecc.
            try:
                await ch.set_permissions(bot_role, overwrite=BOT_OVERWRITE, reason="Fix permessi bot (setup)")
                ok += 1
            except Exception as e:
                fail += 1
                # salva un breve motivo per debug
                details.append(f"{ch.name}: {type(e).__name__}")

        report = f"✅ Sistemati {ok} canali/categorie"
        if fail:
            report += f" | ⚠️ Non riusciti: {fail}\n" + "  " + ", ".join(details[:10])

        await itx.followup.send(report, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(FixPermessi(bot))