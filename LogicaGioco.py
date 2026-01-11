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
    
    '''def clear(self):
        self._items.clear()
        self.notify()  # se vuoi notificare la GUI'''

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
    
class MostroMemento:
    def __init__(self, state: Dict[str, Any]):
        self._state = state

    def get_state(self) -> Dict[str, Any]:
        return self._state


class AutoSaveObserver(Observer):
    def update(self, subject):
        manager = GameManager.get_instance()
        
        dati_da_salvare = {
            "livello_corrente": manager.livello_corrente,
            "vite_rimanenti": manager.vite_rimanenti,
            "giocatori": [],
            "mostri": None  # Cambiato da [] a None perché abbiamo un solo boss attivo
        }

        # Salvataggio Giocatori
        for p in manager.giocatori:
            dati_da_salvare["giocatori"].append(p.save_state().get_state())
        
        # --- CORREZIONE MOSTRi ---
        # Usiamo 'boss_attuale' che è il nome che abbiamo dato nel manager
        if manager.boss_attuale:
            # Salviamo lo stato memento del singolo boss
            dati_da_salvare["mostri"] = manager.boss_attuale.save_state().get_state()

        try:
            with open("salvataggio_gioco.json", "w") as f:
                json.dump(dati_da_salvare, f, indent=4)
            # Log rimosso o reso discreto per non intasare la console ogni volta che colpisci
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
        self.abilita= {"danno":0,"furtivita":0,"intelligenza":0}

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
        print(f"Log: {self.nome} ha subito {amount} danni. HP rimanenti: {self.hp}")

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

    def attacca(self, mostro, arma: Arma) -> int:
        if arma is None: danno_arma = 0
        else: danno_arma = getattr(arma, "danno", 0)    #“Se l’oggetto ha questo attributo, usalo. Se NON ce l’ha, usa il valore di default, 0.”
        danno_totale = self.abilita["danno"] + danno_arma
        print(f"{self.nome} attacca {mostro.nome} per {danno_totale} danni")
        mostro.take_damage(danno_totale)
        return danno_totale
    
    def fuggi(self, mostro) -> bool:
        if isinstance(mostro, SerpenteTreTeste):
            print(f"{self.nome} tenta di fuggire: IMPOSSIBILE (Serpente a Tre Teste)")
            return False
        diff = abs(self.abilita["furtivita"] - mostro.furtivita)
        if diff <= 3:
            self.abilita["furtivita"] += 1
            self.notify()
            print(f"{self.nome} tenta di fuggire: RIUSCITA! Furtività aumentata a {self.abilita['furtivita']}")
            return True
        else:
            print(f"{self.nome} tenta di fuggire: FALLITA (diff = {diff})")
            return False
    
    def ragiona(self, mostro) -> bool:
        diff = abs(self.abilita["intelligenza"] - mostro.intelligenza)
        if diff <= 3:
            self.abilita["intelligenza"] += 1
            self.moralita += 1
            self.notify()
            print(f"{self.nome} prova a ragionare con {mostro.nome}: SUCCESSO! Intelligenza aumentata a {self.abilita['intelligenza']}. Moralità aumentata a {self.moralita}")
            return True
        else:
            print(f"{self.nome} prova a ragionare con {mostro.nome}: FALLIMENTO (diff = {diff})")
            return False


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

class Mostro(Subject, ABC):
    def __init__(self, nome: str, hp: int, danno: int, furtivita: int, intelligenza: int, x=0, y=0):
        super().__init__()
        self.nome = nome
        
        # --- CORREZIONE QUI ---
        # Assegna direttamente alla variabile interna _max_hp
        self._max_hp = hp  
        
        # Ora puoi assegnare hp (che userà il setter di hp definito prima)
        self.hp = hp       
        
        self.danno = danno
        self.furtivita = furtivita
        self.intelligenza = intelligenza
        self.pos = [x, y]

    @property
    def max_hp(self) -> int:
        return self._max_hp
    
    # Se vuoi poter modificare il tetto massimo durante il gioco, aggiungi questo:
    @max_hp.setter
    def max_hp(self, valore: int):
        self._max_hp = valore

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp < 0: self.hp = 0
        print(f"Log: {self.nome} ha subito {amount} danni. HP rimanenti: {self.hp}")
        self.notify()

    @abstractmethod
    def attacca(self, player) -> None:
        pass

    def save_state(self) -> MostroMemento:
        return MostroMemento({
            "type": self.__class__.__name__,
            "nome": self.nome,
            "hp": self.hp,
            "max_hp": self.max_hp, 
            "danno": self.danno,
            "furtivita": self.furtivita,
            "intelligenza": self.intelligenza,
            "pos": self.pos
        })

    def restore_state(self, memento: MostroMemento) -> None:
        state = memento.get_state()

        self.nome = state["nome"]
        self._max_hp = state.get("max_hp", self._max_hp)
        self.hp = state.get("hp", self._max_hp)
        self.danno = state["danno"]
        self.furtivita = state["furtivita"]
        self.intelligenza = state["intelligenza"]
        self.pos = state["pos"]
        self.notify()


