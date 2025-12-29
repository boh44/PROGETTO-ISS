from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
# ==========================================
# 1. PATTERN OBSERVER & MEMENTO (NUOVI)
# ==========================================

class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        pass

class Subject(ABC):
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)

class CharacterMemento:
    """Il pacchetto dati (Memento)."""
    def __init__(self, state: Dict[str, Any]):
        self._state = state

    def get_state(self) -> Dict[str, Any]:
        return self._state

class AutoSaveObserver(Observer):
    """ConcreteObserver + Caretaker: Salva in memoria (history)."""
    def __init__(self):
        self.history: List[CharacterMemento] = []

    def update(self, subject: Subject) -> None:
        if isinstance(subject, Player):
            memento = subject.save_state()
            self.history.append(memento)
            # Ogni volta che aggiorna la memoria, salviamo anche su file per sicurezza
            self.salva_su_file()

    def salva_su_file(self):
        """Trasforma la history in JSON e la scrive su disco."""
        try:
            # Prendiamo solo l'ultimo stato di ogni giocatore per non appesantire il file
            dati_da_salvare = [memento.get_state() for memento in self.history]
            with open("salvataggio_gioco.json", "w") as f:
                json.dump(dati_da_salvare, f, indent=4)
            print("Log: Salvataggio su file completato.")
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")

# ==========================================
# 2. CLASSI PLAYER (MODIFICATE)
# ==========================================

class Player(Subject, ABC):
    """
    Player ora è un Subject (notifica) e un Originator (crea Memento).
    """
    def __init__(self, nome: str, moralita: int):
        super().__init__()
        self.nome = nome
        self._moralita = moralita 

    # PROPERTY per intercettare i cambiamenti di moralità
    @property
    def moralita(self):
        return self._moralita

    @moralita.setter
    def moralita(self, valore: int):
        if valore != self._moralita:
            self._moralita = valore
            self.notify() # Notifica l'Observer -> Salvataggio automatico

    # Metodi Memento (Originator)
    def save_state(self) -> CharacterMemento:
        return CharacterMemento({"nome": self.nome, "moralita": self._moralita})

    def restore_state(self, memento: CharacterMemento) -> None:
        state = memento.get_state()
        self.nome = state["nome"]
        self._moralita = state["moralita"]

class Player1(Player): 
    def __repr__(self): return f"Player1(nome={self.nome}, moralita={self.moralita})"

class Player2(Player): 
    def __repr__(self): return f"Player2(nome={self.nome}, moralita={self.moralita})"

# ==========================================
# 3. FACTORY METHOD (INVARIATO)
# ==========================================

class CharacterCreator(ABC):
    @abstractmethod
    def factory_method(self, nome: str, moralita: int) -> Player: pass

    def create_character(self, nome: str, moralita: int) -> Player:
        return self.factory_method(nome, moralita)

class Player1Creator(CharacterCreator):
    def factory_method(self, nome: str, moralita: int) -> Player1: return Player1(nome, moralita)

class Player2Creator(CharacterCreator):
    def factory_method(self, nome: str, moralita: int) -> Player2: return Player2(nome, moralita)

# ==========================================
# 4. FUNZIONI LOGICA GIOCO (RIPRISTINATE)
# ==========================================

def valida_nome(nome: str, player_id: int) -> str:
    nome = nome.strip()
    if nome == "":
        return "Player1" if player_id == 1 else "Player2"
    return nome


def assegna_moralita(player: Player, scelta_manuale: str = None):
    # Se non viene passata una scelta, usiamo un valore neutro di default
    # Se viene passata (dalla grafica), usiamo quella
    scelta = scelta_manuale if scelta_manuale else "anima indifferente"
    
    if scelta == "eroe altruista": 
        player.moralita += 8
    elif scelta == "mercenario egoista": 
        player.moralita += 3
    elif scelta == "anima indifferente": 
        player.moralita += 5
