# modals/annuncio_evento_modal.py
from __future__ import annotations
import datetime
import discord
from utils import annuncio_storage as store
from views.tipi.evento_view import EventoView

class AnnuncioEventoModal(discord.ui.Modal, title="Crea Evento / Iscrizioni"):
    def __init__(self):
        super().__init__(timeout=None)

        self.titolo = discord.ui.TextInput(label="Titolo", max_length=128)
        self.descrizione = discord.ui.TextInput(label="Descrizione", style=discord.TextStyle.paragraph, max_length=2000)
        self.max_posti = discord.ui.TextInput(label="Limite posti (0=illimitati)", required=False, default="0")
        self.deadline = discord.ui.TextInput(label="Scadenza (opz.)", required=False, placeholder="YYYY-MM-DD HH:MM")

        self.add_item(self.titolo)
        self.add_item(self.descrizione)
        self.add_item(self.max_posti)
        self.add_item(self.deadline)

    async def on_submit(self, interaction: discord.Interaction):
        # parse limite
        try:
            max_posti = int((self.max_posti.value or "0").strip())
        except ValueError:
            max_posti = 0

        # parse scadenza
        deadline_ts = None
        if self.deadline.value and self.deadline.value.strip():
            try:
                dt = datetime.datetime.strptime(self.deadline.value.strip(), "%Y-%m-%d %H:%M")
                deadline_ts = int(dt.timestamp())
            except Exception:
                deadline_ts = None

        embed = discord.Embed(
            title=f"🎉 {self.titolo.value}",
            description=self.descrizione.value,
            color=discord.Color.gold()
        )
        if max_posti > 0:
            embed.add_field(name="🪑 Posti", value=str(max_posti), inline=True)
        if deadline_ts:
            embed.add_field(name="⏰ Scadenza", value=f"<t:{deadline_ts}:F> • <t:{deadline_ts}:R>", inline=True)
        embed.set_footer(text="VeneziaRP | Annunci")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        state = {
            "tipo": "evento",
            "titolo": self.titolo.value,
            "iscritti": [],
            "max_posti": max_posti,
            "deadline_ts": deadline_ts,
            "chiuso": False,
            "channel_id": msg.channel.id
        }

        from views.tipi.evento_view import EventoView
        view = EventoView(msg.id, state)
        await msg.edit(view=view)
        store.save(msg.id, state)