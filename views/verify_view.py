from __future__ import annotations
import discord
from discord.ext import commands

# ====== CONFIG ======
VERIFICA_CHANNEL_ID = 1408584793506971995  # canale #verifica
UNVERIFIED_ROLE_ID  = 1408613575907475590  # ruolo iniziale (es. "Non verificato")
VERIFIED_ROLE_ID    = 1408613574150197258  # ruolo che sblocca il server
LOG_CHANNEL_ID      = 1408599999285039184  # canale log staff

# frase richiesta
VERIFY_PHRASE = "VeneziaRP"

class VerificaModal(discord.ui.Modal, title="Verifica — conferma regolamento"):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.user = user

        self.answer = discord.ui.TextInput(
            label="Scrivi la frase di conferma",
            placeholder=VERIFY_PHRASE,
            style=discord.TextStyle.short,
            max_length=100,
            required=True,
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        attempt = self.answer.value.strip()

        if attempt.lower() == VERIFY_PHRASE.lower():
            await _grant_verified(interaction, self.user)
        else:
            await interaction.response.send_message(
                f"❌ Devi scrivere esattamente:\n`{VERIFY_PHRASE}`",
                ephemeral=True
            )

async def _grant_verified(inter: discord.Interaction, member: discord.Member):
    guild = member.guild
    unverified = guild.get_role(UNVERIFIED_ROLE_ID)
    verified   = guild.get_role(VERIFIED_ROLE_ID)
    log_ch     = guild.get_channel(LOG_CHANNEL_ID)

    try:
        if unverified and unverified in member.roles:
            await member.remove_roles(unverified, reason="Verificato")
        if verified and verified not in member.roles:
            await member.add_roles(verified, reason="Verificato")
    except Exception:
        pass

    if isinstance(log_ch, discord.TextChannel):
        await log_ch.send(f"✅ **{member.mention}** verificato con successo (frase).")

    await inter.response.send_message("✅ Verifica completata! Benvenuto in VeneziaRP 🎉", ephemeral=True)

class VerifyView(discord.ui.View):
    """Bottone persistente da mettere in #verifica."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verificati", style=discord.ButtonStyle.success, custom_id="verify:start")
    async def start(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.channel_id != VERIFICA_CHANNEL_ID:
            return await interaction.response.send_message("Usa il bottone nel canale di verifica.", ephemeral=True)

        if isinstance(interaction.user, discord.Member):
            if UNVERIFIED_ROLE_ID not in [r.id for r in interaction.user.roles]:
                return await interaction.response.send_message("Risulti già verificato ✅", ephemeral=True)

        await interaction.response.send_modal(VerificaModal(interaction.user))

# helper per registrare la view persistente
def register_views(bot: commands.Bot | discord.Client):
    bot.add_view(VerifyView())