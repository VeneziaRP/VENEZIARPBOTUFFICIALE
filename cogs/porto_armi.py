import discord
from discord import app_commands
from discord.ext import commands
from views.porto_armi_view import PortoArmiView
from utils.checks import staff_only  # ⬅️ solo staff

class PortoArmi(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="porto_armi",
        description="Invia il pannello ufficiale per richiedere il porto d’armi."
    )
    @staff_only()
    async def porto_armi(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("❌ Questo comando va usato nel server.", ephemeral=True)

        desc = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏛️ **UFFICIO PORTO D’ARMI — VENEZIARP**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Richiedi il tuo **porto d’armi ufficiale** per poter **portare/detenere** armi **legalmente** nella Repubblica di Venezia.\n"
            "È obbligatorio per chiunque voglia utilizzare armi all’interno del roleplay.\n\n"
            "### ✅ Requisiti\n"
            "• 👤 Essere **cittadino** di VeneziaRP\n"
            "• 🚫 Nessuna **sanzione grave** recente\n"
            "• 🧠 **Motivazione** coerente (sicurezza, lavoro…)\n"
            "• 🤝 Uso **responsabile** e **realistico** delle armi\n\n"
            "### ⚠️ Regole\n"
            "• Uso scorretto ⇒ **ritiro** del porto + **sanzioni**\n"
            "• Ogni richiesta è valutata dallo staff (**24–48 ore**)\n\n"
            "📌 Tipi: **P1** Sportivo • **P2** Caccia • **P3** Difesa • **P4** Lavoro\n"
            "➡️ Clicca **Richiedi Porto d’Armi** per iniziare."
        )

        emb = discord.Embed(
            title="Porto d’Armi — VeneziaRP",
            description=desc,
            color=discord.Color.orange()
        )
        if guild.icon:
            emb.set_thumbnail(url=guild.icon.url)
            emb.set_footer(
                text="VeneziaRP | Ufficio Porto d’Armi",
                icon_url=guild.icon.url  # ✅ logo piccolo nel footer
            )
        else:
            emb.set_footer(text="VeneziaRP | Ufficio Porto d’Armi")

        await interaction.response.send_message(embed=emb, view=PortoArmiView(self.bot))

async def setup(bot: commands.Bot):
    await bot.add_cog(PortoArmi(bot))
    # View persistente per i custom_id dei bottoni
    from views.porto_armi_view import PortoArmiView as _PAV
    bot.add_view(_PAV(bot))