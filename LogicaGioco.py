from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any

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
        # Appena riceve notifica, salva lo stato
        if isinstance(subject, Player):
            memento = subject.save_state()
            self.history.append(memento)

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

def valida_nome(player: Player, player_id: int) -> str:
    nome = input(f"Inserisci il nome per il Personaggio {player_id}: ")
    if nome.strip() == "":
        if player_id == 1: nome = "Player1"
        else: nome = "Player2"
        print(f"Nome assegnato di default: {nome}")
    player.nome = nome
    return player.nome

def assegna_moralita(player: Player):
    # Nota: L'input deve essere esatto per funzionare
    scelta = input("Che individuo sei davvero? Un eroe altruista, un mercenario egoista o un'anima indifferente? ")
    if choice := scelta: # Assegnazione semplice per attivare il setter
        if scelta == "eroe altruista": player.moralita += 8
        elif scelta == "mercenario egoista": player.moralita += 3 
        elif scelta == "anima indifferente": player.moralita += 5

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

class GameFacade:
    def __init__(self):
        self.manager = GameManager.get_instance()
        # Qui istanziamo l'Observer che gestirà i salvataggi
        self.auto_saver = AutoSaveObserver()

    def crea_personaggio_completo(self, creator: CharacterCreator, player_id: int):
        player = creator.create_character("", 0) 
        
        # COLLEGAMENTO FONDAMENTALE: Attacco l'observer al player
        player.attach(self.auto_saver)

        valida_nome(player, player_id)
        assegna_moralita(player) # Qui scatterà l'AutoSave se la moralità cambia
        
        self.manager.giocatori.append(player)
        return player