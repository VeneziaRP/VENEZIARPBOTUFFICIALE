from __future__ import annotations
import io
import time
import discord
from discord import ui
from utils import annuncio_storage as store

STAFF_ROLE_ID = 1408613549168918528 # cambia con il tuo ID staff

def _is_staff(user: discord.abc.User) -> bool:
    return isinstance(user, discord.Member) and any(r.id == STAFF_ROLE_ID for r in user.roles)

class EventoView(ui.View):
    def __init__(self, message_id: int, state: dict | None = None):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.state = state or {
            "tipo": "evento",
            "titolo": None,
            "iscritti": [],
            "max_posti": 0,
            "deadline_ts": None,
            "chiuso": False,
            "channel_id": None,
            "thread_created": False
        }
        self._sync_labels()

    # ---- helpers ----
    def _save(self):
        store.save(self.message_id, self.state)

    def _posti_restanti(self) -> str:
        m = int(self.state.get("max_posti", 0) or 0)
        cur = len(self.state["iscritti"])
        return f"{cur}/{m}" if m > 0 else f"{cur}"

    def _sync_labels(self):
        iscr = len(self.state["iscritti"])
        self.b_iscrivi.label = f"📅 Iscriviti ({iscr})"
        maxp = int(self.state.get("max_posti", 0) or 0)
        pieni = maxp > 0 and iscr >= maxp
        self.b_iscrivi.disabled = self.state.get("chiuso", False) or pieni

    async def _maybe_autoclose(self, interaction: discord.Interaction):
        dl = self.state.get("deadline_ts")
        if dl and time.time() >= float(dl):
            await self._chiudi(interaction, "⏰ Iscrizioni chiuse automaticamente (scadenza).")
            return True
        maxp = int(self.state.get("max_posti", 0) or 0)
        if maxp > 0 and len(self.state["iscritti"]) >= maxp and not self.state.get("chiuso", False):
            await self._chiudi(interaction, "✅ Posti esauriti: iscrizioni chiuse automaticamente.")
            return True
        return False

    async def _chiudi(self, interaction: discord.Interaction, reason: str | None = None):
        self.state["chiuso"] = True
        self._save()
        for c in self.children:
            if c.custom_id not in {"evt:riapri","evt:export"}:
                c.disabled = True
        await interaction.response.edit_message(view=self)
        if reason:
            await interaction.followup.send(reason, ephemeral=True)

    # ---- bottoni ----
    @ui.button(label="📅 Iscriviti (0)", style=discord.ButtonStyle.success, custom_id="evt:iscrivi")
    async def b_iscrivi(self, interaction: discord.Interaction, button: ui.Button):
        if self.state.get("chiuso", False):
            return await interaction.response.send_message("Le iscrizioni sono chiuse.", ephemeral=True)

        if await self._maybe_autoclose(interaction):
            return

        uid = str(interaction.user.id)
        if uid in self.state["iscritti"]:
            return await interaction.response.send_message("Sei già iscritto!", ephemeral=True)

        self.state["iscritti"].append(uid)
        self._save()
        self._sync_labels()

        # prima risposta: aggiorna messaggio
        await interaction.response.edit_message(view=self)

        # messaggi successivi: followup
        try:
            await interaction.user.send("✅ Sei iscritto all'evento! Ti aspettiamo 🎉")
        except Exception:
            pass

        await interaction.followup.send("✅ Iscrizione registrata!", ephemeral=True)

    @ui.button(label="📜 Lista iscritti", style=discord.ButtonStyle.secondary, custom_id="evt:lista")
    async def b_lista(self, interaction: discord.Interaction, button: ui.Button):
        iscritti = self.state["iscritti"]
        if not iscritti:
            return await interaction.response.send_message("Nessun iscritto al momento.", ephemeral=True)
        chunks = [iscritti[i:i+25] for i in range(0, len(iscritti), 25)]
        pages = []
        for idx, ch in enumerate(chunks, 1):
            txt = "\n".join(f"{i+1}. <@{u}>" for i, u in enumerate(ch, start=(idx-1)*25))
            pages.append(txt)
        content = "\n\n".join(pages)
        await interaction.response.send_message(f"📜 **Iscritti ({self._posti_restanti()}):**\n{content}", ephemeral=True)

    @ui.button(label="🔒 Chiudi iscrizioni", style=discord.ButtonStyle.danger, custom_id="evt:chiudi")
    async def b_chiudi(self, interaction: discord.Interaction, button: ui.Button):
        if not _is_staff(interaction.user):
            return await interaction.response.send_message("Solo lo staff può chiudere.", ephemeral=True)
        await self._chiudi(interaction, "🔒 Iscrizioni chiuse.")

    @ui.button(label="🔓 Riapri", style=discord.ButtonStyle.secondary, custom_id="evt:riapri")
    async def b_riapri(self, interaction: discord.Interaction, button: ui.Button):
        if not _is_staff(interaction.user):
            return await interaction.response.send_message("Solo lo staff può riaprire.", ephemeral=True)
        self.state["chiuso"] = False
        self._save()
        self._sync_labels()
        await interaction.response.edit_message(view=self)
        await interaction.response.send_message("🔓 Iscrizioni riaperte.", ephemeral=True)

    @ui.button(label="⬇️ Export CSV", style=discord.ButtonStyle.primary, custom_id="evt:export")
    async def b_export(self, interaction: discord.Interaction, button: ui.Button):
        if not _is_staff(interaction.user):
            return await interaction.response.send_message("Solo lo staff può esportare.", ephemeral=True)
        buf = io.StringIO()
        buf.write("position,user_id,mention\n")
        for i, uid in enumerate(self.state["iscritti"], start=1):
            buf.write(f"{i},{uid},<@{uid}>\n")
        data = io.BytesIO(buf.getvalue().encode("utf-8"))
        filename = f"iscritti_{self.message_id}.csv"
        await interaction.response.send_message(file=discord.File(data, filename), ephemeral=True)