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
# 2. INVENTORY + ITERATOR (Spostato in alto per Player)
# ==========================================

class Item:
    def __init__(self, nome: str, tipo: str, valore: int):
        self.nome = nome
        self.tipo = tipo  # "Cura", "Attacco", "Utility"
        self.valore = valore

    def __repr__(self):
        return f"{self.nome}"

class InventoryIterator(Iterator):
    def __init__(self, items: List[Item]):
        self._items = items
        self._index = 0

    def __next__(self) -> Item:
        try:
            item = self._items[self._index]
            self._index += 1
            return item
        except IndexError:
            raise StopIteration()

class Inventory(Iterable):
    def __init__(self):
        self._items: List[Item] = []

    def add_item(self, item: Item):
        self._items.append(item)

    def __iter__(self) -> InventoryIterator:
        return InventoryIterator(self._items)
    
    def __len__(self):
        return len(self._items)

    def __repr__(self):
        if not self._items: return "Vuoto"
        return ", ".join([item.nome for item in self._items])

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
# 4. PLAYER (Sincronizzato con Inventario)
# ==========================================

class Player(Subject, ABC):
    def __init__(self, nome: str, moralita: int):
        super().__init__()
        self.nome = nome
        self._moralita = moralita
        self._max_hp = 100
        self._hp = 100
        self._inventario = Inventory()

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
            "inventario": nomi_item  # Salva gli item!
        })

    def restore_state(self, memento: CharacterMemento) -> None:
        state = memento.get_state()
        self.nome = state["nome"]
        self._moralita = state["moralita"]
        self._hp = state.get("hp", 100)
        self._max_hp = state.get("max_hp", 100)
        
        # Ripristino oggetti
        self._inventario = Inventory()
        nomi_item = state.get("inventario", [])
        for nome in nomi_item:
            # Ricreiamo gli oggetti Item (valori predefiniti)
            self._inventario.add_item(Item(nome, "Utility", 0))

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

# ==============================================================================
# MOSTRI
# ==============================================================================

class Mostro(ABC):
    def __init__( self, nome: str, hp: int, danno: int, furtivita: int, intelligenza: int):
        self.nome = nome
        self.hp = hp
        self.danno = danno
        self.furtivita = furtivita
        self.intelligenza = intelligenza

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp < 0: self.hp = 0

    @abstractmethod
    def attacca(self, player) -> None:
        pass
# ---------- CONCRETE PRODUCTS ----------

class Goblin(Mostro):
    def __init__(self):
        super().__init__( nome="Goblin", hp=40, danno=10, furtivita=8, intelligenza=4)

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class Anubi(Mostro):
    def __init__(self):
        super().__init__(nome="Anubi", hp=80, danno=15, furtivita=1, intelligenza=2)

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class Chica(Mostro):
    def __init__(self):
        super().__init__(nome="Chica",hp=100, danno=20, furtivita=8, intelligenza=4)

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class Yeti(Mostro):
    def __init__(self):
        super().__init__(nome="Yeti delle Nevi", hp=140, danno=30, furtivita=7, intelligenza=5)

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class SerpenteTreTeste(Mostro):
    def __init__(self):
        super().__init__(nome="Serpente a Tre Teste", hp=200, danno=70, furtivita=10, intelligenza=10)

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

# ---------- CREATOR ----------
class MostroCreator(ABC):
    @abstractmethod
    def factory_method(self) -> Mostro:
        pass

    def crea_mostro(self) -> Mostro:
        return self.factory_method()

# ---------- CONCRETE CREATORS ----------
class GoblinCreator(MostroCreator):
    def factory_method(self) -> Mostro:
        return Goblin()

class AnubiCreator(MostroCreator):
    def factory_method(self) -> Mostro:
        return Anubi()

class ChicaCreator(MostroCreator):
    def factory_method(self) -> Mostro:
        return Chica()

class YetiCreator(MostroCreator):
    def factory_method(self) -> Mostro:
        return Yeti()

class SerpenteTreTesteCreator(MostroCreator):
    def factory_method(self) -> Mostro:
        return SerpenteTreTeste()

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