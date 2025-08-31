import discord
from discord.ext import commands
from discord import app_commands
from views.bando_start_view import BandoStartView

CANALE_BANDO_ID = 1408596591673348116  # 🔹 Sostituisci con ID del canale "bando-staff"

class BandoStaff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bando_staff", description="Pubblica il bando per entrare nello staff")
    @app_commands.checks.has_permissions(manage_guild=True)  # Solo staff può lanciare
    async def bando_staff(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        canale = interaction.guild.get_channel(CANALE_BANDO_ID)
        if not canale:
            return await interaction.followup.send("❌ Canale bando non trovato.", ephemeral=True)

        # Embed principale
        embed = discord.Embed(
            title="📢 BANDO STAFF APERTO!",
            description=(
                "👥 **Siamo alla ricerca di nuove figure da inserire nello staff di VeneziaRP!** 🏛️\n\n"
                "❓ Vuoi contribuire alla gestione della città virtuale?\n"
                "❓ Ti piace aiutare gli altri e vuoi entrare nel cuore della community?\n"
                "❓ Hai esperienza o desideri imparare?\n\n"
                "📝 **Compila il modulo per candidarti!**\n"
                "Le candidature resteranno aperte fino al:\n"
                "**07 Settembre 2025, ore 23:00**\n\n"
                "⚡ **Requisiti minimi:**\n"
                "- Età minima 14 anni\n"
                "- Presenza attiva su Discord\n"
                "- Serietà e rispetto\n\n"
                "❓ In caso di domande, apri un ticket in <#1408589307337375837> "
                "o scrivi a un membro dello staff.\n\n"
                "💛 Aiuta VeneziaRP a crescere... entra in squadra con noi!"
            ),
            color=discord.Color.gold()
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1396088402532634695/1400582618004717608/273E3D3D-33C2-452A-98C8-065B33F339CC.png")  

        # ✅ Footer con logo server in piccolo
        if interaction.guild and interaction.guild.icon:
            embed.set_footer(
                text="VeneziaRP | Candidature Staff",
                icon_url=interaction.guild.icon.url
            )
        else:
            embed.set_footer(text="VeneziaRP | Candidature Staff")

        # Invia messaggio con View
        view = BandoStartView()
        await canale.send(embed=embed, view=view)

        await interaction.followup.send("✅ Bando staff pubblicato!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(BandoStaff(bot))