# ---------- CONCRETE PRODUCTS ----------

class Goblin(Mostro):
    def __init__(self, x=0, y=0):
        super().__init__(nome="Goblin", hp=40, danno=10, furtivita=8, intelligenza=4,x=x,y=y)
        self.pos = [x, y] # Ci serve per sapere dove disegnarlo nella GUI

    def attacca(self, player) -> None:
        print(f"{self.nome} attacca {player.nome} per {self.danno} danni")
        player.take_damage(self.danno)
        self.notify()  # <-- questo farà partire AutoSave


class Anubi(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Anubi", hp=80, danno=15, furtivita=1, intelligenza=2,x=x,y=y)
        self.pos = [x, y] 

    def attacca(self, player) -> None:
        print(f"{self.nome} attacca {player.nome} per {self.danno} danni")
        player.take_damage(self.danno)
        self.notify()  # <-- questo farà partire AutoSave


class Chica(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Chica",hp=100, danno=20, furtivita=8, intelligenza=4,x=x,y=y)

    def attacca(self, player) -> None:
        print(f"{self.nome} attacca {player.nome} per {self.danno} danni")
        player.take_damage(self.danno)
        self.notify()  # <-- questo farà partire AutoSave


class Yeti(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Yeti delle Nevi", hp=140, danno=30, furtivita=7, intelligenza=5,x=x,y=y)

    def attacca(self, player) -> None:
        print(f"{self.nome} attacca {player.nome} per {self.danno} danni")
        player.take_damage(self.danno)
        self.notify()  # <-- questo farà partire AutoSave


class SerpenteTreTeste(Mostro):
    def __init__(self,x=0,y=0):
        super().__init__(nome="Serpente a Tre Teste", hp=200, danno=70, furtivita=10, intelligenza=10,x=x,y=y)

    def attacca(self, player) -> None:
        print(f"{self.nome} attacca {player.nome} per {self.danno} danni")
        player.take_damage(self.danno)
        self.notify()  # <-- questo farà partire AutoSave


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
        self.boss_attuale = None
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

            # 1. DATI GLOBALI
            if isinstance(contenuto, dict):
                self.manager.livello_corrente = contenuto.get("livello_corrente", 1)
                self.manager.vite_rimanenti = contenuto.get("vite_rimanenti", 5)
                lista_giocatori = contenuto.get("giocatori", [])
                # Usiamo la chiave "mostri" come hai specificato tu
                dati_salvatore_mostro = contenuto.get("mostri") 
            else:
                # Gestione vecchio formato (solo lista giocatori)
                lista_giocatori = contenuto
                self.manager.livello_corrente = 1
                self.manager.vite_rimanenti = 5
                dati_salvatore_mostro = None

            # 2. RIPRISTINO GIOCATORI
            self.manager.giocatori.clear()
            for d in lista_giocatori:
                if d.get("type") == "Player2":
                    p = Player2(d["nome"], d["moralita"])
                else:
                    p = Player1(d["nome"], d["moralita"])

                p.restore_state(CharacterMemento(d))
                if self.auto_saver:
                    p.attach(self.auto_saver)
                self.manager.giocatori.append(p)

            if dati_salvatore_mostro:
                classe_nome = dati_salvatore_mostro.get("type")
                ClasseBoss = globals().get(classe_nome)
                
                if ClasseBoss:
                    pos = dati_salvatore_mostro.get("pos", [0, 0])
                    # 1. Creiamo il boss (il costruttore metterà HP al massimo)
                    nuovo_boss = ClasseBoss(x=pos[0], y=pos[1])
                    
                    # 2. SOVRASCRIVIAMO GLI HP con quelli del salvataggio
                    # Usiamo getattr per sicurezza
                    hp_salvati = dati_salvatore_mostro.get("hp")
                    max_hp_salvato = dati_salvatore_mostro.get("max_hp")

                    if hp_salvati is not None:
                        # Prima il massimo, poi l'attuale per non far scattare i limiti del setter
                        nuovo_boss._max_hp = max_hp_salvato
                        nuovo_boss.hp = hp_salvati # Questo chiama notify() e aggiorna la barra
                    
                    self.manager.boss_attuale = nuovo_boss
                    print(f"Log: Ripristinato {nuovo_boss.nome} con {nuovo_boss.hp} HP")
            
            return True

        except Exception as e:
            print(f"Errore critico caricamento: {e}")
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