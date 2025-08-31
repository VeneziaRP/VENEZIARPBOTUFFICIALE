# main.py — BOT con restore votazione + annunci
# Sync in on_ready con copy_global_to(guild) + sync(guild) (no global sync)

import os
import json
import time
import asyncio
import logging
import discord
from discord.ext import commands

# === CONFIG ===
DEV_GUILD_ID = 1408579338777002077  # server principale di test/uso
DATA_VOTAZIONE_FILE = "data/votazione_data.json"

# === LOGGING ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# === INTENTS ===
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.presences = True

# === BOT ===
bot = commands.Bot(command_prefix="!", intents=intents)

# === CARTELLE DATA ===
os.makedirs("data", exist_ok=True)
os.makedirs("data/annunci", exist_ok=True)


# ---------- Ripristino Votazione SSU ----------
async def _restore_votazione_if_any() -> bool:
    """Ripristina la VotazioneView SSU dal file JSON, se esiste."""
    try:
        from views.votazione_view import VotazioneView

        if not os.path.exists(DATA_VOTAZIONE_FILE):
            logging.info("ℹ️ Nessun file votazione da ripristinare.")
            return False

        with open(DATA_VOTAZIONE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        canale_id = data.get("canale_id")
        messaggio_id = data.get("messaggio_id")
        autore_id = data.get("autore_id")
        votanti_ids = data.get("votanti", [])

        if not (canale_id and messaggio_id and autore_id):
            logging.warning("⚠️ File votazione incompleto: niente restore.")
            return False

        try:
            channel = await bot.fetch_channel(int(canale_id))
        except Exception:
            logging.warning("⚠️ Canale votazione non trovato o permessi mancanti.")
            return False

        try:
            message = await channel.fetch_message(int(messaggio_id))
        except discord.NotFound:
            logging.warning("⚠️ Messaggio votazione non trovato.")
            return False

        autore = bot.get_user(int(autore_id)) or await bot.fetch_user(int(autore_id))
        view = VotazioneView(autore=autore, bot=bot)

        if hasattr(view, "aggancia_messaggio"):
            await view.aggancia_messaggio(message)

        if hasattr(view, "votanti"):
            view.votanti = set(int(x) for x in votanti_ids)

        try:
            for child in view.children:
                cid = getattr(child, "custom_id", None)
                if cid == "utenti":
                    child.label = f"👥 Utenti: {len(view.votanti)}"
                elif cid == "ssu":
                    child.disabled = len(view.votanti) < 5
        except Exception:
            pass

        await message.edit(view=view)
        bot.add_view(view)

        logging.info(f"✅ Votazione SSU ripristinata. Votanti: {len(getattr(view, 'votanti', []))}")
        return True

    except Exception as e:
        logging.exception(f"❌ Errore ripristino votazione: {e}")
        return False


# ---------- Ripristino Annunci ----------
async def _restore_annunci_if_any() -> int:
    """Ripristina le view degli Annunci persistenti da utils/annuncio_storage."""
    restored = 0
    try:
        from utils import annuncio_storage as store
    except Exception:
        logging.info("ℹ️ Sistema Annunci non installato (utils/annuncio_storage.py mancante).")
        return 0

    try:
        from views.tipi.votazione_view import VotazioneView as AnnVotazioneView
    except Exception:
        AnnVotazioneView = None
        logging.warning("⚠️ Manca views/tipi/votazione_view.py")
    try:
        from views.tipi.conferma_view import ConfermaView as AnnConfermaView
    except Exception:
        AnnConfermaView = None
        logging.warning("⚠️ Manca views/tipi/conferma_view.py")
    try:
        from views.tipi.sondaggio_view import SondaggioView as AnnSondaggioView
    except Exception:
        AnnSondaggioView = None
        logging.warning("⚠️ Manca views/tipi/sondaggio_view.py")
    try:
        from views.tipi.evento_view import EventoView as AnnEventoView
    except Exception:
        AnnEventoView = None
        logging.warning("⚠️ Manca views/tipi/evento_view.py")

    try:
        states = store.all_states()
    except Exception as e:
        logging.exception(f"❌ Errore lettura stati Annunci: {e}")
        return 0

    if not states:
        logging.info("ℹ️ Nessun annuncio persistente da ripristinare.")
        return 0

    for state in states:
        mid = state.get("message_id")
        tipo = state.get("tipo")
        if not mid or not tipo:
            continue

        try:
            view = None
            if tipo == "votazione" and AnnVotazioneView:
                view = AnnVotazioneView(mid, state)
            elif tipo == "conferma" and AnnConfermaView:
                view = AnnConfermaView(mid, state)
            elif tipo == "sondaggio" and AnnSondaggioView:
                view = AnnSondaggioView(mid, state.get("opzioni", []), state)
            elif tipo == "evento" and AnnEventoView:
                view = AnnEventoView(mid, state)

            if view:
                bot.add_view(view, message_id=mid)
                restored += 1
        except Exception as e:
            logging.exception(f"❌ Errore ripristino annuncio {mid} ({tipo}): {e}")

    logging.info(f"✅ Annunci ripristinati: {restored}")
    return restored


# ---------- Setup ----------
@bot.event
async def setup_hook():
    # Carica COGS
    if os.path.isdir("./cogs"):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                modname = filename[:-3]
                try:
                    await bot.load_extension(f"cogs.{modname}")
                    logging.info(f"✅ Cog caricato: {modname}")
                except Exception as e:
                    logging.exception(f"❌ Errore cog {modname}: {e}")

    # Carica EVENTS
    if os.path.isdir("./events"):
        for filename in os.listdir("./events"):
            if filename.endswith(".py") and filename != "__init__.py":
                modname = filename[:-3]
                try:
                    await bot.load_extension(f"events.{modname}")
                    logging.info(f"✅ Event caricato: {modname}")
                except Exception as e:
                    logging.exception(f"❌ Errore event {modname}: {e}")

    # Restore SSU / Annunci
    try:
        from views.votazione_view import VotazioneView
    except Exception:
        VotazioneView = None
        logging.warning("⚠️ views/votazione_view.py non trovato.")
    restored_ssu = await _restore_votazione_if_any()
    if not restored_ssu and VotazioneView:
        try:
            bot.add_view(VotazioneView())
            logging.info("ℹ️ Registrata VotazioneView SSU globale (nessun restore attivo).")
        except Exception:
            pass
    await _restore_annunci_if_any()

    # (Facoltativo) altre view persistenti se presenti
    for dotted, kwargs in [
        ("views.ferie_view.FerieReviewView", {"bot": bot, "applicant_id": None, "approver_roles": set()}),
        ("views.bando_start_view.BandoStartView", {}),
        ("views.bando_review_view.BandoReviewView", {}),
        ("views.colloqui_view.ColloquiView", {}),
    ]:
        try:
            module_path, cls_name = dotted.rsplit(".", 1)
            mod = __import__(module_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            view = cls(**kwargs) if kwargs else cls()
            bot.add_view(view)
            logging.info(f"ℹ️ View registrata: {cls_name}")
        except Exception:
            pass


# ---------- Ready ----------
@bot.event
async def on_ready():
    guilds_str = ", ".join(f"{g.name} ({g.id})" for g in bot.guilds)
    logging.info(f"✅ {bot.user} è online | Guilds: {guilds_str} | latency {bot.latency:.3f}s")

    # Evita risync continui su reconnessioni
    if getattr(bot, "synced_once", False):
        return

    try:
        total = 0
        # 👇 Copia i comandi "global definiti nel codice" nella tree della singola guild
        # e poi sincronizza SOLO quella guild (no sync globale)
        for g in bot.guilds:
            bot.tree.copy_global_to(guild=g)
            synced = await bot.tree.sync(guild=g)
            logging.info(f"🔁 Slash sync in {g.name} ({g.id}): {len(synced)} comandi")
            total += len(synced)
        logging.info(f"✅ Sync completata su {len(bot.guilds)} guild (tot {total} comandi)")
        bot.synced_once = True
    except Exception as e:
        logging.exception(f"❌ Errore sync slash: {e}")


# ---------- Runner con riavvio automatico ----------
async def _runner():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("❌ Manca DISCORD_TOKEN nei Secrets/Deployment.")
    await bot.start(token, reconnect=True)


if __name__ == "__main__":
    delay = 5
    while True:
        try:
            asyncio.run(_runner())
        except SystemExit:
            raise
        except Exception:
            logging.exception(f"⚠️ Crash. Riavvio tra {delay}s…")
            time.sleep(delay)
            delay = min(delay * 2, 60)  # backoff max 60s