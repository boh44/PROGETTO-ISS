import pygame
import sys
import os
from LogicaGioco import *
from livelli import GestoreLivelli

# --- 0. INIZIALIZZAZIONE ---
pygame.init()
LARGHEZZA, ALTEZZA = 800, 600
screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
pygame.display.set_caption("Beyond the Screen")
clock = pygame.time.Clock()
alpha_fade = 0  # Gestisce la trasparenza del velo nero
fase_transizione = None 
colore_transizione = (0, 0, 0) # Default nero

def disegna_pannello_stats(surface, player, x, y):
    
    sfondo = pygame.Surface((150, 110), pygame.SRCALPHA)
    sfondo.fill((0, 0, 0, 180)) # Nero più opaco per leggere meglio
    pygame.draw.rect(sfondo, (255, 255, 255), sfondo.get_rect(), width=1, border_radius=5)
    surface.blit(sfondo, (x, y))

    font_nome = pygame.font.SysFont("Constantia", 16, bold=True)
    font_s = pygame.font.SysFont("Constantia", 14)
    
    # Nome del Player in alto
    nome_surf = font_nome.render(player.nome.upper(), True, (255, 255, 255))
    surface.blit(nome_surf, (x + 10, y + 8))
    
    # Linea divisoria
    pygame.draw.line(surface, (100, 100, 100), (x + 10, y + 28), (x + 140, y + 28))
    
    stats = [
        (f"Moralità: {player.moralita}/10", (255, 215, 0)),
        (f"Danno: {player.danno}/10", (255, 80, 80)),
        (f"Furtività: {player.furtivita}/10", (100, 200, 255)),
        (f"Intelligenza: {player.intelligenza}/10", (150, 255, 150))
    ]

    for i, (testo, colore) in enumerate(stats):
        txt_surf = font_s.render(testo, True, colore)
        surface.blit(txt_surf, (x + 10, y + 35 + (i * 18)))

