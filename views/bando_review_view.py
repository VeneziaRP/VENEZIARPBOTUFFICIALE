# views/bando_review_view.py
from __future__ import annotations

import discord
from discord import ui

# =========================
# CONFIG
# =========================
# Canale dove pubblicare gli esiti (APPROVATO/RIFIUTATO)
CANALE_ESITI_ID = 1408599545776050338  # <-- metti il tuo

# Canale dove prenotare l’orale/pratico
CALENDARIO_CHANNEL_ID = 1408596882258919475  # <-- metti il tuo

# Canale di supporto nel caso non ci siano slot/disponibilità
SUPPORTO_CHANNEL_ID = 1408589307337375837   # <-- metti il tuo

# (Opzionale) Ruolo da pingare con l’esito (es. @Staff Colloqui)
PING_ROLE_ID: int | None = None


def _is_staff(member: discord.Member) -> bool:
    """Permessi minimi per usare i bottoni review."""
    perms = member.guild_permissions
    return perms.administrator or perms.manage_guild or perms.manage_messages


class BandoReviewView(discord.ui.View):
    """Bottoni di review sotto la candidatura. Persistente."""
    def __init__(self, candidate_id: int | None = None, *, disabled: bool = False):
        super().__init__(timeout=None)
        self.candidate_id = candidate_id

        if disabled:
            for c in self.children:
                c.disabled = True

    # =======================
    # APPROVA
    # =======================
    @discord.ui.button(
        label="✅ Approva",
        style=discord.ButtonStyle.success,
        custom_id="bando:approve"
    )
    async def approve(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _is_staff(interaction.user):
            return await interaction.response.send_message("⛔ Non hai i permessi per usare questo.", ephemeral=True)

        if not self.candidate_id:
            return await interaction.response.send_message("⚠️ Candidate ID mancante.", ephemeral=True)

        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("⚠️ Guild non trovata.", ephemeral=True)

        esiti_ch   = guild.get_channel(CANALE_ESITI_ID)
        cal_ch     = guild.get_channel(CALENDARIO_CHANNEL_ID)
        support_ch = guild.get_channel(SUPPORTO_CHANNEL_ID)
        candidate  = guild.get_member(self.candidate_id)

        # ping line
        ping_bits = []
        if candidate:
            ping_bits.append(candidate.mention)
        if PING_ROLE_ID:
            role = guild.get_role(PING_ROLE_ID)
            if role:
                ping_bits.append(role.mention)
        ping_line = " ".join(ping_bits) if ping_bits else None

        # embed esito
        embed = discord.Embed(
            title="🟩 Candidatura APPROVATA",
            description=(
                f"{candidate.mention if candidate else f'`{self.candidate_id}`'} è stato **APPROVATO** alla fase successiva.\n\n"
                "### 📅 Passi successivi\n"
                f"• Prenota l’**orale/pratico** in "
                f"{cal_ch.mention if isinstance(cal_ch, discord.TextChannel) else '`canale-calendario`'} "
                "scegliendo uno slot libero.\n"
                f"• Se non trovi posto, scrivi in "
                f"{support_ch.mention if isinstance(support_ch, discord.TextChannel) else '`canale-supporto`'}.\n\n"
                "Benvenuto nel percorso Staff!"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="VeneziaRP • Candidature Staff")
        if candidate and candidate.display_avatar:
            embed.set_thumbnail(url=candidate.display_avatar.url)

        # bottoni link (aprono i canali)
        link_view = discord.ui.View()
        if isinstance(cal_ch, discord.TextChannel):
            link_view.add_item(discord.ui.Button(
                label="Apri calendario",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{guild.id}/{cal_ch.id}"
            ))
        if isinstance(support_ch, discord.TextChannel):
            link_view.add_item(discord.ui.Button(
                label="Apri supporto",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{guild.id}/{support_ch.id}"
            ))

        if isinstance(esiti_ch, discord.TextChannel):
            await esiti_ch.send(content=ping_line, embed=embed, view=link_view)

        # disabilita i bottoni sotto il messaggio staff
        for c in self.children:
            c.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.response.send_message("✅ Esito pubblicato nel canale esiti. (Bottoni disabilitati)", ephemeral=True)

    # =======================
    # RIFIUTA
    # =======================
    @discord.ui.button(
        label="❌ Rifiuta",
        style=discord.ButtonStyle.danger,
        custom_id="bando:reject"
    )
    async def reject(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _is_staff(interaction.user):
            return await interaction.response.send_message("⛔ Non hai i permessi per usare questo.", ephemeral=True)

        if not self.candidate_id:
            return await interaction.response.send_message("⚠️ Candidate ID mancante.", ephemeral=True)

        # Apri modale per motivazione rifiuto, passandogli info per disabilitare poi i bottoni
        modal = RejectReasonModal(
            candidate_id=self.candidate_id,
            origin_message_id=interaction.message.id if interaction.message else None,
            origin_channel_id=interaction.channel_id
        )
        await interaction.response.send_modal(modal)


# =======================
# MODALE RIFIUTO
# =======================
class RejectReasonModal(discord.ui.Modal, title="Motivazione rifiuto"):
    def __init__(self, candidate_id: int, origin_message_id: int | None, origin_channel_id: int | None):
        super().__init__(timeout=None)
        self.candidate_id = candidate_id
        self.origin_message_id = origin_message_id
        self.origin_channel_id = origin_channel_id

        self.reason = ui.TextInput(
            label="Motivazione",
            placeholder="Scrivi la motivazione del rifiuto...",
            style=discord.TextStyle.paragraph,
            max_length=400,
            required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel_esiti = guild.get_channel(CANALE_ESITI_ID) if guild else None
        candidate = guild.get_member(self.candidate_id) if guild else None

        # Pubblica esito nel canale esiti
        if isinstance(channel_esiti, discord.TextChannel):
            embed = discord.Embed(
                title="🟥 Candidatura RIFIUTATA",
                description=(
                    f"L'utente {candidate.mention if candidate else f'`{self.candidate_id}`'} "
                    "è stato **RIFIUTATO**.\n\n"
                    f"📌 Motivazione:\n```{self.reason.value}```"
                ),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="VeneziaRP • Candidature Staff")
            if candidate and candidate.display_avatar:
                embed.set_thumbnail(url=candidate.display_avatar.url)

            await channel_esiti.send(embed=embed)

        # Prova a disabilitare i bottoni sul messaggio staff
        try:
            if self.origin_channel_id and self.origin_message_id:
                ch = guild.get_channel(self.origin_channel_id)
                if isinstance(ch, discord.TextChannel):
                    msg = await ch.fetch_message(self.origin_message_id)
                    await msg.edit(view=BandoReviewView(candidate_id=self.candidate_id, disabled=True))
        except Exception:
            pass

        await interaction.response.send_message("❌ Candidatura rifiutata e pubblicata nel canale esiti.", ephemeral=True)