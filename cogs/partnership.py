import discord
from discord.ext import commands
from discord import app_commands

# Invito nuovo del server
INVITE_LINK = "https://discord.gg/mYH3aPyw"

class Partnership(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="partnership", description="Invia l'embed di partnership ufficiale.")
    async def partnership(self, interaction: discord.Interaction):
        guild = interaction.guild
        logo_url = guild.icon.url if guild and guild.icon else None

        emb = discord.Embed(
            title="✨ VeneziaRP – Roleplay d’Eccellenza (Roblox ER:LC)",
            description="📍 Ambientato nella storica città lagunare, **VeneziaRP** è un progetto esclusivo su *ER:LC* che unisce autenticità, professionalità e un’esperienza immersiva mai vista prima.",
            color=discord.Color.blue()
        )

        emb.add_field(
            name="🧭 Chi siamo",
            value=(
                "🔹 Server organizzato con regole chiare e staff competente\n"
                "🔹 Community attiva, accogliente e verificata\n"
                "🔹 Eventi settimanali, incarichi RP e un mondo dinamico\n"
                "🔹 Progetto in costante crescita con obiettivi chiari"
            ),
            inline=False
        )

        emb.add_field(
            name="🧩 Sistema missioni & quest",
            value=(
                "💸 Guadagna soldi in economy, bonus ed equipaggiamenti\n"
                "👮‍♂️ Avanza di grado nei dipartimenti\n"
                "🧨 Ottieni bonus esclusivi per la tua mafia\n"
                "💎 Sblocca contenuti e ruoli unici\n"
                "❓ …e molto altro da scoprire!"
            ),
            inline=False
        )

        emb.add_field(
            name="🛡️ Fazioni disponibili",
            value=(
                "🚓 Polizia di Stato\n"
                "👮‍♂️ Polizia Locale\n"
                "🚔 Polizia Penitenziaria\n"
                "💂‍♂️ Carabinieri\n"
                "💰 Guardia di Finanza\n"
                "🚒 Vigili del Fuoco\n"
                "🚑 Croce Rossa Italiana\n"
                "🛠️ Soccorso Stradale"
            ),
            inline=False
        )

        emb.add_field(
            name="🏢 Sistema aziende & civili",
            value=(
                "🏭 Crea e gestisci attività imprenditoriali realistiche\n"
                "📦 Settori attivi: logistica, food, trasporti, intrattenimento\n"
                "🎓 Carriere interne con avanzamenti concreti\n"
                "⚙️ Economia semi-realistico bilanciata"
            ),
            inline=False
        )

        emb.add_field(
            name="🤝 Perché collaborare con noi",
            value=(
                "✅ Partnership serie, bilanciate e monitorate\n"
                "📢 Promozione reciproca durante eventi e campagne\n"
                "📌 Canali esclusivi per i partner\n"
                "⏱️ Risposte rapide con gestori dedicati"
            ),
            inline=False
        )

        emb.add_field(
            name="🎯 Conclusione",
            value="Collaborare con VeneziaRP significa entrare in un circuito **selezionato, professionale e in crescita**.\nVenezia punta alla **qualità**, non alla quantità.",
            inline=False
        )

        # Logo server
        if logo_url:
            emb.set_thumbnail(url=logo_url)
            emb.set_footer(text="VeneziaRP | Partnership Ufficiale", icon_url=logo_url)
        else:
            emb.set_footer(text="VeneziaRP | Partnership Ufficiale")

        emb.timestamp = discord.utils.utcnow()

        # Bottone invito
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="🔗 Unisciti a VeneziaRP",
            url=INVITE_LINK,
            style=discord.ButtonStyle.link
        ))

        await interaction.channel.send(content="@everyone", embed=emb, view=view)
        await interaction.response.send_message("✅ Embed di partnership inviato.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Partnership(bot))