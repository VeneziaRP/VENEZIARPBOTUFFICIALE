# cogs/revoca_cittadinanza.py
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import staff_only  # ⬅️ aggiungi
from views.cittadinanza_db import revoke_approved  # usa la funzione che abbiamo aggiunto

CITTADINO_ROLE_ID = 1408613574850379959
LOG_REVOCA_CITTADINANZA_CHANNEL_ID = 1408591528213086228  # <-- METTI QUI il canale logs cittadinanza

class RevocaCittadinanza(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="revoca_cittadinanza", description="Revoca la cittadinanza a un utente.")
    @staff_only()  # ⬅️ solo staff
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(utente="Utente a cui revocare la cittadinanza", motivo="Motivazione (opz.)")
    async def revoca_cittadinanza(
        self,
        interaction: discord.Interaction,
        utente: discord.Member,
        motivo: str | None = None
    ):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Solo in server.", ephemeral=True)

        # 1) DB: togli da approved (e pending se presente)
        changed = revoke_approved(utente.id)

        # 2) Ruolo
        ruolo_cittadino = interaction.guild.get_role(CITTADINO_ROLE_ID)
        removed = False
        if ruolo_cittadino and ruolo_cittadino in utente.roles:
            try:
                await utente.remove_roles(ruolo_cittadino, reason=motivo or "Revoca cittadinanza")
                removed = True
            except discord.Forbidden:
                pass

        # 3) Log canale staff
        ch = interaction.client.get_channel(LOG_REVOCA_CITTADINANZA_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            emb = discord.Embed(
                title="🔻 Revoca Cittadinanza",
                color=discord.Color.red(),
                description="Cittadinanza revocata; l’utente potrà ripresentare domanda in futuro."
            )
            emb.add_field(name="👤 Utente", value=f"{utente.mention}\n`ID: {utente.id}`", inline=False)
            emb.add_field(name="🛡️ Staff", value=interaction.user.mention, inline=True)
            emb.add_field(name="🔧 Azione ruolo", value="Rimosso ✅" if removed else "Non presente / non rimosso", inline=True)
            if motivo:
                emb.add_field(name="📝 Motivazione", value=f"```{motivo[:1000]}```", inline=False)
            if interaction.guild.icon:
                emb.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url)
            try:
                await ch.send(embed=emb)
            except discord.Forbidden:
                pass

        # 4) DM utente (best effort)
        try:
            await utente.send(
                "🏛️ **Cittadinanza revocata.**\n"
                f"Motivo: {motivo or 'non specificato'}\n"
                "Potrai ripresentare la domanda in futuro, se idoneo."
            )
        except discord.Forbidden:
            pass

        # 5) Risposta allo staff
        msg = []
        msg.append("✅ Revoca registrata.")
        msg.append("Ruolo cittadino rimosso." if removed else "Ruolo cittadino non presente o non rimosso.")
        msg.append("DB aggiornato." if changed else "In archivio non risultava approvato/pending.")
        await interaction.response.send_message(" ".join(msg), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RevocaCittadinanza(bot))