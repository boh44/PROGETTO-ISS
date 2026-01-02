from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import os
from collections.abc import Iterable, Iterator

# ==========================================
# 1. INTERFACCE OBSERVER
# ==========================================

class Observer(ABC):
    @abstractmethod
    def update(self, subject: "Subject") -> None:
        pass

class Subject(ABC):
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)


# ==========================================
# 3. MEMENTO
# ==========================================

class CharacterMemento:
    def __init__(self, state: Dict[str, Any]):
        self._state = state

    def get_state(self) -> Dict[str, Any]:
        return self._state

class AutoSaveObserver(Observer):
    def update(self, subject: Subject) -> None:
        if isinstance(subject, Player):
            self._salva_giocatori_attivi()

    def _salva_giocatori_attivi(self):
        manager = GameManager.get_instance()
        if not manager.giocatori: return
        try:
            # Crea la lista di stati da salvare
            stati = [p.save_state().get_state() for p in manager.giocatori]
            # Scrittura fisica sul file
            with open("salvataggio_gioco.json", "w") as f:
                json.dump(stati, f, indent=4)
            print("Log: Salvataggio completato correttamente.") # Aggiungi questo per debug
        except Exception as e:
            print(f"Errore critico durante il salvataggio: {e}")

# ==========================================
# 4. PLAYER 
# ==========================================

class Player(Subject, ABC):
    def __init__(self, nome: str, moralita: int):
        super().__init__()
        self.nome = nome
        self._moralita = moralita
        self._max_hp = 100
        self._hp = 100

    @property
    def moralita(self) -> int: return self._moralita

    @moralita.setter
    def moralita(self, valore: int):
        if valore != self._moralita:
            self._moralita = valore
            self.notify()

    @property
    def hp(self) -> int: return self._hp

    @hp.setter
    def hp(self, valore: int):
        self._hp = max(0, min(valore, self._max_hp))
        self.notify()

    @property
    def max_hp(self) -> int: return self._max_hp

    def take_damage(self, amount: int): self.hp -= amount
    def heal(self, amount: int): self.hp += amount

    # ---------- MEMENTO AGGIORNATO ----------
    def save_state(self) -> CharacterMemento:
        # Salviamo i nomi degli oggetti come lista di stringhe
        nomi_item = [item.nome for item in self._inventario]
        return CharacterMemento({
            "type": self.__class__.__name__,
            "nome": self.nome,
            "moralita": self._moralita,
            "hp": self._hp,
            "max_hp": self._max_hp,
        })

    def restore_state(self, memento: CharacterMemento) -> None:
        state = memento.get_state()
        self.nome = state["nome"]
        self._moralita = state["moralita"]
        self._hp = state.get("hp", 100)
        self._max_hp = state.get("max_hp", 100)

class Player1(Player):
    def __repr__(self): return f"Player1({self.nome}, HP={self.hp})"

class Player2(Player):
    def __repr__(self): return f"Player2({self.nome}, HP={self.hp})"

# ==========================================
# 5. FACTORY METHOD
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
# 6. MOSTRI
# ==========================================

class Mostro(ABC):
    def __init__( self, nome: str, hp: int, danno: int, furtivita: int, intelligenza: int):
        self.nome = nome
        self.hp = hp
        self.danno = danno
        self.furtivita = furtivita
        self.intelligenza = intelligenza

    def is_alive(self) -> bool: return self.hp > 0
    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    @abstractmethod
    def attacca(self, player) -> None: pass

class Goblin(Mostro):
    def __init__(self): super().__init__("Goblin", 100, 10, 8, 4)
    def attacca(self, player) -> None: player.take_damage(self.danno)

# ==========================================
# 7. GAMEMANAGER (SINGLETON)
# ==========================================

class GameManager:
    _instance = None
    def __init__(self):
        if GameManager._instance is not None: raise Exception("Singleton violation")
        GameManager._instance = self
        self.resetGameData()

    @staticmethod
    def get_instance():
        if GameManager._instance is None: GameManager()
        return GameManager._instance

    def resetGameData(self):
        self.livello_corrente = 1
        self.vite_rimanenti = 5
        self.giocatori: List[Player] = []
        print("Log: Dati di gioco resettati.")

# ==========================================
# 8. FACADE
# ==========================================

class GameFacade:
    def __init__(self, manager: GameManager, auto_saver: AutoSaveObserver | None = None):
        self.manager = manager
        self.auto_saver = auto_saver

    def crea_personaggio_completo(self, creator: CharacterCreator, player_id: int, nome_inserito: str = "", scelta_fatta: str = None) -> Player:
        nome = valida_nome(nome_inserito, player_id)
        player = creator.create_character(nome, 0)
        self.manager.giocatori.append(player)
        if self.auto_saver: player.attach(self.auto_saver)
        assegna_moralita(player, scelta_fatta)
        return player

    def carica_da_disco(self) -> bool:
        if not os.path.exists("salvataggio_gioco.json"): return False
        try:
            with open("salvataggio_gioco.json", "r") as f:
                dati = json.load(f)
            self.manager.giocatori.clear()
            for d in dati:
                p = Player2(d["nome"], d["moralita"]) if d.get("type") == "Player2" else Player1(d["nome"], d["moralita"])
                p.restore_state(CharacterMemento(d))
                self.manager.giocatori.append(p)
                if self.auto_saver: p.attach(self.auto_saver)
                print(f"Log: Ripristinato {p.nome} (Moralità: {p.moralita}, HP: {p.hp}), Item: {p._inventario}")
            return True
        except Exception as e:
            print(f"Errore: {e}")
            return False

    def esiste_salvataggio(self) -> bool:
        return os.path.exists("salvataggio_gioco.json")

# ==========================================
# 9. FUNZIONI SUPPORTO
# ==========================================

def valida_nome(nome: str, player_id: int) -> str:
    nome = nome.strip()
    return nome if nome != "" else (f"Player{player_id}")

def assegna_moralita(player: Player, scelta: str = None):
    scelta = scelta or "anima indifferente"
    bonus = {"eroe altruista": 8, "mercenario egoista": 3, "anima indifferente": 5}
    player.moralita += bonus.get(scelta, 5)