"""def assegna_moralita(player: Player):
    if scelta_moralita is None:
        scelta_moralita = input(
            f"{player.nome}, che individuo sei davvero? "
            "Un eroe altruista, un mercenario egoista o un'anima indifferente? ")

    # Assegna valori corretti
    if scelta_moralita == "eroe altruista": 
        player.moralita += 8
    elif scelta_moralita == "mercenario egoista": 
        player.moralita += 3
    elif scelta_moralita == "anima indifferente": 
        player.moralita += 5"""

# ==========================================
# 5. GAMEMANAGER & FACADE (INTEGRATI)
# ==========================================

class GameManager:
    """
    Singleton. Gestisce lo stato globale (livello, vite, lista giocatori).
    (Codice originale ripristinato esattamente)
    """
    _instance = None

    def __init__(self):
        if GameManager._instance is not None:
            raise Exception("Singleton violation: Usa GameManager.get_instance()")
        else:
            GameManager._instance = self
            # Attributi specifici richiesti dallo schema
            self.livello_corrente = 1
            self.vite_rimanenti = 5
            self.giocatori = []
            print("Log: Dati di gioco resettati.")

    @staticmethod
    def get_instance():
        if GameManager._instance is None:
            GameManager()
        return GameManager._instance

    def resetGameData(self):
        """Metodo per ripristinare i valori iniziali."""
        self.livello_corrente = 1
        self.vite_rimanenti = 5
        self.giocatori = []
        print("Log: Dati di gioco resettati.")

#UNISCE GRAFICA E LOGICA
class GameFacade:
    def __init__(self, manager, auto_saver=None):
        self.manager = manager
        self.auto_saver = auto_saver # Ora la Facade "sa" cos'è l'auto_saver

    def crea_personaggio_completo(self, creator: CharacterCreator, player_corrente: int, nome_inserito: str = "", scelta_fatta: str = None):
        # 1. Validazione del nome
        nome_valido = valida_nome(nome_inserito, player_corrente)
        # 2. Creazione del player (passiamo 0 come valore temporaneo per la moralità)
        player = creator.create_character(nome_valido, 0)
        # 3. CORREZIONE: Collega l'auto_saver solo se esiste
        if self.auto_saver is not None:
            player.attach(self.auto_saver)
        # 4. Assegnazione della moralità reale scelta dall'utente
        assegna_moralita(player, scelta_fatta)
        # 5. Aggiunta al manager dei giocatori
        self.manager.giocatori.append(player)
        return player
    
    def carica_ultimo_salvataggio(self):
        """Ripristina lo stato dei giocatori dall'ultimo Memento disponibile."""
        if not self.auto_saver or not self.auto_saver.history:
            print("Log: Nessun salvataggio trovato.")
            return False

        # Esempio: ripristiniamo l'ultimo stato salvato per ogni giocatore
      
        for player in self.manager.giocatori:
            # Cerchiamo nella cronologia l'ultimo memento che appartiene a questo player
            for memento in reversed(self.auto_saver.history):
                if memento.get_state()["nome"] == player.nome:
                    player.restore_state(memento)
                    print(f"Log: Ripristinato stato per {player.nome}")
                    break
        return True
    
    def carica_da_disco(self):
        try:
            with open("salvataggio_gioco.json", "r") as f:
                dati = json.load(f)
                if self.auto_saver:
                    self.auto_saver.history = [CharacterMemento(d) for d in dati]
                    
                    # --- AGGIUNTA: Se i giocatori non ci sono, creali dai dati salvati ---
                    if len(self.manager.giocatori) == 0:
                        for d in dati:
                            # Creiamo un Player1 o Player2 in base al numero di caricati
                            nuovo_p = Player1(d["nome"], d["moralita"]) if len(self.manager.giocatori) == 0 else Player2(d["nome"], d["moralita"])
                            nuovo_p.attach(self.auto_saver)
                            self.manager.giocatori.append(nuovo_p)
                    return True
        except FileNotFoundError:
            return False
        
    def esiste_salvataggio(self) -> bool:
        """Controlla se esiste fisicamente il file di salvataggio."""
        import os
        return os.path.exists("salvataggio_gioco.json")
    
