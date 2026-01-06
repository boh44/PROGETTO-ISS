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
fase_transizione = None # Può essere "IN" o "OUT"
colore_transizione = (0, 0, 0) # Default nero

def disegna_pannello_stats(surface, player, x, y):
    # Sfondo leggermente più grande per ospitare il nome
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
        (f"Moralità: {player.moralita}", (255, 215, 0)),
        (f"Danno: {getattr(player, 'danno', 10)}", (255, 80, 80)),
        (f"Furtività: {getattr(player, 'furtivita', 5)}", (100, 200, 255)),
        (f"Intelligenza: {getattr(player, 'intelligenza', 5)}", (150, 255, 150))
    ]

    for i, (testo, colore) in enumerate(stats):
        txt_surf = font_s.render(testo, True, colore)
        surface.blit(txt_surf, (x + 10, y + 35 + (i * 18)))

# --- 1. CLASSI UTILITY (UI) ---
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
        # Spostiamo tutto l'inventario 40 pixel più in basso rispetto alla barra vita
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

        # 3. Disegna gli oggetti (SPADA E POZIONE)
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
class HealthBar(Observer):
    def __init__(self, x, y, w, h, player):
        self.rect = pygame.Rect(x, y, w, h)
        self.player = player
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.player.attach(self)

    def update(self, subject: Subject) -> None:
        pass 

    def disegna(self, surface):
        # 1. DISEGNO BARRA HP
        pygame.draw.rect(surface, (40, 40, 40), self.rect) # Sfondo più scuro
        pygame.draw.rect(surface, (80, 0, 0), self.rect, width=2)

        ratio = max(0, self.player.hp / self.player.max_hp) if self.player.max_hp > 0 else 0
        current_width = self.rect.width * ratio
        rect_hp = pygame.Rect(self.rect.x, self.rect.y, int(current_width), self.rect.height)
        
        # Colore sfumato: verde se alto, rosso se basso
        colore_barra = (0, 200, 0) if ratio > 0.3 else (255, 0, 0)
        pygame.draw.rect(surface, colore_barra, rect_hp) 

        # 2. DISEGNO CUORICINI (VITE) - PIÙ BASSI
        manager = GameManager.get_instance()
        vite_attuali = manager.vite_rimanenti
        
        raggio = 5      # Leggermente più piccoli per precisione
        spazio = 15     # Più compatti
        
        # start_y regolato: prima era -20, ora lo mettiamo a -12 
        # così i cuori sono molto vicini al bordo superiore della barra
        start_x = self.rect.x + 2
        start_y = self.rect.y - 12 

        for i in range(5):
            pos_x = start_x + (i * spazio)
            
            # Colore in base alla disponibilità della vita
            colore_cuore = (220, 20, 60) if i < vite_attuali else (60, 60, 60)
            spessore = 0 if i < vite_attuali else 2 # Pieno se attivo, solo bordo se perso
            
            # Disegniamo la forma del cuore con due piccoli cerchi e un triangolo invertito
            # Parte superiore (i due lobi)
            pygame.draw.circle(surface, colore_cuore, (pos_x, start_y), raggio, width=spessore)
            pygame.draw.circle(surface, colore_cuore, (pos_x + 6, start_y), raggio, width=spessore)
            
            # Parte inferiore (punta del cuore) - Solo se il cuore è pieno
            if i < vite_attuali:
                punti_triangolo = [(pos_x - raggio, start_y + 2), 
                                   (pos_x + 6 + raggio, start_y + 2), 
                                   (pos_x + 3, start_y + raggio + 4)]
                pygame.draw.polygon(surface, colore_cuore, punti_triangolo)

        # 3. TESTO HP (Opzionale, lo mettiamo centrato)
        txt = f"{self.player.hp}"
        txt_surf = self.font.render(txt, True, (255, 255, 255))
        surface.blit(txt_surf, (self.rect.centerx - txt_surf.get_width()//2, self.rect.centery - txt_surf.get_height()//2))
class AnimatedSprite:
    def __init__(self, path, cols, rows, x, y, scale=2, flip=False):
        self.frames = []
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

    def disegna(self, surface, con_ombra=False):
        self.index += self.animation_speed
        if self.index >= len(self.frames):
            self.index = 0
        
        frame_attuale = self.frames[int(self.index)]
        rect = frame_attuale.get_rect(topleft=self.pos)

        if con_ombra:
            # 1. Creiamo una superficie per l'ombra con supporto trasparenza (Alpha)
            larghezza_ombra = rect.width * 0.6
            altezza_ombra = rect.height * 0.2
            ombra_surf = pygame.Surface((larghezza_ombra, altezza_ombra), pygame.SRCALPHA)
            
            # 2. Disegniamo un'ellisse nera semitrasparente (valore 100 su 255)
            pygame.draw.ellipse(ombra_surf, (0, 0, 0, 100), ombra_surf.get_rect())
            
            pos_ombra = (rect.centerx - larghezza_ombra // 2-60, rect.bottom - altezza_ombra // 2 - 80)
            surface.blit(ombra_surf, pos_ombra)

        # 4. Disegniamo lo sprite sopra l'ombra
        surface.blit(frame_attuale, self.pos)


# --- 2. ASSET E RISORSE ---
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


# --- 3. VARIABILI UI GLOBALI ---
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
toggle_schermo = None 

# HUD (Barra Vita)
# Sostituisci le variabili singole con questo dizionario
hud = {
    "p1_health": None,
    "p1_inv": None,
    "p2_health": None,
    "p2_inv": None
}

# Sotto la definizione di hud (riga 135 circa)
hud_config = {
    "show_inventory": False,
    "categoria_selezionata": "Attacco" # Default
}

# --- 3. VARIABILI UI GLOBALI ---
# (Sotto gli altri bottoni esistenti)

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

def sincronizza_hud():
    """Ricostruisce l'HUD basandosi sui giocatori attualmente nel manager"""
    # Resettiamo tutto per evitare fantasmi grafici
    hud["p1_health"] = None
    hud["p1_inv"] = None
    hud["p2_health"] = None
    hud["p2_inv"] = None
    
    if len(manager_gioco.giocatori) >= 1:
        p1 = manager_gioco.giocatori[0]
        hud["p1_health"] = HealthBar(20, 20, 200, 25, p1)
        hud["p1_inv"] = InventoryUI(20, 55, p1)
        print(f"Log HUD: P1 sincronizzato ({p1.nome})")
        
    if len(manager_gioco.giocatori) >= 2:
        p2 = manager_gioco.giocatori[1]
        hud["p2_health"] = HealthBar(LARGHEZZA - 220, 20, 200, 25, p2)
        hud["p2_inv"] = InventoryUI(LARGHEZZA - 220, 55, p2)
        print(f"Log HUD: P2 sincronizzato ({p2.nome})")
        
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
        if valore == "FULLSCREEN": 
            pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        else: 
            pygame.display.set_mode((w, h), pygame.RESIZABLE)
        gestore_livelli.ridimensiona_tutto(w, h)

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

    # --- 6. AGGIORNAMENTO SPRITE ---
    ratio = w / 800
    scala_p = ratio * 3
    
    pos_y_personaggi = 250
    alt_y_comune = 250 # La posizione Y che vuoi per TUTTI i boss
    alt_y_goblin = 10  # Posizione alta specifica per il Goblin
    # Coordinate X dei Player
    x_p1 = int(w * 0.12)
    x_p2 = int(w * 0.68)
    
    # Creazione Player
    nuovo_p1 = AnimatedSprite(path_idle, 4, 1, x_p1, pos_y_personaggi, scale=scala_p)
    nuovo_p2 = AnimatedSprite(path_idle, 4, 1, x_p2, pos_y_personaggi, scale=scala_p, flip=True)

    # --- GESTIONE DINAMICA BOSS ---
    nuovo_boss_visual = None

    # Definiamo i parametri specifici per ogni boss ma la logica di posizionamento è identica
    if indice_livello == 0: # GOBLIN
        nuovo_boss_visual = AnimatedSprite("goblin.png", 5, 2, 0, alt_y_goblin, scale=ratio * 1.5)
    
    elif indice_livello == 1: # ANUBI
        nuovo_boss_visual = AnimatedSprite("anubi.png", 5, 1, 0, alt_y_comune, scale=ratio * 0.1)
        nuovo_boss_visual.animation_speed = 0.04

    elif indice_livello == 2: # CHICA
        nuovo_boss_visual = AnimatedSprite("chica.png", 5, 1, 0, alt_y_comune, scale=ratio * 1)

    elif indice_livello == 3: # YETI
        nuovo_boss_visual = AnimatedSprite("yeti.png", 5, 1, 0, alt_y_comune, scale=ratio * 1)

    elif indice_livello == 4: # SERPENTE
        nuovo_boss_visual = AnimatedSprite("serpente.png", 5, 1, 0, alt_y_goblin, scale=ratio * 1.5)

    # --- CENTRAMENTO UNIFICATO ---
    # Questa parte ora vale per TUTTI i mostri: calcola la larghezza del frame e centra
    if nuovo_boss_visual:
        w_f = nuovo_boss_visual.frames[0].get_width()
        nuovo_boss_visual.pos = [(w // 2) - (w_f // 2), alt_y_comune]

    return nuovo_p1, nuovo_p2, nuovo_boss_visual

# --- 4. LOGICA GIOCO ---

path_idle = os.path.join("assets", "character", "idle", "idle-sheet.png")
path_goblin = os.path.join("goblin.png") 

# 1. Otteniamo i player e lo sprite temporaneo del boss dalle posizioni calcolate
personaggio1, personaggio2, sprite_temp = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

# 2. Creiamo la LOGICA del boss (quella che ha HP e is_alive)
# Usiamo il nome 'goblin' perché è quello che usi nel loop GAMEPLAY
goblin = Goblin(x=sprite_temp.pos[0], y=sprite_temp.pos[1]) 

# 3. Creiamo la GRAFICA del boss (quella che ha il metodo disegna)
goblin_visual = sprite_temp

# --- STATO INIZIALE ---
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

def draw_text_centered(testo, rettangolo, colore, font=font_bottoni):
    superficie = font.render(testo, True, colore)
    screen.blit(superficie, superficie.get_rect(center=rettangolo.center))

# --- 5. LOOP PRINCIPALE ---
# 1. Otteniamo lo sprite corretto (passando 0 come indice per il Goblin)
personaggio1, personaggio2, sprite_temp = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, 0)

# 2. Creiamo la LOGICA con la Y corretta (40)
goblin = Goblin(x=sprite_temp.pos[0]+60, y=40) 

# 3. Assegniamo la grafica
goblin_visual = sprite_temp
BOSS_MAP = {
    0: Goblin,
    1: Anubi,
    2: Chica,
    3: Yeti,
    4: SerpenteTreTeste
}
mostra_messaggio_livello = False
timer_messaggio = 0
testo_passaggio = ""
running = True
while running:
    pos_mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if stato_gioco in ["VITTORIA", "GAME_OVER"]:
                    manager_gioco.resetGameData()
                    stato_gioco = "SCELTA" # Torna al menu iniziale

        if event.type == pygame.VIDEORESIZE:
            LARGHEZZA, ALTEZZA = event.w, event.h
            # Se non è in fullscreen, aggiorna la finestra
            if not (screen.get_flags() & pygame.FULLSCREEN):
                screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
            
            # 1. Ridimensiona gli sfondi nel gestore livelli
            gestore_livelli.ridimensiona_tutto(LARGHEZZA, ALTEZZA)
            
            # 2. RECUPERA L'INDICE ATTUALE (0 per Goblin, 1 per Anubi, ecc.)
            # Questo permette alla funzione di sapere quale Y e quale scala usare
            indice_attuale = gestore_livelli.indice_corrente 
            
            # 3. AGGIORNA POSIZIONI E SCALE
            personaggio1, personaggio2, nuovo_boss_visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, indice_attuale)
            
            # 4. SINCRONIZZA LE VARIABILI ATTIVE
            # Sovrascriviamo la variabile visiva con quella appena ricalcolata
            goblin_visual = nuovo_boss_visual
            
            # Sincronizziamo la posizione della LOGICA (fondamentale per le collisioni)
            # Usiamo list() o una tupla per copiare le coordinate
            goblin.pos = (nuovo_boss_visual.pos[0], nuovo_boss_visual.pos[1])

        if event.type == pygame.KEYDOWN:    # Controlla se un tasto è stato premuto.
            # Tasto K: Uccide il boss
            if event.key == pygame.K_k:
                goblin.hp = 0
            
            # --- TEST PLAYER 1 (Tasto L) ---
            if event.key == pygame.K_l:
                if stato_gioco == "GAMEPLAY" and manager_gioco.vite_rimanenti > 0:
                    if len(manager_gioco.giocatori) > 0:
                        manager_gioco.giocatori[0].take_damage(50)
                        print(f"P1 subisce danno! HP: {manager_gioco.giocatori[0].hp} | Vite: {manager_gioco.vite_rimanenti}")

            # --- TEST PLAYER 2 (Tasto S) ---
            if event.key == pygame.K_s:
                if stato_gioco == "GAMEPLAY" and manager_gioco.vite_rimanenti > 0:
                    # Controlliamo che esista il secondo giocatore
                    if len(manager_gioco.giocatori) > 1:
                        manager_gioco.giocatori[1].take_damage(50)
                        print(f"P2 subisce danno! HP: {manager_gioco.giocatori[1].hp} | Vite: {manager_gioco.vite_rimanenti}")
                    else:
                        print("DEBUG: Player 2 non presente!")
            # Tasto TAB per le stats del Player 1
            if event.key == pygame.K_TAB:
                stats_p1_aperte = not stats_p1_aperte
            
            # Tasto BACKSLASH (o quello che preferisci) per le stats del Player 2
            if event.key == pygame.K_BACKSLASH:
                stats_p2_aperte = not stats_p2_aperte

            # Gestione input nome (già esistente)
            if input_nome_attivo:
                if event.key == pygame.K_RETURN and len(nome_inserito) > 1: 
                    input_nome_attivo = False 
                    stato_gioco = "SCELTA_MORALITA"
                elif event.key == pygame.K_BACKSPACE:
                    nome_inserito = nome_inserito[:-1] 
                else: 
                    if len(nome_inserito) < 12: 
                        nome_inserito += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  #Controlla se il mouse viene premuto con il tasto sinistro
            if stato_gioco == "MENU":   #Cambia lo stato di gioco in base al pulsante cliccato: avvia nuova partita, apri le impostazioni o esci dal gioco.
                if btn_start.collidepoint(pos_mouse): stato_gioco = "SCELTA"
                elif btn_settings.collidepoint(pos_mouse): stato_gioco = "SETTINGS"
                elif btn_exit.collidepoint(pos_mouse): running = False
            
            elif stato_gioco == "SETTINGS": #se siamo nel setting
                if toggle_schermo.gestisci_click(pos_mouse):    #Controlla se il toggle dello schermo (finestra/fullscreen) è stato cliccato.
                    pass
                elif btn_reset_data.collidepoint(pos_mouse):    #Se clicchi su “RESET DATI”, cancella il salvataggio e resettare i dati del gioco.
                    if os.path.exists("salvataggio_gioco.json"): 
                        os.remove("salvataggio_gioco.json")
                    manager_gioco.resetGameData()
                    if facade.auto_saver: facade.auto_saver.history = []
                    print("Log: Reset eseguito.")
                elif btn_back_menu.collidepoint(pos_mouse):     #senno torniamo al menu
                    stato_gioco = "MENU"

            elif stato_gioco == "SCELTA":
                if btn_nuovo.collidepoint(pos_mouse): 
                    # Reset per nuova partita
                    manager_gioco.livello_corrente = 1
                    gestore_livelli.indice_corrente = 0
                    stato_gioco, indice_lettura = "INTRODUZIONE", 0
                    
                elif btn_carica.collidepoint(pos_mouse):
                    if facade.carica_da_disco():
                        # 1. SINCRONIZZA GLI INDICI
                        # Se il manager ha caricato '3', l'indice della lista deve essere 2
                        indice_da_caricare = max(0, manager_gioco.livello_corrente - 1)
                        gestore_livelli.indice_corrente = indice_da_caricare
                        
                        # 2. RIESUMA GLI OSSERVATORI
                        # Fondamentale: i player caricati devono poter salvare di nuovo
                        for p in manager_gioco.giocatori:
                            p.attach(facade.auto_saver)
                        
                        # 3. RIGENERA IL MONDO (Grafica e Logica)
                        personaggio1, personaggio2, nuovo_boss_visual = aggiorna_posizioni_e_scale(
                            LARGHEZZA, ALTEZZA, gestore_livelli.indice_corrente
                        )
                        goblin_visual = nuovo_boss_visual
                        
                        # Recupera il tipo di Boss corretto dal dizionario BOSS_MAP
                        ClasseBoss = BOSS_MAP.get(gestore_livelli.indice_corrente)
                        if ClasseBoss:
                            goblin = ClasseBoss(x=goblin_visual.pos[0], y=goblin_visual.pos[1])
                        
                        # 4. SINCRONIZZA L'HUD (Barre vita e Inventari)
                        sincronizza_hud()
                        
                        if len(manager_gioco.giocatori) > 0:
                            p1 = manager_gioco.giocatori[0]
                            hud["p1_health"] = HealthBar(20, 20, 200, 25, p1)
                            hud["p1_inv"] = InventoryUI(20, 55, p1)
                            
                        if len(manager_gioco.giocatori) > 1:
                            p2 = manager_gioco.giocatori[1]
                            hud["p2_health"] = HealthBar(LARGHEZZA - 220, 20, 200, 25, p2)
                            hud["p2_inv"] = InventoryUI(LARGHEZZA - 220, 55, p2)

                        # 5. AVVIA IL GIOCO
                        stato_gioco = "GAMEPLAY"
                        print(f"Log: Caricato Livello {manager_gioco.livello_corrente} (Indice {gestore_livelli.indice_corrente})")
                    else: 
                        print("Errore: Nessun salvataggio trovato o file corrotto.")

            elif stato_gioco == "INTRODUZIONE":
                indice_lettura += 1
                if indice_lettura >= len(intro_frasi): 
                    stato_gioco, indice_lettura = "LIVELLO_0", 0
            
            elif stato_gioco == "LIVELLO_0":
                if indice_lettura == len(livello0_frasi) - 1: 
                    input_nome_attivo = True
                else: 
                    indice_lettura += 1
            
            elif stato_gioco == "SCELTA_MORALITA":
                scelta = None
                if btn_eroe.collidepoint(pos_mouse): scelta = "eroe altruista"
                elif btn_mercenario.collidepoint(pos_mouse): scelta = "mercenario egoista"
                elif btn_indifferente.collidepoint(pos_mouse): scelta = "anima indifferente"

                if scelta:
                    creator = Player1Creator() if player_corrente == 1 else Player2Creator()
                    
                    # 1. CREA IL PERSONAGGIO
                    nome = valida_nome(nome_inserito, player_corrente)
                    p = creator.create_character(nome, 0)
                    
                    # 2. AGGIUNGI L'ITEM SUBITO (Prima di salvarlo!)
                    p.add_item(Item("SpadaBase", "Attacco", 10, oggetto=SpadaBase()))
                    p.add_item(Item("PozioneCura", "Cura", 10, oggetto=PozioneCura()))
                    
                    # 3. AGGIUNGI AL MANAGER E COLLEGA L'OSSERVATORE
                    # Questo è fondamentale affinché l'AutoSave veda il player nella lista
                    manager_gioco.giocatori.append(p)
                    p.attach(facade.auto_saver)
                    
                    # 4. ASSEGNA MORALITA (Questo triggera il metodo di salvataggio nel file LogicaGioco)
                    assegna_moralita(p, scelta) 
                    
                    # 5. AGGIORNA LA GRAFICA
                    sincronizza_hud()
                    
                    if player_corrente == 1:
                        player_corrente = 2
                        nome_inserito = ""
                        stato_gioco = "LIVELLO_0"
                        input_nome_attivo = True
                        indice_lettura = 6 
                    else:
                        stato_gioco = "MAPPA_MONDI"
                        input_nome_attivo = False
                        # Reset livello per sicurezza prima di entrare nella mappa
                        gestore_livelli.indice_corrente = 0
       

            elif stato_gioco == "MAPPA_MONDI":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    ratio = LARGHEZZA / 800 
                    
                    #gestore_livelli.indice_corrente += 1
                    stato_gioco = "GAMEPLAY"
                    nuovo_indice = gestore_livelli.indice_corrente
                    
                    ClasseBoss = BOSS_MAP.get(nuovo_indice)
                    if ClasseBoss:
                        if nuovo_indice == 0:
                            nuova_y = 40  # Goblin alto
                            goblin_visual = AnimatedSprite("goblin.png", 5, 2, 60, nuova_y, scale=ratio * 1.5)
                        else:
                            nuova_y = 250 # Tutti gli altri boss "a terra
                        
                        # 1. IDENTIFICAZIONE ASSET E SCALE (Copiando lo stile di Anubi)
                        if nuovo_indice == 1: # ANUBI
                            goblin_visual = AnimatedSprite("anubi.png", 5, 1, 0, 10, scale=ratio * 0.1)
                            goblin_visual.animation_speed = 0.04
                        elif nuovo_indice == 2: # CHICA
                            goblin_visual = AnimatedSprite("chica.png", 5, 1, 0, nuova_y, scale=ratio * 1.0)
                        elif nuovo_indice == 3: # YETI
                            goblin_visual = AnimatedSprite("yeti.png", 5, 1, 0, nuova_y, scale=ratio * 1.0)
                        elif nuovo_indice == 4: # BOSS FINALE
                            nuova_y=40
                            goblin_visual = AnimatedSprite("serpente.png", 5, 1, 0, nuova_y, scale=ratio * 1.0)
                        
                        # 2. CALCOLO CENTRAMENTO (Fondamentale per tutti)
                        # Prendiamo la larghezza del frame appena creato
                        larghezza_frame = goblin_visual.frames[0].get_width()
                        nuova_x = (LARGHEZZA // 2) - (larghezza_frame // 2)
                        
                        # 3. ASSEGNAZIONE POSIZIONE FINALE (Grafica + Logica)
                        goblin_visual.pos = [nuova_x, nuova_y]
                        goblin = ClasseBoss(x=nuova_x, y=nuova_y)
                        
                    sincronizza_hud()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if stato_gioco == "GAMEPLAY":
                    
                    # --- PLAYER 1 ---
                    # Controlliamo prima se l'inventario è aperto per catturare il click sulle TAB
                    tab_p1_cliccata = False
                    if inv_p1_aperto:
                        # y_offset è self.y(50) + 40 = 90. Le tab sono tra 90 e 120.
                        if 90 < pos_mouse[1] < 125: 
                            if 20 < pos_mouse[0] < 80: idx_cat_p1 = 0; tab_p1_cliccata = True
                            elif 80 < pos_mouse[0] < 140: idx_cat_p1 = 1; tab_p1_cliccata = True
                            elif 140 < pos_mouse[0] < 200: idx_cat_p1 = 2; tab_p1_cliccata = True

                    # Se non abbiamo cliccato una TAB, allora controlliamo il pulsante INV
                    if not tab_p1_cliccata and rect_btn_p1.collidepoint(pos_mouse):
                        inv_p1_aperto = not inv_p1_aperto

                   
                # --- PLAYER 2 ---
                tab_p2_cliccata = False
                # Definiamo il punto di inizio X dell'inventario di P2
                x_inv_p2 = LARGHEZZA - 305 
                
                # --- PLAYER 2 ---
                if inv_p2_aperto:
                    # Stessa altezza del Player 1
                    if 90 < pos_mouse[1] < 125:
                        # Usiamo x_inv_p2 come base per le 3 tab
                        if x_inv_p2 < pos_mouse[0] < x_inv_p2 + 60:
                            idx_cat_p2 = 0; tab_p2_cliccata = True
                        elif x_inv_p2 + 60 < pos_mouse[0] < x_inv_p2 + 120:
                            idx_cat_p2 = 1; tab_p2_cliccata = True
                        elif x_inv_p2 + 120 < pos_mouse[0] < x_inv_p2 + 180:
                            idx_cat_p2 = 2; tab_p2_cliccata = True

                # Solo se NON ho cliccato una tab, controllo se devo chiudere l'inventario
                if not tab_p2_cliccata and rect_btn_p2.collidepoint(pos_mouse):
                    inv_p2_aperto = not inv_p2_aperto

               
    # --- 6. DISEGNO ---
    
    # Primo passo: Disegniamo lo sfondo base
    sfondo_base = None
    if stato_gioco in ["MENU", "SCELTA", "SETTINGS"]: 
        sfondo_base = sfondi["menu"]
    elif stato_gioco == "INTRODUZIONE": 
        sfondo_base = sfondi["stanza"]
    elif stato_gioco in ["LIVELLO_0", "SCELTA_MORALITA"]: 
        sfondo_base = sfondi["l0"]
    elif stato_gioco == "MAPPA_MONDI": 
        sfondo_base = sfondi["mondi"][0]
    elif stato_gioco == "GAMEPLAY": 
        sfondo_base = gestore_livelli.get_livello_attuale()

    if sfondo_base:
        screen.blit(sfondo_base, (0, 0))
    
    if stato_gioco in ["MENU", "SCELTA"]:
        draw_text_centered("Beyond the screen", pygame.Rect(0, 20, LARGHEZZA, 100), (255, 255, 255), font_titolo)

    if stato_gioco == "MENU":
        for btn, txt, col in [(btn_start, "START", (39, 174, 96)), (btn_settings, "SETTINGS", (127, 140, 141)), (btn_exit, "EXIT", (192, 57, 43))]:
            pygame.draw.rect(screen, col, btn, border_radius=8)
            draw_text_centered(txt, btn, (255, 255, 255))

    elif stato_gioco == "SETTINGS":
        overlay = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA) #Crea un overlay semitrasparente scuro sopra lo sfondo per la schermata impostazioni.
        overlay.fill((5, 25, 55, 230))
        screen.blit(overlay, (0,0))
        draw_text_centered("IMPOSTAZIONI", pygame.Rect(0, 50, LARGHEZZA, 50), (255, 255, 255), font_titolo) #Disegna il titolo “IMPOSTAZIONI” centrato in alto.
        if toggle_schermo: toggle_schermo.disegna(screen)   #Disegna il toggle per la modalità schermo (finestra / fullscreen).
        
        col_res = (192, 57, 43) if facade.esiste_salvataggio() else (80, 80, 80)
        pygame.draw.rect(screen, col_res, btn_reset_data, border_radius=8)
        draw_text_centered("RESET DATI", btn_reset_data, (255, 255, 255))
        pygame.draw.rect(screen, (149, 165, 166), btn_back_menu, border_radius=8)
        draw_text_centered("INDIETRO", btn_back_menu, (255, 255, 255))
        
        debug_txt = f"Res: {LARGHEZZA}x{ALTEZZA} | FPS: {int(clock.get_fps())}"
        screen.blit(font_bottoni.render(debug_txt, True, (150,150,150)), (20, ALTEZZA - 40))

    elif stato_gioco == "SCELTA":
        pygame.draw.rect(screen, (41, 128, 185), btn_nuovo, border_radius=8)
        draw_text_centered("NUOVA PARTITA", btn_nuovo, (255, 255, 255))
        col_car = (41, 128, 185) if facade.esiste_salvataggio() else (50, 50, 50)
        pygame.draw.rect(screen, col_car, btn_carica, border_radius=8)
        draw_text_centered("CARICA PARTITA", btn_carica, (255, 255, 255) if facade.esiste_salvataggio() else (150,150,150))

    elif stato_gioco in ["INTRODUZIONE", "LIVELLO_0"]:
        h_box = 130
        pygame.draw.rect(screen, (0, 0, 0, 180), (20, ALTEZZA - h_box - 20, LARGHEZZA - 40, h_box), border_radius=10)   #Disegna una finestra nera semi-trasparente in basso dove compariranno i testi/dialoghi.
        frasi = intro_frasi[indice_lettura] if stato_gioco == "INTRODUZIONE" else livello0_frasi[indice_lettura]
        for i, riga in enumerate(frasi):
            is_corsivo = riga.startswith("_") and riga.endswith("_")    #Controlla se la riga è in corsivo (se inizia e finisce con "_")
            testo = riga.replace("_", "")   #Rimuove i caratteri "_" per il rendering.
            font = pygame.font.SysFont("Constantia", int(ALTEZZA * 0.035), italic=is_corsivo)   #Crea il font con il corsivo
            testo_surf = font.render(testo, True, (255, 255, 255))
            screen.blit(testo_surf, (40, (ALTEZZA - h_box) + i * 30))

        if input_nome_attivo:   #In pratica: questo blocco serve a far vedere sullo schermo il nome mentre lo scrivi, con il cursore lampeggiante.
            txt_in = font_bottoni.render(f"P{player_corrente} Nome: {nome_inserito}|", True, (255, 255, 0))
            screen.blit(txt_in, (LARGHEZZA // 2 - txt_in.get_width() // 2, ALTEZZA - 55))

    elif stato_gioco == "SCELTA_MORALITA":
        font_piccolo = pygame.font.SysFont("Constantia", 18, bold=True)
        draw_text_centered("Che individuo sei davvero? Un eroe altruista, un mercenario egoista o un'anima indifferente?", pygame.Rect(0, ALTEZZA//4, LARGHEZZA, 50), (255, 255, 255), font_piccolo)

        for btn, txt, col in [(btn_eroe, "EROE", (46, 204, 113)), (btn_mercenario, "MERCENARIO", (231, 76, 60)), (btn_indifferente, "NEUTRALE", (149, 165, 166))]:
            pygame.draw.rect(screen, col, btn, border_radius=8)
            draw_text_centered(txt, btn, (255, 255, 255))

    elif stato_gioco == "MAPPA_MONDI":
        # 1. DISEGNO SFONDO
        screen.blit(sfondi["mondi"][gestore_livelli.indice_corrente], (0, 0))
        
        # 2. OVERLAY E TESTI
        overlay = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160)) 
        screen.blit(overlay, (0, 0))

        # Testo principale
        draw_text_centered("I MONDI SI ALLINEANO", pygame.Rect(0, ALTEZZA // 2 - 50, LARGHEZZA, 50), (255, 255, 255), font_titolo)
        
        # Calcolo del numero livello: indice 0 -> Livello 1, indice 1 -> Livello 2...
        
        num_livello = gestore_livelli.indice_corrente + 1
        
        f_istruzioni = pygame.font.SysFont("Constantia", 22, italic=True)
        
        # MODIFICA QUI: Usiamo f-string per inserire il numero
        testo_dinamico = f"Clicca per iniziare la tua avventura nel Livello {num_livello}"
        
        draw_text_centered(testo_dinamico, 
                           pygame.Rect(0, ALTEZZA // 2 + 30, LARGHEZZA, 30), (200, 200, 200), f_istruzioni)
        
    elif stato_gioco == "GAMEPLAY":
        # --- A. LOGICA DI GIOCO ---
        # CONTROLLO VITE (GAME OVER)
        if manager_gioco.vite_rimanenti <= 0:
            stato_gioco = "GAME_OVER"
            alpha_fade = 255
            colore_transizione = (0, 0, 0) # Fade verso il nero
            fase_transizione = "SVELA_VITTORIA" # Usiamo la stessa logica di schiarita
            continue # Salta il resto del disegno per questo frame

        if not goblin.is_alive() and not mostra_messaggio_livello:
            if gestore_livelli.indice_corrente < 4:
                mostra_messaggio_livello = True
                timer_messaggio = pygame.time.get_ticks()
                testo_passaggio = "BOSS SCONFITTO!"
                fase_transizione = "INIZIO" # Prepariamo il terreno
            else:
                stato_gioco = "VITTORIA"
                alpha_fade = 255     # Partiamo già coperti
                colore_transizione = (255, 255, 255) # Bagliore Bianco
                fase_transizione = "SVELA_VITTORIA"

        # --- Gestione transizione dopo la morte del boss ---
        if mostra_messaggio_livello:
            tempo_trascorso = pygame.time.get_ticks() - timer_messaggio
            
            # Effetto fade out
            if tempo_trascorso > 1500:
                alpha_fade = min(255, alpha_fade + 5) 
            
            # Fine del timer: CAMBIO LIVELLO E SALVATAGGIO
            if tempo_trascorso > 2500: 
                mostra_messaggio_livello = False
                
                # 1. Incrementa l'indice logico e aggiorna il manager
                gestore_livelli.indice_corrente += 1 
                manager_gioco.livello_corrente = gestore_livelli.indice_corrente + 1
                
                # 2. SALVATAGGIO FISICO (Scrive il livello +1 sul JSON)
                facade.auto_saver.update(manager_gioco)
                print(f"PROGRESSO SALVATO: Livello {manager_gioco.livello_corrente}")

                # --- 3. RESET DELLE ENTITA' PER IL NUOVO LIVELLO ---
                # Dobbiamo "materializzare" il nuovo boss e posizionare i player
                nuovo_idx = gestore_livelli.indice_corrente
                
                # Questa funzione ricrea gli sprite per il nuovo indice
                personaggio1, personaggio2, nuovo_boss_visual = aggiorna_posizioni_e_scale(
                    LARGHEZZA, ALTEZZA, nuovo_idx
                )
                
                # Aggiorniamo le variabili globali usate nel loop GAMEPLAY
                goblin_visual = nuovo_boss_visual
                
                # Recuperiamo la classe logica corretta (Anubi, Chica, ecc.) dal BOSS_MAP
                ClasseBoss = BOSS_MAP.get(nuovo_idx)
                if ClasseBoss:
                    # Creiamo la logica del nuovo boss alle coordinate dello sprite
                    goblin = ClasseBoss(x=goblin_visual.pos[0], y=goblin_visual.pos[1])
                
                # Sincronizziamo l'HUD (barre vita) con i nuovi player
                sincronizza_hud()
                # --------------------------------------------------

                stato_gioco = "MAPPA_MONDI"
                fase_transizione = "FINE"
                
        idx = gestore_livelli.indice_corrente
        
        sfondo_attuale = gestore_livelli.get_livello_attuale()
        screen.blit(sfondo_attuale, (0, 0))
            
        screen.blit(sfondo_attuale, (0, 0))

        # --- C. DISEGNO ENTITÀ ---
        if goblin.is_alive() and not mostra_messaggio_livello:
            goblin_visual.pos = goblin.pos
            goblin_visual.disegna(screen, con_ombra=True)

        personaggio1.disegna(screen)
        personaggio2.disegna(screen)

        # --- D. DISEGNO HUD ---
        font_hint = pygame.font.SysFont("Arial", 11, bold=True, italic=True)
        colore_hint = (200, 200, 200)

        # Player 1
        cat_p1 = categorie_disponibili[idx_cat_p1]
        if hud["p1_health"]: 
            hud["p1_health"].disegna(screen)
            # SUGGERIMENTO P1
            txt_hint_p1 = font_hint.render("[TAB] STATS", True, colore_hint)
            screen.blit(txt_hint_p1, (20, 48)) 

        pygame.draw.rect(screen, (60, 60, 60), rect_btn_p1, border_radius=5)
        draw_text_centered("INV", rect_btn_p1, (255, 215, 0), pygame.font.SysFont("Arial", 10, bold=True))
        
        if inv_p1_aperto and hud["p1_inv"]: 
            hud["p1_inv"].disegna(screen, cat_p1)
        
        # Pannello Player 1 (Sinistra)
        if stats_p1_aperte and len(manager_gioco.giocatori) > 0:
            disegna_pannello_stats(screen, manager_gioco.giocatori[0], 20, 100)

        # Player 2
        cat_p2 = categorie_disponibili[idx_cat_p2]
        if hud["p2_health"]: 
            hud["p2_health"].rect.x = LARGHEZZA - 220 
            hud["p2_health"].disegna(screen)
            # SUGGERIMENTO P2
            txt_hint_p2 = font_hint.render("[ \ ] STATS", True, colore_hint)
            screen.blit(txt_hint_p2, (LARGHEZZA - txt_hint_p2.get_width() - 20, 48))

        pygame.draw.rect(screen, (60, 60, 60), rect_btn_p2, border_radius=5)
        draw_text_centered("INV", rect_btn_p2, (255, 215, 0), pygame.font.SysFont("Arial", 10, bold=True))
        
        if inv_p2_aperto and hud["p2_inv"]:
            hud["p2_inv"].x = LARGHEZZA - 265
            hud["p2_inv"].disegna(screen, cat_p2)
            
        if stats_p2_aperte and len(manager_gioco.giocatori) > 1:
            # Allineato a destra, stessa altezza del P1
            disegna_pannello_stats(screen, manager_gioco.giocatori[1], LARGHEZZA - 170, 100)
        # --- E. OVERLAY LIVELLO (Boss Sconfitto) ---
        if mostra_messaggio_livello:
            # Scurisce leggermente lo sfondo per far risaltare il testo
            overlay = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))

            box_msg = pygame.Surface((LARGHEZZA, 120), pygame.SRCALPHA)
            box_msg.fill((0, 0, 0, 200)) 
            screen.blit(box_msg, (0, ALTEZZA // 2 - 60))
            
            # Testo dorato con font Constantia come richiesto
            font_vittoria = pygame.font.SysFont("Constantia", 50, bold=True)
            draw_text_centered(testo_passaggio, pygame.Rect(0, ALTEZZA // 2 - 60, LARGHEZZA, 120), (255, 215, 0), font_vittoria)

    elif stato_gioco == "VITTORIA":
        screen.fill((10, 10, 20)) 
        
        # Testi con ombra
        font_titolo = pygame.font.SysFont("Constantia", 60, bold=True)
        draw_text_centered("IL MALE È STATO ABBATTUTO", pygame.Rect(2, ALTEZZA // 2 - 78, LARGHEZZA, 60), (50, 50, 50), font_titolo)
        draw_text_centered("IL MALE È STATO ABBATTUTO", pygame.Rect(0, ALTEZZA // 2 - 80, LARGHEZZA, 60), (255, 255, 255), font_titolo)
        draw_text_centered("FINALMENTE SEI LIBERO!", pygame.Rect(0, ALTEZZA // 2, LARGHEZZA, 50), (0, 255, 150), font_titolo)
        draw_text_centered("Premi ESC per tornare al menu", 
                           pygame.Rect(0, ALTEZZA - 100, LARGHEZZA, 30), 
                           (100, 100, 100), font_sub)
    # --- DISEGNO DEL FADE GLOBALE ---
    if alpha_fade > 0:
        fade_surf = pygame.Surface((LARGHEZZA, ALTEZZA))
        fade_surf.fill(colore_transizione) 
        fade_surf.set_alpha(alpha_fade)
        screen.blit(fade_surf, (0, 0))
        
        # Gestiamo qui tutte le uscite dai fade
        if fase_transizione == "FINE":
            alpha_fade -= 5
        elif fase_transizione == "SVELA_VITTORIA":
            alpha_fade -= 2 # Più lento per la vittoria
            
        if alpha_fade <= 0:
            alpha_fade = 0
            fase_transizione = None
    #game over
    elif stato_gioco == "GAME_OVER":
        screen.fill((20, 0, 0)) # Sfondo rosso scuro/nero
        
        font_main = pygame.font.SysFont("Constantia", 70, bold=True)
        font_sub = pygame.font.SysFont("Constantia", 30, italic=True)
        
        # Testo principale "GAME OVER"
        draw_text_centered("HAI FALLITO LA MISSIONE", 
                           pygame.Rect(0, ALTEZZA // 2 - 60, LARGHEZZA, 70), 
                           (200, 0, 0), font_main)
        
        draw_text_centered("Premi ESC per tornare al menu", 
                           pygame.Rect(0, ALTEZZA - 100, LARGHEZZA, 30), 
                           (100, 100, 100), font_sub)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()