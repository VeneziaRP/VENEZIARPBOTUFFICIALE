# cogs/pulisci.py
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class Pulisci(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="pulisci",
        description="Cancella messaggi nel canale (bulk < 14 giorni, altrimenti singolarmente)."
    )
    @app_commands.describe(
        quantita="Quanti messaggi controllare (1–1000, default 1000)",
        solo_bot="Se true, elimina solo i messaggi dei bot",
        utente="(Opz.) Elimina solo i messaggi di questo utente"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def pulisci(
        self,
        interaction: discord.Interaction,
        quantita: Optional[int] = 1000,
        solo_bot: Optional[bool] = False,
        utente: Optional[discord.Member] = None,
    ):
        channel = interaction.channel
        me = interaction.guild.me if interaction.guild else None

        # Permessi del bot
        if not me:
            return await interaction.response.send_message(
                "❌ Non riesco a verificare i miei permessi in questo server.", ephemeral=True
            )

        perms = channel.permissions_for(me)
        if not (perms.manage_messages and perms.read_message_history):
            return await interaction.response.send_message(
                "❌ Mi servono i permessi **Gestisci messaggi** e **Leggere la cronologia** in questo canale.",
                ephemeral=True
            )

        # Sanifica input
        if not quantita or quantita < 1:
            quantita = 100
        quantita = min(quantita, 1000)

        await interaction.response.defer(ephemeral=True, thinking=True)

        def _filtro(msg: discord.Message) -> bool:
            if msg.pinned:
                return False
            if solo_bot and not msg.author.bot:
                return False
            if utente and msg.author.id != utente.id:
                return False
            return True

        try:
            # Prova cancellazione bulk (solo messaggi più recenti di 14 giorni)
            bulk_deleted = await channel.purge(limit=quantita, check=_filtro, bulk=True)
            count_bulk = len(bulk_deleted)

            # Se nulla in bulk, prova cancellazione singola (messaggi più vecchi di 14 giorni)
            if count_bulk == 0:
                single_count = 0
                async for msg in channel.history(limit=quantita):
                    if not _filtro(msg):
                        continue
                    try:
                        await msg.delete()
                        single_count += 1
                    except discord.HTTPException:
                        pass

                if single_count:
                    return await interaction.followup.send(
                        f"🧹 Eliminati **{single_count}** messaggi "
                        f"(singolarmente, > 14 giorni){' di ' + utente.mention if utente else ''}.",
                        ephemeral=True
                    )
                else:
                    return await interaction.followup.send(
                        "ℹ️ Nessun messaggio corrisponde ai filtri (o sono pinnati).",
                        ephemeral=True
                    )

            # Esito bulk
            await interaction.followup.send(
                f"✅ Ho cancellato **{count_bulk}** messaggi in {channel.mention}"
                f"{' (solo bot)' if solo_bot else ''}"
                f"{' di ' + utente.mention if utente else ''}.",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send("❌ Permessi insufficienti in questo canale.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"⚠️ Errore durante la pulizia: `{e}`", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Pulisci(bot))