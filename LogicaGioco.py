from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import os
from collections.abc import Iterable, Iterator

# ==========================================
# INTERFACCE OBSERVER
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
# INVENTORY + ITERATOR
# ==========================================

class Item:
    def __init__(self, nome: str, tipo: str, valore: int, oggetto=None):
        self.nome = nome
        self.tipo = tipo  # "Cura", "Attacco", "Armatura"
        self.valore = valore
        self.oggetto = oggetto  # riferimento all'oggetto reale (arma, pozione, armatura)

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

class Inventory(Iterable, Subject):
    def __init__(self):
        super().__init__()
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
# MEMENTO
# ==========================================

class CharacterMemento:
    def __init__(self, state: Dict[str, Any]):
        self._state = state

    def get_state(self) -> Dict[str, Any]:
        return self._state

class AutoSaveObserver(Observer):
    def update(self, subject):
        manager = GameManager.get_instance()
        
        # Creiamo una struttura dati completa
        dati_da_salvare = {
            "livello_corrente": manager.livello_corrente,
            "vite_rimanenti": manager.vite_rimanenti,  # Questi sono i "Cuori" comuni
            "giocatori": []
        }
        
        # Estraiamo lo stato dettagliato di ogni giocatore (HP + Inventario)
        for p in manager.giocatori:
            # Il metodo save_state() del player deve includere hp e inventario
            memento_data = p.save_state().get_state()
            dati_da_salvare["giocatori"].append(memento_data)
            
        # Scrittura fisica su file
        try:
            with open("salvataggio_gioco.json", "w") as f:
                json.dump(dati_da_salvare, f, indent=4)
            print(f"Log: Salvataggio completato (Livello: {manager.livello_corrente}, Vite: {manager.vite_rimanenti})")
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")

    def _salva_giocatori_attivi(self):
        manager = GameManager.get_instance()
        if not manager.giocatori: return
        try:
            stati = [p.save_state().get_state() for p in manager.giocatori]
            with open("salvataggio_gioco.json", "w") as f:
                json.dump(stati, f, indent=4)
            print("Log: Salvataggio completato correttamente.")
        except Exception as e:
            print(f"Errore critico durante il salvataggio: {e}")

# ==========================================
# PLAYER
# ==========================================

class Player(Subject, ABC):
    def __init__(self, nome: str, moralita: int):
        super().__init__()
        self.nome = nome
        self._moralita = moralita
        self._max_hp = 100
        self._hp = 100
        self._inventario = Inventory()
        self._armatura: Armatura | None = None  #riferimento all'armatura equipaggiata

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

    def take_damage(self, amount: int):
        # 1. Sottrai il danno
        self.hp -= amount
        print(f"Log: {self.nome} ha subito {amount} danni. HP: {self.hp}")

        # 2. Controllo se gli HP sono finiti
        if self.hp <= 0:
            manager = GameManager.get_instance()
            
            if manager.vite_rimanenti > 0:
                # TOGLIE UN CUORE
                manager.vite_rimanenti -= 1 
                
                # RESETTA LA BARRA VERDE A 100 (o al massimo)
                self.hp = self._max_hp 
                print(f"Log: Vita persa! Vite rimaste: {manager.vite_rimanenti}. HP resettati.")
            else:
                # Se non ci sono più vite, resta a 0 per il Game Over
                self.hp = 0
                print("Log: Nessuna vita rimasta!")

        # 3. NOTIFICA LA GUI (Questo fa muovere la barra e i cuori in tempo reale)
        self.notify()

    def heal(self, amount: int):
        self.hp += amount

    def equip_armatura(self, armatura: Armatura):
        self._armatura = armatura

    def add_item(self, item: Item):
        self._inventario.add_item(item)  # aggiungi oggetto
        self.notify()   

    # ---------- MEMENTO  ----------
    def save_state(self) -> CharacterMemento:
        nomi_item = [item.nome for item in self._inventario]
        return CharacterMemento({
            "type": self.__class__.__name__,
            "nome": self.nome,
            "moralita": self._moralita,
            "hp": self._hp,
            "max_hp": self._max_hp,
            "inventario": [item.nome for item in self._inventario],
        })

    def restore_state(self, memento: CharacterMemento) -> None:
        state = memento.get_state()
        self.nome = state["nome"]
        self._moralita = state["moralita"]
        self._hp = state.get("hp", 100)
        self._max_hp = state.get("max_hp", 100)
        self._inventario = Inventory()
        self._armatura = None

        for nome in state.get("inventario", []):
            oggetto_reale = None
            valore = 0
            tipo = "Utility"

            # tenta di creare l'oggetto dalla classe globale con lo stesso nome
            try:
                oggetto_reale = globals()[nome]()  # es: "SpadaBase" → SpadaBase()
            except KeyError:
                oggetto_reale = None  # se non esiste la classe, rimane None

            # dedurre tipo e valore in base alla classe
            if isinstance(oggetto_reale, Arma):
                tipo = "Attacco"
                valore = getattr(oggetto_reale, "danno", 0)
            elif isinstance(oggetto_reale, Pozione):
                tipo = "Cura"
                valore = getattr(oggetto_reale, "cura", 0)
            elif isinstance(oggetto_reale, Armatura):
                tipo = "Armatura"
                self.equip_armatura(oggetto_reale)

            # aggiungi l'oggetto all'inventario
            self._inventario.add_item(Item(nome, tipo, valore, oggetto=oggetto_reale))


