import pygame
import sys
from LogicaGioco import *
from livelli import GestoreLivelli

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

# Carichiamo i "Master" una volta sola
masters = {
    "menu":   carica_asset('sfondo.png', (40, 40, 40)),
    "stanza": carica_asset('stanza.jpeg', (60, 60, 100)),
    "l0":     carica_asset('sfondo_livello0.jpeg', (20, 20, 20)),
    "mondi":  carica_asset('livello_1.jpeg', (0, 50, 0))
}

# Dizionario per le versioni scalate (si aggiorna col ridimensionamento)
sfondi = {}
font_bottoni = pygame.font.SysFont("Constantia", 25, bold=True)
font_titolo = None

# --- 3. RECT DEI BOTTONI (Globali) ---
larghezza_btn, altezza_btn = 200, 45
btn_start = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_settings = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_exit = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_nuovo = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_carica = pygame.Rect(0, 0, larghezza_btn, altezza_btn)
btn_eroe = pygame.Rect(0, 0, 180, 50)
btn_mercenario = pygame.Rect(0, 0, 180, 50)
btn_indifferente = pygame.Rect(0, 0, 180, 50)

def aggiorna_posizioni_e_scale(w, h):
    """Ricalcola tutte le posizioni e riscala le immagini al ridimensionamento."""
    global sfondi, font_titolo
    # Riscala Sfondi
    for chiave, img in masters.items():
        sfondi[chiave] = pygame.transform.scale(img, (w, h))
    
    # Font dinamico per il titolo
    font_titolo = pygame.font.SysFont("Constantia", int(w * 0.07), bold=True)
    
    # Centratura Menu
    x_c = (w - larghezza_btn) // 2
    btn_start.topleft = (x_c, h - 250)
    btn_settings.topleft = (x_c, h - 185)
    btn_exit.topleft = (x_c, h - 120)
    btn_nuovo.topleft = (x_c, h - 220)
    btn_carica.topleft = (x_c, h - 155)
    
    # Bottoni Moralità
    centro_x = w // 2
    btn_eroe.topleft = (centro_x - 290, h // 2)
    btn_mercenario.topleft = (centro_x - 90, h // 2)
    btn_indifferente.topleft = (centro_x + 110, h // 2)

# Prima inizializzazione del layout
aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

# --- 4. LOGICA DI GIOCO ---
stato_gioco = "MENU"
player_corrente = 1
nome_inserito = ""
input_nome_attivo = False
indice_lettura = 0

manager_gioco = GameManager.get_instance()
facade = GameFacade(manager_gioco, AutoSaveObserver())
gestore_livelli = GestoreLivelli(LARGHEZZA, ALTEZZA)

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
        if event.type == pygame.QUIT: #esce dalla finestra
            running = False

        if event.type == pygame.VIDEORESIZE: #per ingrandire la fijnestra
            LARGHEZZA, ALTEZZA = event.w, event.h
            screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
            aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)
            gestore_livelli.ridimensiona_tutto(LARGHEZZA, ALTEZZA)

        #costruire casella di testo riga per riga
        if event.type == pygame.KEYDOWN and input_nome_attivo: #se è stato premuto un tasto fisico nella tastiera e se input nome attivo è true si usa la tastiera
            if event.key == pygame.K_RETURN and len(nome_inserito) > 1: #almeno 2 lettere  e invio
                input_nome_attivo = False #non si può scrivere più
                stato_gioco = "SCELTA_MORALITA"
            elif event.key == pygame.K_BACKSPACE: #tasto per l'ultima lettera
                nome_inserito = nome_inserito[:-1] #si esclude l'ultimo carattere
            else:
                if len(nome_inserito) < 12: nome_inserito += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if stato_gioco == "MENU":
                if btn_start.collidepoint(pos_mouse): stato_gioco = "SCELTA"
                elif btn_exit.collidepoint(pos_mouse): running = False
            
            elif stato_gioco == "SCELTA":
                if btn_nuovo.collidepoint(pos_mouse):
                    stato_gioco, indice_lettura = "INTRODUZIONE", 0
                elif btn_carica.collidepoint(pos_mouse):
                    if facade.carica_da_disco() and facade.carica_ultimo_salvataggio():
                        # 1. Recupera l'indice del livello salvato dal manager
                        indice_salvato = manager_gioco.livello_corrente -1 # Corretto
                        
                        # 2. Sincronizza il gestore livelli
                        gestore_livelli.indice_corrente = indice_salvato
                        
                        # 3. Imposta lo stato su GAMEPLAY per saltare menu e intro
                        stato_gioco = "GAMEPLAY" 
                    else:
                        print("Errore nel caricamento o nessun salvataggio trovato")

            elif stato_gioco == "INTRODUZIONE":
                indice_lettura += 1
                if indice_lettura >= len(intro_frasi):
                    stato_gioco, indice_lettura = "LIVELLO_0", 0
            
            #si scrivono i nomi
            elif stato_gioco == "LIVELLO_0":
                if indice_lettura == len(livello0_frasi) - 1:
                    input_nome_attivo = True
                else:
                    indice_lettura += 1
            
            #pattern facade/factory, crra l'oggetto del giocatore con nome e classe

            elif stato_gioco == "SCELTA_MORALITA":
                scelta = None
                if btn_eroe.collidepoint(pos_mouse): scelta = "eroe altruista"
                elif btn_mercenario.collidepoint(pos_mouse): scelta = "mercenario egoista"
                elif btn_indifferente.collidepoint(pos_mouse): scelta = "anima indifferente"
                
                if scelta:
                    creator = Player1Creator() if player_corrente == 1 else Player2Creator()
                    facade.crea_personaggio_completo(creator, player_corrente, nome_inserito, scelta)
                    if player_corrente == 1: #se ho creato il primo giocatore torno al livello 0 per il secondo
                        player_corrente, nome_inserito, stato_gioco, input_nome_attivo = 2, "", "LIVELLO_0", True
                    else:
                        stato_gioco = "MAPPA_MONDI"

            elif stato_gioco == "MAPPA_MONDI":
                stato_gioco = "GAMEPLAY"
                gestore_livelli.indice_corrente = 0

    # --- 6. DISEGNO ---
    # Gestione Sfondi per stato
    sfondo_da_disegnare = None
    if stato_gioco in ["MENU", "SCELTA"]: sfondo_da_disegnare = sfondi["menu"]
    elif stato_gioco == "INTRODUZIONE": sfondo_da_disegnare = sfondi["stanza"]
    elif stato_gioco in ["LIVELLO_0", "SCELTA_MORALITA"]: sfondo_da_disegnare = sfondi["l0"]
    elif stato_gioco == "MAPPA_MONDI": sfondo_da_disegnare = sfondi["mondi"]
    elif stato_gioco == "GAMEPLAY": 
        sfondo_da_disegnare = gestore_livelli.get_livello_attuale()

    #screen blit icolla l'immagine sulla finestra
    if sfondo_da_disegnare: screen.blit(sfondo_da_disegnare, (0, 0))
    
    # UI: Titolo
    if stato_gioco in ["MENU", "SCELTA"]:
        draw_text_centered("Beyond the screen", pygame.Rect(0, 20, LARGHEZZA, 100), (255, 255, 255), font_titolo)

    # UI: Bottoni Menu
    if stato_gioco == "MENU":
        
        for btn, txt, col in [(btn_start, "START", (39, 174, 96)), (btn_settings, "SETTINGS", (127, 140, 141)), (btn_exit, "EXIT", (192, 57, 43))]:
            pygame.draw.rect(screen, col, btn, border_radius=8)
            draw_text_centered(txt, btn, (255, 255, 255))

    elif stato_gioco == "SCELTA":
        pygame.draw.rect(screen, (41, 128, 185), btn_nuovo, border_radius=8)
        draw_text_centered("NUOVA PARTITA", btn_nuovo, (255, 255, 255))
        
        col_carica = (41, 128, 185) if facade.esiste_salvataggio() else (50, 50, 50)
        pygame.draw.rect(screen, col_carica, btn_carica, border_radius=8)
        draw_text_centered("CARICA PARTITA", btn_carica, (255, 255, 255) if facade.esiste_salvataggio() else (150,150,150))

    # UI: Introduzione e Dialoghi
    #ogni elemento può contenere più righe, sono distanziate di 30 pixel
    elif stato_gioco in ["INTRODUZIONE", "LIVELLO_0"]:
        h_box = 130
        pygame.draw.rect(screen, (0, 0, 0, 180), (20, ALTEZZA - h_box - 20, LARGHEZZA - 40, h_box), border_radius=10)
        frasi = intro_frasi[indice_lettura] if stato_gioco == "INTRODUZIONE" else livello0_frasi[indice_lettura]
        for i, riga in enumerate(frasi):
            testo_surf = pygame.font.SysFont("Constantia", int(ALTEZZA * 0.035)).render(riga.replace("_", ""), True, (255, 255, 255))
            screen.blit(testo_surf, (40, (ALTEZZA - h_box) + i * 30))
        #cursore di testo
        if input_nome_attivo:
            txt_in = font_bottoni.render(f"P{player_corrente} Nome: {nome_inserito}|", True, (255, 255, 0))
            screen.blit(txt_in, (LARGHEZZA // 2 - txt_in.get_width() // 2, ALTEZZA - 55))

    # UI: Moralità
    elif stato_gioco == "SCELTA_MORALITA":
        draw_text_centered(f"{nome_inserito}, che individuo sei davvero?", pygame.Rect(0, ALTEZZA//4, LARGHEZZA, 50), (255,255,255), font_bottoni)
        for btn, txt, col in [(btn_eroe, "EROE", (46, 204, 113)), (btn_mercenario, "MERCENARIO", (231, 76, 60)), (btn_indifferente, "NEUTRALE", (149, 165, 166))]:
            pygame.draw.rect(screen, col, btn, border_radius=8)
            draw_text_centered(txt, btn, (255, 255, 255))

    elif stato_gioco == "MAPPA_MONDI":
    # Creiamo un rettangolo che parte dall'80% o 90% dell'altezza dello schermo
    # In questo modo la scritta apparirà quasi sul fondo.
        area_molto_bassa = pygame.Rect(0, ALTEZZA * 0.85, LARGHEZZA, ALTEZZA * 0.1)
    
        draw_text_centered("I mondi si allineano. Clicca per iniziare.", area_molto_bassa, (255, 255, 255))


    pygame.display.flip() #prima di questo comando tutto ciò è in una memoria nascosta
    clock.tick(60) #60 fotogrammi al secondo

pygame.quit()
sys.exit()