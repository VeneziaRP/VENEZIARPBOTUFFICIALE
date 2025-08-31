import discord
from discord.ext import commands
from discord import app_commands

class RequisitiPartnership(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="requisiti_partnership", description="Mostra i requisiti per diventare partner di VeneziaRP.")
    async def requisiti_partnership(self, interaction: discord.Interaction):
        guild = interaction.guild
        logo_url = guild.icon.url if guild and guild.icon else None

        emb = discord.Embed(
            title="🤝 Requisiti per la Partnership",
            description="Vuoi diventare nostro partner? Ecco cosa serve:",
            color=discord.Color.green()
        )

        emb.add_field(
            name="📌 Requisiti generali",
            value=(
                "✅ Minimo **50 membri reali**\n"
                "✅ Server attivo con utenti coinvolti\n"
                "✅ Staff presente e canali ben organizzati\n"
                "✅ Canale partnership visibile\n"
                "🚫 Nessun contenuto **NSFW / illegale / tossico**\n"
                "📢 Pubblicare **prima** il nostro annuncio nel vostro server"
            ),
            inline=False
        )

        emb.add_field(
            name="📊 Ping consentiti in base ai membri",
            value=(
                "👥 **0 – 99 membri** → ❌ Nessun ping\n"
                "👥 **100 – 199 membri** → ✅ @partner\n"
                "👥 **200 – 399 membri** → ✅ @here\n"
                "👥 **400+ membri** → ✅ @everyone"
            ),
            inline=False
        )

        emb.add_field(
            name="⚠️ Nota importante",
            value=(
                "🔄 Le partnership devono essere **reciproche, corrette e trasparenti**.\n"
                "📌 Il tuo server deve permettere lo stesso tipo di ping (o superiore) che richiedi a noi.\n"
                "❌ Le partnership sbilanciate verranno rifiutate automaticamente."
            ),
            inline=False
        )

        if logo_url:
            emb.set_thumbnail(url=logo_url)
            emb.set_footer(text="VeneziaRP | Partnership Requisiti", icon_url=logo_url)
        else:
            emb.set_footer(text="VeneziaRP | Partnership Requisiti")

        emb.timestamp = discord.utils.utcnow()

        await interaction.channel.send(embed=emb)
        await interaction.response.send_message("✅ Embed requisiti partnership inviato.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RequisitiPartnership(bot))