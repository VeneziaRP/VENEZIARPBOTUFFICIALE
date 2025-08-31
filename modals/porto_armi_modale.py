# modals/porto_armi_modale.py
import discord
from typing import Optional

# usa le tue funzioni DB/stato e la view staff
from views.porto_armi_review_view import (
    PortoArmiReviewView,
    mark_pending, is_pending, is_already_approved
)

# ⬇️ metti l'ID del canale staff "logs-porto-darmi"
STAFF_PORTO_ARMI_CHANNEL_ID = 1408591152323625100  # <-- CAMBIA

class PortoArmiModal(discord.ui.Modal, title="Richiesta Porto d’Armi"):
    """
    Viene aperta dalla view (dove scegli P1/P2/P3/P4).
    Passa 'tipo' = 'P1' | 'P2' | 'P3' | 'P4'
    """
    def __init__(self, bot: discord.Client, autore: discord.Member, tipo: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.autore = autore
        self.tipo = tipo  # P1, P2, P3, P4

        # --- Campi richiesta (come nello screen) ---
        self.motivazione = discord.ui.TextInput(
            label="Motivazione",
            placeholder="Perché richiedi questo porto d’armi?",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        )
        self.lavoro = discord.ui.TextInput(
            label="Lavoro RP",
            placeholder="Es. Guardia giurata, Cacciatore, Meccanico…",
            style=discord.TextStyle.short,
            max_length=60,
            required=False
        )
        self.arma = discord.ui.TextInput(
            label="Arma principale",
            placeholder="Es. Pistola / Fucile / Pompa…",
            style=discord.TextStyle.short,
            max_length=40,
            required=True
        )
        self.esperienza = discord.ui.TextInput(
            label="Esperienza",
            placeholder="Breve descrizione (es. tiro sportivo, addestramento, ecc.)",
            style=discord.TextStyle.paragraph,
            max_length=300,
            required=False
        )
        self.scuola = discord.ui.TextInput(
            label="A scuola",
            placeholder="Hai seguito un corso/lezione? Sì/No + dettagli",
            style=discord.TextStyle.short,
            max_length=80,
            required=False
        )

        for it in (self.motivazione, self.lavoro, self.arma, self.esperienza, self.scuola):
            self.add_item(it)

    async def on_submit(self, interaction: discord.Interaction):
        uid = self.autore.id

        if is_already_approved(uid):
            return await interaction.response.send_message("✅ Hai già un porto d’armi approvato.", ephemeral=True)
        if is_pending(uid):
            return await interaction.response.send_message("⏳ Hai già una richiesta in revisione.", ephemeral=True)

        # Pacchetto dati salvato nel DB "pending"
        dati = {
            "tipo": self.tipo,                               # P1 | P2 | P3 | P4
            "motivazione": (self.motivazione.value or "").strip(),
            "lavoro_rp": (self.lavoro.value or "").strip(),
            "arma_principale": (self.arma.value or "").strip(),
            "esperienza": (self.esperienza.value or "").strip(),
            "a_scuola": (self.scuola.value or "").strip(),
        }
        mark_pending(uid, dati)

        # Embed per lo staff (come nel tuo layout)
        e = discord.Embed(title="🔫 Nuova Richiesta Porto d’Armi", color=discord.Color.dark_gold())
        e.add_field(name="👤 Utente", value=f"{self.autore.mention}\n`{uid}`", inline=False)
        e.add_field(name="🏷️ Tipologia", value=f"**{dati['tipo']}**", inline=True)
        e.add_field(name="\u200b", value="\u200b", inline=True)

        e.add_field(name="📝 Motivazione", value=dati["motivazione"] or "—", inline=False)
        e.add_field(name="💼 Lavoro", value=dati["lavoro_rp"] or "—", inline=True)
        e.add_field(name="🔧 Arma principale", value=dati["arma_principale"] or "—", inline=True)
        e.add_field(name="🎯 Esperienza", value=dati["esperienza"] or "—", inline=False)
        e.add_field(name="🏫 A scuola", value=dati["a_scuola"] or "—", inline=True)

        if self.autore.display_avatar:
            e.set_thumbnail(url=self.autore.display_avatar.url)

        # Footer con icona server se disponibile
        if interaction.guild and interaction.guild.icon:
            e.set_footer(text="VeneziaRP | Porto d’Armi", icon_url=interaction.guild.icon.url)
        else:
            e.set_footer(text="VeneziaRP | Porto d’Armi")

        # Invio nel canale staff con i bottoni Approva/Rifiuta
        ch = interaction.client.get_channel(STAFF_PORTO_ARMI_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            return await interaction.response.send_message("❌ Canale staff non configurato.", ephemeral=True)

        view = PortoArmiReviewView(interaction.client, applicant_id=uid, tipo=self.tipo)
        await ch.send(embed=e, view=view)

        await interaction.response.send_message(
            "✅ **Richiesta inviata!** Lo staff la valuterà entro 24–48 ore.",
            ephemeral=True
        )