class Player1(Player):
    def __repr__(self): return f"Player1({self.nome}, HP={self.hp})"

class Player2(Player):
    def __repr__(self): return f"Player2({self.nome}, HP={self.hp})"

# ==========================================
# FACTORY METHOD PLAYER
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
# MOSTRI
# ==========================================

class Mostro(ABC):
    def __init__( self, nome: str, hp: int, danno: int, furtivita: int, intelligenza: int,x=0,y=0):
        self.nome = nome
        self.hp = hp
        self.danno = danno
        self.furtivita = furtivita
        self.intelligenza = intelligenza
        self.pos = [x, y]

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
    def __init__(self, x=0, y=0):
        super().__init__(nome="Goblin", hp=40, danno=10, furtivita=8, intelligenza=4,x=x,y=y)
        self.pos = [x, y] # Ci serve per sapere dove disegnarlo nella GUI

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class Anubi(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Anubi", hp=80, danno=15, furtivita=1, intelligenza=2,x=x,y=y)
        self.pos = [x, y] 

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class Chica(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Chica",hp=100, danno=20, furtivita=8, intelligenza=4,x=x,y=y)

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class Yeti(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Yeti delle Nevi", hp=140, danno=30, furtivita=7, intelligenza=5,x=x,y=y)

    def attacca(self, player) -> None:
        player.take_damage(self.danno)

class SerpenteTreTeste(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Serpente a Tre Teste", hp=200, danno=70, furtivita=10, intelligenza=10,x=x,y=y)

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
# GAMEMANAGER (SINGLETON)
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
# FACADE
# ==========================================

class GameFacade:
    def __init__(self, manager: GameManager, auto_saver: AutoSaveObserver | None = None):
        self.manager = manager
        self.auto_saver = auto_saver

    def crea_personaggio_completo(self, creator: CharacterCreator, player_id: int,
                                   nome_inserito: str = "", scelta_fatta: str = None,
                                   factory: ItemFactory | None = None) -> Player:
        nome = valida_nome(nome_inserito, player_id)
        player = creator.create_character(nome, 0)
        self.manager.giocatori.append(player)
        if self.auto_saver: player.attach(self.auto_saver)
        assegna_moralita(player, scelta_fatta)

        return player

    def carica_da_disco(self) -> bool:
        if not os.path.exists("salvataggio_gioco.json"): 
            return False
        try:
            with open("salvataggio_gioco.json", "r") as f:
                contenuto = json.load(f)
            
            # 1. GESTIONE DATI GLOBALI (Livello e Cuori/Vite)
            if isinstance(contenuto, dict):
                # Carica il livello
                self.manager.livello_corrente = contenuto.get("livello_corrente", 1)
                # Carica i cuori (vite rimanenti del team)
                self.manager.vite_rimanenti = contenuto.get("vite_rimanenti", 3)
                lista_giocatori = contenuto.get("giocatori", [])
            else:
                # Fallback per vecchi salvataggi senza struttura a dizionario
                lista_giocatori = contenuto 
                self.manager.livello_corrente = 1
                self.manager.vite_rimanenti = 3

            # 2. RIPRISTINO GIOCATORI (HP e Inventario)
            self.manager.giocatori.clear()
            for d in lista_giocatori:
                # Identifica il tipo di player
                if d.get("type") == "Player2":
                    p = Player2(d["nome"], d["moralita"])
                else:
                    p = Player1(d["nome"], d["moralita"])
                
                # restore_state caricherà HP e Inventario se CharacterMemento li gestisce
                p.restore_state(CharacterMemento(d))
                
                # Aggiunge il player al manager e riattacca l'auto_saver
                self.manager.giocatori.append(p)
                if self.auto_saver: 
                    p.attach(self.auto_saver)
            
            print(f"Log: Caricato Livello {self.manager.livello_corrente}, Vite: {self.manager.vite_rimanenti}")
            return True

        except Exception as e:
            print(f"Errore caricamento: {e}")
            return False
        
    def esiste_salvataggio(self) -> bool:
        return os.path.exists("salvataggio_gioco.json")


# ==========================================
# ABSTRACT FACTORY ITEM
# ==========================================

class Arma(ABC):
    @abstractmethod
    def attacca(self, mostro) -> int: pass

class Pozione(ABC):
    @abstractmethod
    def usa(self, player): pass

class Armatura(ABC):
    @abstractmethod
    def difendi(self, danno: int) -> int: pass

# ---------- ARMI CONCRETE ----------
class SpadaBase(Arma):
    def __init__(self): self.danno = 5
    def attacca(self, mostro) -> int:
        mostro.take_damage(self.danno)
        return self.danno

class Mazza(Arma):
    def __init__(self): self.danno = 7
    def attacca(self, mostro) -> int:
        mostro.take_damage(self.danno)
        return self.danno

class Lama(Arma):
    def __init__(self): self.danno = 9
    def attacca(self, mostro) -> int:
        mostro.take_damage(self.danno)
        return self.danno

class HeavySniper(Arma):
    def __init__(self): self.danno = 15
    def attacca(self, mostro) -> int:
        mostro.take_damage(self.danno)
        return self.danno

class Pugnale(Arma):
    def __init__(self): self.danno = 6
    def attacca(self, mostro) -> int:
        mostro.take_damage(self.danno)
        return self.danno

# ---------- POZIONI ----------
class PozioneCura(Pozione):
    def __init__(self): self.cura = 15
    def usa(self, player): player.heal(self.cura); return self.cura

class KitPozioniFinale(Pozione):
    def __init__(self): self.cura = 50
    def usa(self, player): player.heal(self.cura); return self.cura

# ---------- ARMATURE ----------
class ArmaturaBase(Armatura):
    def difendi(self, danno: int) -> int: return int(danno * 0.95)
class ArmaturaElevata(Armatura):
    def difendi(self, danno: int) -> int: return int(danno * 0.95)
class ArmaturaPiuElevata(Armatura):
    def difendi(self, danno: int) -> int: return int(danno * 0.95)

# ---------- ABSTRACT FACTORY ----------
class ItemFactory(ABC):
    @abstractmethod
    def create_arma(self) -> Arma: pass
    @abstractmethod
    def create_pozione(self): pass
    @abstractmethod
    def create_armatura(self): pass

# ---------- FACTORY LIVELLI ----------
class Livello1Item(ItemFactory):
    def create_arma(self) -> Arma: return SpadaBase()
    def create_pozione(self): return None
    def create_armatura(self): return None

class Livello2Item(ItemFactory):
    def create_arma(self) -> Arma: return Mazza()
    def create_pozione(self): return PozioneCura()
    def create_armatura(self): return ArmaturaBase()

class Livello3Item(ItemFactory):
    def create_arma(self) -> Arma: return Lama()
    def create_pozione(self): return PozioneCura()
    def create_armatura(self): return ArmaturaBase()

class Livello4Item(ItemFactory):
    def create_arma(self) -> Arma: return HeavySniper()
    def create_pozione(self): return PozioneCura()
    def create_armatura(self): return ArmaturaPiuElevata()

class Livello5Item(ItemFactory):
    def create_arma(self) -> Arma: return Pugnale()
    def create_pozione(self): return KitPozioniFinale()
    def create_armatura(self): return ArmaturaElevata()


# ==========================================
# FUNZIONI SUPPORTO
# ==========================================

def valida_nome(nome: str, player_id: int) -> str:
    nome = nome.strip()
    return nome if nome != "" else (f"Player{player_id}")

def assegna_moralita(player: Player, scelta: str = None):
    scelta = scelta or "anima indifferente"
    bonus = {"eroe altruista": 8, "mercenario egoista": 3, "anima indifferente": 5}
    player.moralita += bonus.get(scelta, 5)