import discord
from discord import app_commands
from discord.ext import commands

from views.cittadinanza_view import CittadinanzaView
from utils.checks import staff_only  # opzionale

# === CONFIG ===
TURISTA_ROLE_ID = 1408613574150197258  # Ruolo "Turista"

class Cittadinanza(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="cittadinanza",
        description="Invia il pannello ufficiale per richiedere la cittadinanza."
    )
    @staff_only()
    async def cittadinanza(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("❌ Questo comando va usato nel server.", ephemeral=True)

        turista = guild.get_role(TURISTA_ROLE_ID)
        ping_content = turista.mention if isinstance(turista, discord.Role) else None

        desc = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏛️ **UFFICIO CITTADINANZA — VENEZIARP**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 Diventa un **cittadino ufficiale** della nostra Repubblica e partecipa pienamente alla vita civile e legale del server.\n\n"
            "### ✅ Vantaggi per i cittadini registrati\n"
            "• 👮 Accesso a **lavori dedicati** (polizia, sanitari, meccanici…)\n"
            "• 📝 **Richieste ufficiali** (porto d’armi, licenze, acquisti speciali)\n"
            "• 🗳️ **Votazioni** e decisioni della community\n"
            "• 🏠 Acquisto di **immobili** e 🚗 **veicoli**\n"
            "• 🧩 **Eventi esclusivi** e contenuti dedicati\n\n"
            "### 🧾 Requisiti per la cittadinanza\n"
            "• 🆔 **Nome e cognome validi** in gioco\n"
            "• 📜 Rispetto del **regolamento di VeneziaRP**\n"
            "• 🚫 Nessuna **sanzione grave** recente\n\n"
            "⏳ Le domande vengono valutate dallo staff entro **24–48 ore**.\n"
            "📌 Clicca su **Richiedi Cittadinanza** per iniziare."
        )

        emb = discord.Embed(
            title="Cittadinanza — VeneziaRP",
            description=desc,
            color=discord.Color.gold()
        )
        if guild.icon:
            emb.set_thumbnail(url=guild.icon.url)
            emb.set_footer(
                text="VeneziaRP | Ufficio Cittadinanza",
                icon_url=guild.icon.url
            )
        else:
            emb.set_footer(text="VeneziaRP | Ufficio Cittadinanza")

        view = CittadinanzaView(self.bot)

        allowed = discord.AllowedMentions.none()
        if ping_content:
            allowed = discord.AllowedMentions(roles=True, users=False, everyone=False)

        await interaction.response.send_message(
            content=ping_content or None,
            embed=emb,
            view=view,
            allowed_mentions=allowed
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Cittadinanza(bot))
    bot.add_view(CittadinanzaView(bot))