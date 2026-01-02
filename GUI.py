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
        self.x = x             # Posizione orizzontale di partenza dell'HUD
        self.y = y             # Posizione verticale
        self.player = player   # Riferimento al giocatore proprietario
        self.slot_size = 50    # Dimensione di ogni quadratino
        self.padding = 10      # Spazio tra un quadratino e l'altro
        self.font = pygame.font.SysFont("Arial", 12, bold=True)
    def disegna(self, surface):
        # Chiediamo l'iteratore all'inventario del giocatore
        it = iter(self.player._inventario)
        current_x = self.x
        
        while True:
            try:
                # Chiediamo il prossimo oggetto
                item = next(it) 
                
                # Disegniamo il quadratino dello slot
                rect_slot = pygame.Rect(current_x, self.y, self.slot_size, self.slot_size)
                pygame.draw.rect(surface, (60, 60, 60), rect_slot, border_radius=5)
                pygame.draw.rect(surface, (200, 200, 200), rect_slot, width=2, border_radius=5)
                
                # Disegniamo il nome dell'oggetto (le prime 3 lettere)
                txt_surf = self.font.render(item.nome[:3].upper(), True, (255, 255, 255))
                surface.blit(txt_surf, (rect_slot.centerx - txt_surf.get_width()//2, 
                                        rect_slot.centery - txt_surf.get_height()//2))
                
                # Spostiamo la X per il prossimo slot
                current_x += self.slot_size + self.padding
                
            except StopIteration:
                # Quando l'iteratore finisce gli oggetti, usciamo dal ciclo
                break
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
    "mondi":  carica_asset('livello_1.jpeg', (0, 50, 0)),
    "livello1": carica_asset('livello1_gameplay.jpeg', (30, 30, 30))

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
    ["_Inserite i vostri nomi_"]
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

        if event.type == pygame.VIDEORESIZE: #se la finestra viene ridimensionata:
            LARGHEZZA, ALTEZZA = event.w, event.h
            if not (screen.get_flags() & pygame.FULLSCREEN):
                screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
            gestore_livelli.ridimensiona_tutto(LARGHEZZA, ALTEZZA)
            aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

        if event.type == pygame.KEYDOWN:    #Controlla se un tasto della tastiera è stato premuto.
            if input_nome_attivo: #se il gioco è nella modalità in cui il giocatore sta inserendo il nome
                if event.key == pygame.K_RETURN and len(nome_inserito) > 1: 
                    input_nome_attivo = False 
                    stato_gioco = "SCELTA_MORALITA"
                elif event.key == pygame.K_BACKSPACE: #se clicchi indietro cancella l'ultimo carattere scritto
                    nome_inserito = nome_inserito[:-1] 
                else: 
                    if len(nome_inserito) < 12: nome_inserito += event.unicode #nome inserito = quello che hai digitato

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

            elif stato_gioco == "SCELTA":   #se siamo nel menu di scelta
                if btn_nuovo.collidepoint(pos_mouse): 
                    stato_gioco, indice_lettura = "INTRODUZIONE", 0
                elif btn_carica.collidepoint(pos_mouse):
                    if facade.carica_da_disco():
                        indice_salvato = manager_gioco.livello_corrente - 1
                        gestore_livelli.indice_corrente = indice_salvato
                        stato_gioco = "GAMEPLAY"
                        sincronizza_hud()
                        # Inizializziamo l'HUD usando il DIZIONARIO hud
                        if len(manager_gioco.giocatori) > 0:
                            p1 = manager_gioco.giocatori[0]
                            hud["p1_health"] = HealthBar(20, 20, 200, 25, p1)
                            hud["p1_inv"] = InventoryUI(20, 55, p1)
                            
                        if len(manager_gioco.giocatori) > 1:
                            p2 = manager_gioco.giocatori[1]
                            hud["p2_health"] = HealthBar(LARGHEZZA - 220, 20, 200, 25, p2)
                            hud["p2_inv"] = InventoryUI(LARGHEZZA - 220, 55, p2)
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
                    
                    # 1. CREA IL PERSONAGGIO
                    nome = valida_nome(nome_inserito, player_corrente)
                    p = creator.create_character(nome, 0)
                    
                    # 2. AGGIUNGI L'ITEM SUBITO (Prima di salvarlo!)
                    p._inventario.add_item(Item("Spada", "Attacco", 20))
                    
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

            elif stato_gioco == "MAPPA_MONDI":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Entriamo nel gioco
                    stato_gioco = "GAMEPLAY"
                    gestore_livelli.indice_corrente = 0
                    sincronizza_hud()

                    # Inizializziamo l'HUD prendendo i dati REALI dal manager (sia da Carica che da Nuovo)
                    if len(manager_gioco.giocatori) > 0:
                        p1 = manager_gioco.giocatori[0]
                        hud["p1_health"] = HealthBar(20, 20, 200, 25, p1)
                        hud["p1_inv"] = InventoryUI(20, 55, p1)
                        
                    if len(manager_gioco.giocatori) > 1:
                        p2 = manager_gioco.giocatori[1]
                        hud["p2_health"] = HealthBar(LARGHEZZA - 220, 20, 200, 25, p2)
                        hud["p2_inv"] = InventoryUI(LARGHEZZA - 220, 55, p2)

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
        draw_text_centered("I mondi si allineano. Clicca per iniziare.", pygame.Rect(0, ALTEZZA * 0.85, LARGHEZZA, ALTEZZA * 0.1), (255, 255, 255))


    elif stato_gioco == "GAMEPLAY":

    # Sfondo diverso SOLO per il livello 1
        if gestore_livelli.indice_corrente == 0:
            sfondo_gioco = sfondi["livello1"]
        else:
            sfondo_gioco = gestore_livelli.get_livello_attuale()

        screen.blit(sfondo_gioco, (0, 0))

        # Barra vita SOLO nel livello 1
        if gestore_livelli.indice_corrente == 0:
            if hud["p1_health"]: hud["p1_health"].disegna(screen)
            if hud["p1_inv"]:    hud["p1_inv"].disegna(screen)
            
            if hud["p2_health"]: hud["p2_health"].disegna(screen)
            if hud["p2_inv"]:    hud["p2_inv"].disegna(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()