class ToggleSelector:
    """Selettore per le impostazioni (Stile Tkinter)"""
    def __init__(self, rect, titolo, opzioni, indice_iniziale=0, callback=None):
        self.rect = rect
        self.titolo = titolo
        self.opzioni = opzioni
        self.index = indice_iniziale
        self.callback = callback
        
        self.font = pygame.font.SysFont("Constantia", 25, bold=True)
        self.arrow_font = pygame.font.SysFont("Arial", 30, bold=True)

        w_arrow = 30
        # Posizioni delle frecce relative al rettangolo principale
        self.rect_sx = pygame.Rect(rect.right - 200, rect.y, w_arrow, rect.height)
        self.rect_dx = pygame.Rect(rect.right - 40, rect.y, w_arrow, rect.height)
    
    def disegna(self, surface):
        # Disegna Titolo
        txt_titolo = self.font.render(self.titolo, True, (255, 255, 255))
        surface.blit(txt_titolo, (self.rect.x + 10, self.rect.centery - txt_titolo.get_height()//2))

        # Disegna Freccia SX
        col_sx = (255, 255, 255) if self.rect_sx.collidepoint(pygame.mouse.get_pos()) else (90, 106, 130)
        surface.blit(self.arrow_font.render(" < ", True, col_sx), (self.rect_sx.x, self.rect_sx.y + 5))

        # Disegna Valore Centrale
        testo_opzione = self.opzioni[self.index]
        txt_val = self.font.render(testo_opzione, True, (255, 255, 255))
        centro_x = (self.rect_sx.right + self.rect_dx.left) // 2
        surface.blit(txt_val, (centro_x - txt_val.get_width()//2, self.rect.centery - txt_val.get_height()//2))

        # Disegna Freccia DX
        col_dx = (255, 255, 255) if self.rect_dx.collidepoint(pygame.mouse.get_pos()) else (90, 106, 130)
        surface.blit(self.arrow_font.render(" > ", True, col_dx), (self.rect_dx.x, self.rect_dx.y + 5))

    def gestisci_click(self, pos):
        cambio = 0
        if self.rect_sx.collidepoint(pos): cambio = -1
        elif self.rect_dx.collidepoint(pos): cambio = 1
        
        if cambio != 0:
            self.index = (self.index + cambio) % len(self.opzioni)
            if self.callback: self.callback(self.opzioni[self.index])
            return True
        return False

class InventoryUI:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player
        self.slot_size = 50
        self.padding = 8
        self.font = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_cat = pygame.font.SysFont("Arial", 10, bold=True)
        self.categorie = ["Attacco", "Cura", "Utility"]

    def disegna(self, surface, categoria_attiva):
        # Sposto tutto l'inventario 40 pixel più in basso rispetto alla barra vita
        y_offset = self.y + 40 
        
        # 1. Box Sfondo (190px larghezza)
        rect_bg = pygame.Rect(self.x - 10, y_offset, 190, 100) 
        pygame.draw.rect(surface, (30, 30, 30), rect_bg, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), rect_bg, width=2, border_radius=8)

        # 2. Scritte Categorie
        for i, cat in enumerate(self.categorie):
            colore = (255, 215, 0) if cat.lower() == categoria_attiva.lower() else (150, 150, 150)
            txt_cat = self.font_cat.render(cat.upper(), True, colore)
            surface.blit(txt_cat, (self.x + (i * 60), y_offset + 10))

        # Filtriamo l'inventario del player
        oggetti_filtrati = [item for item in self.player._inventario if item.tipo.lower() == categoria_attiva.lower()]
        
        current_x = self.x
        for item in oggetti_filtrati:
            # Slot posizionato sotto le scritte delle categorie
            rect_slot = pygame.Rect(current_x, y_offset + 40, self.slot_size, self.slot_size)
            
            pygame.draw.rect(surface, (50, 50, 50), rect_slot, border_radius=5)
            pygame.draw.rect(surface, (255, 215, 0), rect_slot, width=1, border_radius=5)

            # Nome oggetto
            txt = self.font.render(item.nome.upper(), True, (255, 255, 255))
            surface.blit(txt, (rect_slot.centerx - txt.get_width()//2, 
                               rect_slot.centery - txt.get_height()//2))
            
            current_x += self.slot_size + self.padding
    
    @staticmethod
    def aggiorna_inventario(player, arma=None, pozione=None, armatura=None):
        # 1. Svuota il vecchio equipaggiamento
        player._inventario._items.clear() 
        
        # 2. Lista degli oggetti da processare
        oggetti = [
            (arma, "Attacco"), 
            (pozione, "Cura"), 
            (armatura, "Utility")  
        ]
        
        for obj, tipo_default in oggetti:
            if obj is not None:
                if isinstance(obj, Item):
                    player.add_item(obj)
                else:
                    nome_classe = obj.__class__.__name__
                    valore = 0
                    if hasattr(obj, "danno"): valore = obj.danno
                    elif hasattr(obj, "cura"): valore = obj.cura
                    
                    
                    nuovo_item = Item(
                        nome=nome_classe, 
                        tipo=tipo_default, 
                        valore=valore, 
                        oggetto=obj
                    )
                    player.add_item(nuovo_item)
        
        player.notify()

class HealthBar(Observer):
    def __init__(self, x, y, w, h, player, mostra_vite=True, is_boss=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.player = player
        self.mostra_vite = mostra_vite 
        self.is_boss = is_boss 
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.player.attach(self)

    def update(self, subject: Subject) -> None:
        pass 

    def disegna(self, surface):
        # 1. ACCESSO AI DATI
        attuale_hp = getattr(self.player, '_hp', 0)
        massimo_hp = getattr(self.player, '_max_hp', 100)
        
        # Protezione per valori iniziali
        if attuale_hp == 0 and massimo_hp > 0:
            attuale_hp = self.player.hp 

        ratio = max(0, attuale_hp / massimo_hp) if massimo_hp > 0 else 0

        # 2. DISEGNO BARRA HP
        pygame.draw.rect(surface, (40, 40, 40), self.rect) 
        pygame.draw.rect(surface, (200, 200, 200), self.rect, width=1)
        
        current_width = int(self.rect.width * ratio)
        rect_hp = pygame.Rect(self.rect.x, self.rect.y, current_width, self.rect.height)
        
        # Colore barra 
        colore_barra = (39, 174, 96) if ratio > 0.3 else (192, 57, 43)
        pygame.draw.rect(surface, colore_barra, rect_hp) 

        # 3. DISEGNO CUORICINI (Solo per i Player)
        if self.mostra_vite and not self.is_boss:
            manager = GameManager.get_instance()
            vite_attuali = manager.vite_rimanenti
            colore_cuore = (220, 20, 60) # Rosso classico per i player
            
            raggio = 5
            spazio = 15
            start_x = self.rect.x + 2
            start_y = self.rect.y - 12 # Posizionati sopra la barra

            for i in range(6):
                pos_x = start_x + (i * spazio)
                attivo = i < vite_attuali
                col = colore_cuore if attivo else (60, 60, 60)
                spessore = 0 if attivo else 1 # Pieno se attivo, solo bordo se perso
                
                # Disegno lobi del cuore
                pygame.draw.circle(surface, col, (pos_x, start_y), raggio, width=spessore)
                pygame.draw.circle(surface, col, (pos_x + 6, start_y), raggio, width=spessore)
                
                # Disegno punta del cuore (triangolo)
                if attivo:
                    punti_triangolo = [(pos_x - raggio, start_y + 2), 
                                       (pos_x + 6 + raggio, start_y + 2), 
                                       (pos_x + 3, start_y + raggio + 4)]
                    pygame.draw.polygon(surface, col, punti_triangolo)

        # 4. TESTO HP
        testo_hp = f"{int(attuale_hp)} / {int(massimo_hp)}"
        txt_surf = self.font.render(testo_hp, True, (255, 255, 255))
        surface.blit(txt_surf, (self.rect.centerx - txt_surf.get_width()//2, 
                               self.rect.centery - txt_surf.get_height()//2))
class AnimatedSprite:
    def __init__(self, path, cols, rows, x, y, scale=2, flip=False):
        self.frames = []
        self.path = path
        try:
            # Se è un PNG usiamo convert_alpha(), se è JPG usiamo convert()
            if path.lower().endswith('.png'):
                full_sheet = pygame.image.load(path).convert_alpha()
            else:
                full_sheet = pygame.image.load(path).convert()
                # Se il JPG ha uno sfondo nero perfetto, lo rendiamo trasparente
                full_sheet.set_colorkey((0, 0, 0))
            
            sheet_rect = full_sheet.get_rect()
            frame_width = sheet_rect.width // cols
            frame_height = sheet_rect.height // rows
            
            for r in range(rows):
                for c in range(cols):
                    rect = pygame.Rect(c * frame_width, r * frame_height, frame_width, frame_height)
                    frame = full_sheet.subsurface(rect)
                    
                    if flip:
                        frame = pygame.transform.flip(frame, True, False)
                    
                    # Calcolo dimensioni intere per evitare sformature
                    nuova_larghezza = int(frame_width * scale)
                    nuova_altezza = int(frame_height * scale)
                    
                    frame = pygame.transform.scale(frame, (nuova_larghezza, nuova_altezza))
                    self.frames.append(frame)
            # Limita ai frame reali se lo sheet non è pieno (es. il goblin ne ha 9)
            if "goblin" in path.lower() and len(self.frames) > 9: 
                self.frames = self.frames[:9]
                
        except Exception as e:
            print(f"Errore: {e}")
            surf = pygame.Surface((50, 50))
            surf.fill((255, 0, 255))
            self.frames = [surf]

        self.index = 0
        self.animation_speed = 0.15
        self.pos = [x, y]
    def rescale(self, scale):
        """Aggiorna solo la scala dei frame senza resettare l'animazione."""
        self.scale = scale
        # Scaliamo ogni frame a partire dai frame originali
        for i, frame in enumerate(self.frames_original):
            self.frames[i] = pygame.transform.scale(
                frame,
                (int(frame.get_width() * scale), int(frame.get_height() * scale))
            )
    def disegna(self, surface, con_ombra=False):
        self.index += self.animation_speed
        if self.index >= len(self.frames):
            self.index = 0
        
        frame_attuale = self.frames[int(self.index)]
        rect = frame_attuale.get_rect(topleft=self.pos)

        if con_ombra:
            # 1. Dimensioni proporzionali
            larghezza_ombra = rect.width * 0.5
            altezza_ombra = rect.height * 0.10
            ombra_surf = pygame.Surface((larghezza_ombra, altezza_ombra), pygame.SRCALPHA)
            pygame.draw.ellipse(ombra_surf, (0, 0, 0, 80), ombra_surf.get_rect())
            
            # 2. GESTIONE OFFSET SPECIFICI (Altezza e Laterale)
            if hasattr(self, 'path') and "goblin" in self.path.lower():
                offset_y = 130  # Alza l'ombra per il Goblin
                offset_x = 90  # Sposta l'ombra a sinistra per il Goblin
            else:
                offset_y = 40  # Ombra normale ai piedi
                offset_x = 10  # Ombra centrata
            
            # 3. Calcolo posizione finale
            pos_x_ombra = rect.centerx - (larghezza_ombra // 2) - offset_x
            pos_y_ombra = rect.bottom - (altezza_ombra // 2) - offset_y
            
            surface.blit(ombra_surf, (pos_x_ombra, pos_y_ombra))

        # 4. Disegna lo sprite
        surface.blit(frame_attuale, self.pos)

#2. ASSET E RISORSE
def carica_asset(path, colore_fallback):
    try:
        return pygame.image.load(path).convert()
    except:
        surf = pygame.Surface((800, 600))
        surf.fill(colore_fallback)
        return surf

masters = {
    "menu":   carica_asset('sfondo.jpeg', (40, 40, 40)),
    "stanza": carica_asset('stanza.jpeg', (60, 60, 100)),
    "l0":     carica_asset('sfondo_livello0.jpeg', (20, 20, 20)),
    "mondi":  [
        carica_asset('livello_1.jpeg', (0, 50, 0)),
        carica_asset('livello_2.jpeg', (0, 50, 0)),
        carica_asset('livello_3.jpeg', (0, 50, 0)),
        carica_asset('livello_4.jpeg', (0, 50, 0)),
        carica_asset('livello_5.jpeg', (0, 50, 0)),
        ],
    "livello1": carica_asset('sfondo_livello1.jpeg', (30, 30, 30)),
    "livello2": carica_asset("sfondo_livello2.jpg",(30,30,30))
}
sfondi = {}
font_bottoni = pygame.font.SysFont("Constantia", 25, bold=True)
font_titolo = pygame.font.SysFont("Constantia", 50, bold=True)


# 3. VARIABILI UI GLOBALI 
larghezza_btn, altezza_btn = 200, 45
btn_start = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_settings = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_exit = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_nuovo = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_carica = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_eroe = pygame.Rect(0, 0, 180, 50)
btn_mercenario = pygame.Rect(0, 0, 180, 50)
btn_indifferente = pygame.Rect(0, 0, 180, 50)
btn_reset_data = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_back_menu  = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_attacca = pygame.Rect(LARGHEZZA//2 - 320, ALTEZZA - 80, 200, 50)
btn_fuggi   = pygame.Rect(LARGHEZZA//2 - 100, ALTEZZA - 80, 200, 50)
btn_ragiona = pygame.Rect(LARGHEZZA//2 + 120, ALTEZZA - 80, 200, 50)
toggle_schermo = None



# HUD (Barra Vita)
hud = {
    "p1_health": None,
    "p1_inv": None,
    "p2_health": None,
    "p2_inv": None
}

hud_config = {
    "show_inventory": False,
    "categoria_selezionata": "Attacco" # Default
}


# Il bottone centrale per le categorie
btn_zaino = pygame.Rect(LARGHEZZA // 2 - 50, 20, 100, 35)

# I bottoni quadrati per aprire gli inventari dei singoli player
rect_btn_p1 = pygame.Rect(230, 15, 35, 35) 
rect_btn_p2 = pygame.Rect(LARGHEZZA - 265, 15, 35, 35) 

# Variabili di stato per sapere se i rettangoli sono aperti o chiusi
inv_p1_aperto = False
inv_p2_aperto = False
# Variabile per mostrare/nascondere le statistiche
stats_p1_aperte = False
stats_p2_aperte = False

# Gestione categorie
categorie_disponibili = ["Attacco", "Cura", "Utility"]
idx_cat_p1 = 0
idx_cat_p2 = 0

# Variabile globale per alternanza giocatori
player_turn = 1 


def sincronizza_hud():
    global hud
    # 1. Reset completo (Fondamentale per l'Observer Pattern)
    hud["p1_health"] = None
    hud["p1_inv"] = None
    hud["p2_health"] = None
    hud["p2_inv"] = None
    hud["boss_health"] = None 

    # 2. Player 1
    if len(manager_gioco.giocatori) >= 1:
        p1 = manager_gioco.giocatori[0]
        hud["p1_health"] = HealthBar(20, 20, 200, 25, p1,mostra_vite=True)
        hud["p1_inv"] = InventoryUI(20, 55, p1)
        
    # 3. Player 2
    if len(manager_gioco.giocatori) >= 2:
        p2 = manager_gioco.giocatori[1]
        hud["p2_health"] = HealthBar(LARGHEZZA - 220, 20, 200, 25, p2,mostra_vite=True)
        hud["p2_inv"] = InventoryUI(LARGHEZZA - 220, 55, p2)

    # Boss
    attuale_boss = manager_gioco.boss_attuale 
    if attuale_boss:
        # Calcolo proporzionale per fullscreen o ridimensionamento
        w, h = screen.get_size()
        larg_b = int(w * 0.15)   # 15% larghezza schermo
        alt_b = int(h * 0.02)    # Altezza barra proporzionale
        bx = w // 2 - larg_b // 2
        by = int(h * 0.15)       # Posizione verticale proporzionale

        # Possiamo anche adattare posizione Y per boss specifici
        nome_boss = attuale_boss.nome.lower()
        if "goblin" in nome_boss:
            by = int(h * 0.10)
        elif "serpente" in nome_boss:
            by = int(h * 0.18)

        hud["boss_health"] = HealthBar(bx, by, larg_b, alt_b, attuale_boss, mostra_vite=False, is_boss=True)
        print(f"Log HUD: Boss collegato ({attuale_boss.nome}) in posizione ({bx},{by})")

def aggiorna_posizioni_e_scale(w, h,indice_livello=0):
    global sfondi, font_titolo, toggle_schermo
    
    # 1. Ridimensionamento Sfondi esistente
    for chiave, valore in masters.items():
        if chiave == "mondi":
            # Cicliamo la lista dei mondi e scaliamo ogni immagine
            sfondi[chiave] = [pygame.transform.scale(img, (w, h)) for img in valore]
        else:
            # Sfondi singoli (menu, stanza, l0)
            sfondi[chiave] = pygame.transform.scale(valore, (w, h))
    
    # 3. Riposizionamento Bottoni UI esistente
    x_c = (w - larghezza_btn) // 2
    btn_start.topleft = (x_c, h - 250)
    btn_settings.topleft = (x_c, h - 185)
    btn_exit.topleft = (x_c, h - 120)
    btn_nuovo.topleft = (x_c, h - 220)
    btn_carica.topleft = (x_c, h - 155)
    
    centro_x = w // 2
    btn_eroe.topleft = (centro_x - 290, h // 2)
    btn_mercenario.topleft = (centro_x - 90, h // 2)
    btn_indifferente.topleft = (centro_x + 110, h // 2)

    # 4. Settings e Toggle esistente
    btn_reset_data.topleft = (x_c, h // 2 + 10)
    btn_back_menu.topleft  = (x_c, h // 2 + 80)
    w_sel, h_sel = 600, 50
    rect_schermo = pygame.Rect((w - w_sel) // 2, h // 2 - 60, w_sel, h_sel)

    def on_change_schermo(valore):
        global LARGHEZZA, ALTEZZA
        if valore == "FULLSCREEN":
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)

        w, h = screen.get_size()
        LARGHEZZA, ALTEZZA = w, h

        gestore_livelli.ridimensiona_tutto(w, h)
        aggiorna_posizioni_e_scale(w, h)
        sincronizza_hud()  # <-- Aggiorna tutte le barre (player + boss)


    opzioni_video = ["FINESTRA", "FULLSCREEN"]
    idx = 1 if (screen.get_flags() & pygame.FULLSCREEN) else 0
    toggle_schermo = ToggleSelector(rect_schermo, "MODALITA' SCHERMO", opzioni_video, idx, on_change_schermo)

    # 5. HUD Dinamico esistente
    rect_btn_p1.topleft = (230, 15)
    rect_btn_p2.topleft = (w - 265, 15)

    if hud["p1_health"]:
        hud["p1_health"].rect = pygame.Rect(20, 20, 200, 25)
    if hud["p2_health"]:
        hud["p2_health"].rect = pygame.Rect(w - 220, 20, 200, 25)

    #bottoni di combattimento dinamici
    # Definiamo dimensioni proporzionali o fisse
    w_b, h_b = 200, 50
    spazio = 20
    y_pos = h - 80  # Distanza dal bordo inferiore
    centro_x = w // 2

    # Aggiorniamo i Rect globali esistenti
    btn_attacca.update(centro_x - (w_b * 1.5) - spazio, y_pos, w_b, h_b)
    btn_fuggi.update(centro_x - (w_b // 2), y_pos, w_b, h_b)
    btn_ragiona.update(centro_x + (w_b // 2) + spazio, y_pos, w_b, h_b)

   #Parametri scala e posizione
    ratio = w / 800
    scala_p = ratio * 3
    
    pos_y_personaggi = 250
    alt_y_comune = 250 # Posizione a terra (usata per Anubi, Chica, Yeti e ora Serpente)
    alt_y_goblin = 20  # Posizione alta specifica per il Goblin
    
    # Coordinate X dei Player (proporzionali alla larghezza)
    x_p1 = int(w * 0.12)
    x_p2 = int(w * 0.68)
    
    # Creazione Player
    nuovo_p1 = AnimatedSprite(path_idle, 4, 1, x_p1, pos_y_personaggi, scale=scala_p)
    nuovo_p2 = AnimatedSprite(path_idle, 4, 1, x_p2, pos_y_personaggi, scale=scala_p, flip=True)

    nuovo_boss_visual = None

    # GESTIONE BOSS
    if indice_livello == 0: # GOBLIN
        nuovo_boss_visual = AnimatedSprite("goblin.png", 5, 2, 0, alt_y_goblin, scale=ratio * 2.0)
    
    elif indice_livello == 1: # ANUBI
        nuovo_boss_visual = AnimatedSprite("anubi.png", 5, 1, 0, alt_y_comune, scale=ratio * 0.2)
        nuovo_boss_visual.animation_speed = 0.04

    elif indice_livello == 2: # CHICA
        nuovo_boss_visual = AnimatedSprite("chica.png", 5, 1, 0, alt_y_comune, scale=ratio * 1)

    elif indice_livello == 3: # YETI
        nuovo_boss_visual = AnimatedSprite("yeti.png", 5, 1, 0, alt_y_comune, scale=ratio * 1.5)

    elif indice_livello == 4: # SERPENTE
        # Usiamo alt_y_comune (250) per farlo stare in basso
        nuovo_boss_visual = AnimatedSprite("serpente.png", 5, 1, 0, alt_y_comune, scale=ratio * 1.2)

  
    if nuovo_boss_visual:
        # Recuperiamo larghezza (w_f) e altezza (h_f) del primo frame
        w_f = nuovo_boss_visual.frames[0].get_width()
        h_f = nuovo_boss_visual.frames[0].get_height()
        
        # Calcolo dei centri esatti dello schermo
        centro_x = (w // 2) - (w_f // 2)
        centro_y = (h // 2) - (h_f // 2)
        
        if indice_livello == 0: # GOBLIN
            nuovo_boss_visual.pos = [centro_x + 100, centro_y-50] 
            
        elif indice_livello == 4: # SERPENTE
            nuovo_boss_visual.pos = [centro_x - 70, centro_y] 
            
        else:
            nuovo_boss_visual.pos = [centro_x, centro_y]

    return nuovo_p1, nuovo_p2, nuovo_boss_visual

path_idle = os.path.join("assets", "character", "idle", "idle-sheet.png")
path_goblin = os.path.join("goblin.png") 

# 1. Otteniamo i player e lo sprite temporaneo del boss dalle posizioni calcolate
personaggio1, personaggio2, sprite_temp = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

# 2. Creiamo la LOGICA basandoci sulla posizione REALE calcolata per lo sprite

goblin = Goblin(x=sprite_temp.pos[0] + 60, y=sprite_temp.pos[1])

# 3. Creiamo la GRAFICA del boss 
goblin_visual = sprite_temp

#INTRODUZIONE
stato_gioco = "MENU"
player_corrente = 1
nome_inserito = ""
input_nome_attivo = False
indice_lettura = 0

manager_gioco = GameManager.get_instance()
facade = GameFacade(manager_gioco, AutoSaveObserver())
gestore_livelli = GestoreLivelli(LARGHEZZA, ALTEZZA)

# Testi Completi
intro_frasi = [
    ["Ti svegli, confuso…", "Che strano sogno! Meglio alzarsi"], 
    ["C'era una cosa che volevi fare, ma cosa?"],
    ["Ah, certo! Provare il nuovo gioco!"],
    ["Lo prendi in mano e… starnutisci!", "È impolverato, meglio pulirlo prima."],
    ["Prendi un panno, lo pulisci e lo inserisci nel lettore…", "L’oscurità ti avvolge…"]
]

livello0_frasi = [
    [],
    ["Apri gli occhi… tutto è nero.", "Un senso di disagio ti avvolge."], 
    ["Davanti a te c'è un ragazzo… ma dove siete?"],
    ["Ti avvicini, provi a parlargli… nulla.", "Sembra perso quanto te."],
    ["All'improvviso, nel buio… una scritta appare!"],
    [
        "_Benvenuti nella vostra nuova avventura!_",
        "_D'ora in poi collaborerete per vincere._",
        "_Se non lo farete, rimarrete qui per sempre._"
    ],
    ["_Inserite i vostri nomi_"]
]

#Testi livelli 
testi_livello = {
    0: ["Benvenuti, avventurieri!", "Il primo mostro vi attende, preparatevi!"],
    1: ["Anubi veglia dall’ombra...", "Camminate con cautela tra le trappole!"],
    2: ["Una creatura misteriosa si palesa.", "Si fa chiamare Chica.", "Non sottovalutatela!"],
    3: ["Lo Yeti vi sfida con forza bestiale!", "Coraggio, non arretrate!"],
    4: ["Siete giunti all'ultimo livello.", "Il gioco si ricorda delle vostre scelte ed esse avranno un impatto.", "Preparatevi all’ultima sfida!"]
}

#label per livello
def draw_label_livello(surface, testo, larghezza, altezza):
    """Disegna una finestra nera semi-trasparente con il testo centrato in basso."""
    h_box = 130
    overlay = pygame.Surface((larghezza, altezza), pygame.SRCALPHA)
    overlay.fill((0,0,0,100))
    surface.blit(overlay, (0,0))

    box = pygame.Surface((larghezza - 40, h_box), pygame.SRCALPHA)
    box.fill((0,0,0,200))
    surface.blit(box, (20, altezza - h_box - 20))

    font = pygame.font.SysFont("Constantia", int(altezza * 0.035))
    for i, riga in enumerate(testo):
        testo_surf = font.render(riga, True, (255,255,255))
        surface.blit(testo_surf, (40, (altezza - h_box) + i * 30))


def draw_text_centered(testo, rettangolo, colore, font=font_bottoni):
    superficie = font.render(testo, True, colore)
    screen.blit(superficie, superficie.get_rect(center=rettangolo.center))
