import pygame
import sys
import os
from LogicaGioco import *
from livelli import GestoreLivelli

# --- 0. CLASSI UTILITY (UI) ---

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

class HealthBar(Observer):
    """
    Observer che visualizza la barra della vita (HUD).
    Simile all'immagine: Barra verde su sfondo scuro, con testo numerico.
    """
    def __init__(self, x, y, w, h, player):
        self.rect = pygame.Rect(x, y, w, h)
        self.player = player
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.player.attach(self) # Si registra come osservatore del player

    def update(self, subject: Subject) -> None:
        pass 

    def disegna(self, surface):
        # Sfondo Barra
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        pygame.draw.rect(surface, (100, 0, 0), self.rect, width=2) # Bordo rosso scuro

        # Barra Verde
        if self.player.max_hp > 0:
            ratio = self.player.hp / self.player.max_hp
        else:
            ratio = 0
        
        # Evitiamo valori negativi per la larghezza
        if ratio < 0: ratio = 0
        
        current_width = self.rect.width * ratio
        rect_hp = pygame.Rect(self.rect.x, self.rect.y, int(current_width), self.rect.height)
        pygame.draw.rect(surface, (0, 180, 0), rect_hp) 
        
        # Testo
        txt = f"{self.player.hp} / {self.player.max_hp}"
        txt_surf = self.font.render(txt, True, (255, 255, 255))
        surface.blit(txt_surf, (self.rect.centerx - txt_surf.get_width()//2, self.rect.centery - txt_surf.get_height()//2))

# --- 1. INIZIALIZZAZIONE ---
pygame.init()
LARGHEZZA, ALTEZZA = 800, 600
screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
pygame.display.set_caption("Beyond the Screen")
clock = pygame.time.Clock()

# --- 2. ASSET E RISORSE ---
def carica_asset(path, colore_fallback):
    try:
        return pygame.image.load(path).convert()
    except:
        surf = pygame.Surface((800, 600))
        surf.fill(colore_fallback)
        return surf

masters = {
    "menu":   carica_asset('sfondo.png', (40, 40, 40)),
    "stanza": carica_asset('stanza.jpeg', (60, 60, 100)),
    "l0":     carica_asset('sfondo_livello0.jpeg', (20, 20, 20)),
    "mondi":  carica_asset('livello_1.jpeg', (0, 50, 0))
}
sfondi = {}
font_bottoni = pygame.font.SysFont("Constantia", 25, bold=True)
font_titolo = None

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

# Impostazioni
btn_reset_data = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_back_menu  = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
toggle_schermo = None 

# HUD (Barra Vita)
health_bar_ui = None 

def aggiorna_posizioni_e_scale(w, h):
    global sfondi, font_titolo, toggle_schermo
    for chiave, img in masters.items():
        sfondi[chiave] = pygame.transform.scale(img, (w, h))
    
    font_titolo = pygame.font.SysFont("Constantia", int(w * 0.07), bold=True)
    
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

    # Settings
    btn_reset_data.topleft = (x_c, h // 2 + 10)
    btn_back_menu.topleft  = (x_c, h // 2 + 80)
    w_sel, h_sel = 600, 50
    rect_schermo = pygame.Rect((w - w_sel) // 2, h // 2 - 60, w_sel, h_sel)

    def on_change_schermo(valore):
        if valore == "FULLSCREEN": pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.FULLSCREEN)
        else: pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
        gestore_livelli.ridimensiona_tutto(LARGHEZZA, ALTEZZA)

    opzioni_video = ["FINESTRA", "FULLSCREEN"]
    idx = 1 if (screen.get_flags() & pygame.FULLSCREEN) else 0
    toggle_schermo = ToggleSelector(rect_schermo, "MODALITA' SCHERMO", opzioni_video, idx, on_change_schermo)

aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

# --- 4. LOGICA GIOCO ---
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
    ["All’improvviso, nel buio… una scritta appare!"],
    [
        "_Benvenuti nella vostra nuova avventura!_",
        "_D'ora in poi collaborerete per vincere._",
        "_Se non lo farete, rimarrete qui per sempre._"
    ],
    ["Inserite i vostri nomi"]
]

def draw_text_centered(testo, rettangolo, colore, font=font_bottoni):
    superficie = font.render(testo, True, colore)
    screen.blit(superficie, superficie.get_rect(center=rettangolo.center))

# --- 5. LOOP PRINCIPALE ---
running = True
while running:
    pos_mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            running = False

        if event.type == pygame.VIDEORESIZE: 
            LARGHEZZA, ALTEZZA = event.w, event.h
            if not (screen.get_flags() & pygame.FULLSCREEN):
                screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
            gestore_livelli.ridimensiona_tutto(LARGHEZZA, ALTEZZA)
            aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

        # DEBUG: Tasto K per farsi male (Test Barra Vita)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k and stato_gioco == "GAMEPLAY":
                if manager_gioco.giocatori:
                    manager_gioco.giocatori[0].take_damage(10)
                    print(f"Ouch! HP: {manager_gioco.giocatori[0].hp}")

            if input_nome_attivo: 
                if event.key == pygame.K_RETURN and len(nome_inserito) > 1: 
                    input_nome_attivo = False 
                    stato_gioco = "SCELTA_MORALITA"
                elif event.key == pygame.K_BACKSPACE: 
                    nome_inserito = nome_inserito[:-1] 
                else: 
                    if len(nome_inserito) < 12: nome_inserito += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if stato_gioco == "MENU":
                if btn_start.collidepoint(pos_mouse): stato_gioco = "SCELTA"
                elif btn_settings.collidepoint(pos_mouse): stato_gioco = "SETTINGS"
                elif btn_exit.collidepoint(pos_mouse): running = False
            
            elif stato_gioco == "SETTINGS":
                if toggle_schermo.gestisci_click(pos_mouse): 
                    pass
                elif btn_reset_data.collidepoint(pos_mouse):
                    if os.path.exists("salvataggio_gioco.json"): 
                        os.remove("salvataggio_gioco.json")
                    manager_gioco.resetGameData()
                    if facade.auto_saver: facade.auto_saver.history = []
                    print("Log: Reset eseguito.")
                elif btn_back_menu.collidepoint(pos_mouse): 
                    stato_gioco = "MENU"

            elif stato_gioco == "SCELTA":
                if btn_nuovo.collidepoint(pos_mouse): 
                    stato_gioco, indice_lettura = "INTRODUZIONE", 0
                elif btn_carica.collidepoint(pos_mouse):
                    if facade.carica_da_disco() and facade.carica_ultimo_salvataggio():
                        indice_salvato = manager_gioco.livello_corrente - 1
                        gestore_livelli.indice_corrente = indice_salvato
                        stato_gioco = "GAMEPLAY"
                        # Creiamo la Health Bar per il primo giocatore caricato
                        if manager_gioco.giocatori:
                            health_bar_ui = HealthBar(20, 20, 200, 25, manager_gioco.giocatori[0])
                    else: 
                        print("Errore nel caricamento o nessun salvataggio trovato")

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
                    p = facade.crea_personaggio_completo(creator, player_corrente, nome_inserito, scelta)
                    
                    if player_corrente == 1:
                        # Assegniamo la barra della vita al Player 1 appena creato
                        health_bar_ui = HealthBar(20, 20, 200, 25, p)
                        player_corrente, nome_inserito, stato_gioco, input_nome_attivo = 2, "", "LIVELLO_0", True
                    else:
                        stato_gioco = "MAPPA_MONDI"

            elif stato_gioco == "MAPPA_MONDI":
                stato_gioco = "GAMEPLAY"
                gestore_livelli.indice_corrente = 0

    # --- 6. DISEGNO ---
    sfondo = None
    if stato_gioco in ["MENU", "SCELTA", "SETTINGS"]: sfondo = sfondi["menu"]
    elif stato_gioco == "INTRODUZIONE": sfondo = sfondi["stanza"]
    elif stato_gioco in ["LIVELLO_0", "SCELTA_MORALITA"]: sfondo = sfondi["l0"]
    elif stato_gioco == "MAPPA_MONDI": sfondo = sfondi["mondi"]
    elif stato_gioco == "GAMEPLAY": sfondo = gestore_livelli.get_livello_attuale()

    if sfondo: screen.blit(sfondo, (0, 0))
    
    if stato_gioco in ["MENU", "SCELTA"]:
        draw_text_centered("Beyond the screen", pygame.Rect(0, 20, LARGHEZZA, 100), (255, 255, 255), font_titolo)

    if stato_gioco == "MENU":
        for btn, txt, col in [(btn_start, "START", (39, 174, 96)), (btn_settings, "SETTINGS", (127, 140, 141)), (btn_exit, "EXIT", (192, 57, 43))]:
            pygame.draw.rect(screen, col, btn, border_radius=8)
            draw_text_centered(txt, btn, (255, 255, 255))

    elif stato_gioco == "SETTINGS":
        overlay = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
        overlay.fill((5, 25, 55, 230))
        screen.blit(overlay, (0,0))
        draw_text_centered("IMPOSTAZIONI", pygame.Rect(0, 50, LARGHEZZA, 50), (255, 255, 255), font_titolo)
        if toggle_schermo: toggle_schermo.disegna(screen)
        
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
        pygame.draw.rect(screen, (0, 0, 0, 180), (20, ALTEZZA - h_box - 20, LARGHEZZA - 40, h_box), border_radius=10)
        frasi = intro_frasi[indice_lettura] if stato_gioco == "INTRODUZIONE" else livello0_frasi[indice_lettura]
        for i, riga in enumerate(frasi):
            testo_surf = pygame.font.SysFont("Constantia", int(ALTEZZA * 0.035)).render(riga.replace("_", ""), True, (255, 255, 255))
            screen.blit(testo_surf, (40, (ALTEZZA - h_box) + i * 30))
        if input_nome_attivo:
            txt_in = font_bottoni.render(f"P{player_corrente} Nome: {nome_inserito}|", True, (255, 255, 0))
            screen.blit(txt_in, (LARGHEZZA // 2 - txt_in.get_width() // 2, ALTEZZA - 55))

    elif stato_gioco == "SCELTA_MORALITA":
        draw_text_centered(f"{nome_inserito}, che individuo sei davvero?", pygame.Rect(0, ALTEZZA//4, LARGHEZZA, 50), (255,255,255), font_bottoni)
        for btn, txt, col in [(btn_eroe, "EROE", (46, 204, 113)), (btn_mercenario, "MERCENARIO", (231, 76, 60)), (btn_indifferente, "NEUTRALE", (149, 165, 166))]:
            pygame.draw.rect(screen, col, btn, border_radius=8)
            draw_text_centered(txt, btn, (255, 255, 255))

    elif stato_gioco == "MAPPA_MONDI":
        draw_text_centered("I mondi si allineano. Clicca per iniziare.", pygame.Rect(0, ALTEZZA * 0.85, LARGHEZZA, ALTEZZA * 0.1), (255, 255, 255))

    elif stato_gioco == "GAMEPLAY":
        # Disegna la Health Bar se esiste
        if health_bar_ui:
            health_bar_ui.disegna(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()