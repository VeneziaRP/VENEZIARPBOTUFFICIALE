import discord
from discord.ext import commands
from discord import app_commands
import json
import io
import traceback

INVITE_LINK = "https://discord.gg/mYH3aPyw"

class ShareEmbed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="share_partnership",
        description="Genera il codice JSON dell'embed partnership per Discohook."
    )
    async def share_partnership(self, interaction: discord.Interaction):
        # 1) rispondi SUBITO così l'interazione non scade
        await interaction.response.defer(ephemeral=True)

        try:
            # 2) costruisci l'embed (uguale al tuo /partnership)
            emb = discord.Embed(
                title="✨ VeneziaRP – Roleplay d’Eccellenza (Roblox ER:LC)",
                description=(
                    "📍 Ambientato nella storica città lagunare, **VeneziaRP** è un progetto esclusivo su *ER:LC* "
                    "che unisce autenticità, professionalità e un’esperienza immersiva mai vista prima.\n\n"
                    "🧭 **Chi siamo**\n"
                    "🔹 Server organizzato con regole chiare e staff competente\n"
                    "🔹 Community attiva, accogliente e verificata\n"
                    "🔹 Eventi settimanali, incarichi RP e un mondo dinamico\n"
                    "🔹 Progetto in costante crescita con obiettivi chiari\n\n"
                    "🧩 **Missioni & quest**\n"
                    "💸 Guadagni, bonus ed equipaggiamenti\n"
                    "👮‍♂️ Avanzamenti nei dipartimenti\n"
                    "🧨 Bonus per mafie\n"
                    "💎 Contenuti e ruoli esclusivi\n\n"
                    "🛡️ **Fazioni**: Polizia, Carabinieri, Finanza, VV.F, CRI, Soccorso Stradale…\n\n"
                    "🏢 **Aziende & Civili**: attività realistiche ed economia bilanciata.\n\n"
                    "🤝 **Perché collaborare**\n"
                    "✅ Partnership serie e monitorate • 📢 Promozione reciproca • 📌 Canali partner dedicati\n\n"
                    f"🔗 **Invito**: {INVITE_LINK}"
                ),
                color=discord.Color.gold()
            )
            # logo server nel footer se disponibile
            if interaction.guild and interaction.guild.icon:
                emb.set_footer(text="VeneziaRP • Partnership Ufficiale", icon_url=interaction.guild.icon.url)
                emb.set_thumbnail(url=interaction.guild.icon.url)
            else:
                emb.set_footer(text="VeneziaRP • Partnership Ufficiale")

            # 3) JSON per Discohook
            payload = {"content": "", "embeds": [emb.to_dict()]}
            buf = io.BytesIO(json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"))
            file = discord.File(buf, filename="partnership_embed.json")

            # 4) invia con followup
            await interaction.followup.send(
                content="📂 Ecco il **JSON** da importare su https://discohook.org/ → *Import*.",
                file=file,
                ephemeral=True
            )

        except Exception as e:
            # se qualcosa va storto, mostra l'errore invece di far scadere l'interazione
            traceback.print_exc()
            await interaction.followup.send(
                f"❌ Errore durante la generazione: `{e}`",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(ShareEmbed(bot))