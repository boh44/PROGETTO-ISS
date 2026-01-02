from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import os

# ==========================================
# 1. OBSERVER + SUBJECT
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
# 2. MEMENTO
# ==========================================

class CharacterMemento:
    """Contiene lo stato serializzabile del personaggio"""
    def __init__(self, state: Dict[str, Any]):
        self._state = state

    def get_state(self) -> Dict[str, Any]:
        return self._state


class AutoSaveObserver(Observer):
    """Observer + Caretaker: salva automaticamente lo stato"""
    def __init__(self):
        self.history: List[CharacterMemento] = []

    def update(self, subject: Subject) -> None:
        if isinstance(subject, Player):
            self.history.append(subject.save_state())
            self._salva_su_file()

    def _salva_su_file(self):
        try:
            dati = [m.get_state() for m in self.history]
            with open("salvataggio_gioco.json", "w") as f:
                json.dump(dati, f, indent=4)
        except Exception as e:
            print(f"Errore salvataggio: {e}")

# ==========================================
# 3. PLAYER
# ==========================================

class Player(Subject, ABC):
    def __init__(self, nome: str, moralita: int):
        super().__init__()
        self.nome = nome
        self._moralita = moralita
        self._max_hp = 100
        self._hp = 100

    # ---------- MORALITÀ ----------
    @property
    def moralita(self) -> int:
        return self._moralita

    @moralita.setter
    def moralita(self, valore: int):
        if valore != self._moralita:
            self._moralita = valore
            self.notify()

    # ---------- VITA ----------
    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, valore: int):
        self._hp = max(0, min(valore, self._max_hp))
        self.notify()

    @property
    def max_hp(self) -> int:
        return self._max_hp

    # ---------- METODI DANNI/CURA ----------
    def take_damage(self, amount: int):
        self.hp -= amount  # chiama il setter

    def heal(self, amount: int):
        self.hp += amount  # chiama il setter

    # ---------- MEMENTO ----------
    def save_state(self) -> CharacterMemento:
        return CharacterMemento({
            "type": self.__class__.__name__,
            "nome": self.nome,
            "moralita": self._moralita,
            "hp": self._hp,
            "max_hp": self._max_hp
        })

    def restore_state(self, memento: CharacterMemento) -> None:
        state = memento.get_state()
        self.nome = state["nome"]
        self._moralita = state["moralita"]
        self._hp = state.get("hp", 100)
        self._max_hp = state.get("max_hp", 100)
        self.notify()


class Player1(Player):
    def __repr__(self):
        return f"Player1({self.nome}, HP={self.hp})"


class Player2(Player):
    def __repr__(self):
        return f"Player2({self.nome}, HP={self.hp})"

# ==========================================
# 4. FACTORY METHOD
# ==========================================

class CharacterCreator(ABC):
    @abstractmethod
    def factory_method(self, nome: str, moralita: int) -> Player:
        pass

    def create_character(self, nome: str, moralita: int) -> Player:
        return self.factory_method(nome, moralita)


class Player1Creator(CharacterCreator):
    def factory_method(self, nome: str, moralita: int) -> Player1:
        return Player1(nome, moralita)


class Player2Creator(CharacterCreator):
    def factory_method(self, nome: str, moralita: int) -> Player2:
        return Player2(nome, moralita)

# ==========================================
# 5. FUNZIONI DI SUPPORTO
# ==========================================

def valida_nome(nome: str, player_id: int) -> str:
    nome = nome.strip()
    if nome == "":
        return "Player1" if player_id == 1 else "Player2"
    return nome


def assegna_moralita(player: Player, scelta: str = None):
    scelta = scelta or "anima indifferente"
    if scelta == "eroe altruista":
        player.moralita += 8
    elif scelta == "mercenario egoista":
        player.moralita += 3
    else:
        player.moralita += 5

# ==========================================
# 6. GAMEMANAGER (SINGLETON)
# ==========================================

class GameManager:
    _instance = None

    def __init__(self):
        if GameManager._instance is not None:
            raise Exception("Singleton violation")
        GameManager._instance = self
        self.resetGameData()

    @staticmethod
    def get_instance():
        if GameManager._instance is None:
            GameManager()
        return GameManager._instance

    def resetGameData(self):
        self.livello_corrente = 1
        self.vite_rimanenti = 5
        self.giocatori: List[Player] = []
        print("Log: Dati resettati.")

# ==========================================
# 7. FACADE
# ==========================================

class GameFacade:
    def __init__(self, manager: GameManager, auto_saver: AutoSaveObserver | None = None):
        self.manager = manager
        self.auto_saver = auto_saver

    def crea_personaggio_completo(
        self,
        creator: CharacterCreator,
        player_id: int,
        nome_inserito: str = "",
        scelta_fatta: str = None
    ) -> Player:

        nome = valida_nome(nome_inserito, player_id)
        player = creator.create_character(nome, 0)

        if self.auto_saver:
            player.attach(self.auto_saver)

        assegna_moralita(player, scelta_fatta)
        self.manager.giocatori.append(player)
        return player

    def carica_da_disco(self) -> bool:
        if not os.path.exists("salvataggio_gioco.json"):
            return False

        with open("salvataggio_gioco.json", "r") as f:
            dati = json.load(f)

        if self.auto_saver:
            self.auto_saver.history = [CharacterMemento(d) for d in dati]

        self.manager.giocatori.clear()

        for d in dati:
            tipo = d.get("type", "Player1")
            if tipo == "Player2":
                p = Player2(d["nome"], d["moralita"])
            else:
                p = Player1(d["nome"], d["moralita"])

            p.restore_state(CharacterMemento(d))
            if self.auto_saver:
                p.attach(self.auto_saver)

            self.manager.giocatori.append(p)

        return True

    def carica_ultimo_salvataggio(self) -> bool:
        if not self.auto_saver or not self.auto_saver.history:
            return False

        for player in self.manager.giocatori:
            for memento in reversed(self.auto_saver.history):
                if memento.get_state()["nome"] == player.nome:
                    player.restore_state(memento)
                    break
        return True

    def esiste_salvataggio(self) -> bool:
        return os.path.exists("salvataggio_gioco.json")

