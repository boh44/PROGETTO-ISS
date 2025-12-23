import pygame
import sys

# 1. Inizializzazione
pygame.init()
screen = pygame.display.set_mode((800, 600))    #finestra di gioco
pygame.display.set_caption("Menu di Gioco")
clock = pygame.time.Clock()

# --- STATO DEL GIOCO ---
# "MENU" = schermata principale, "SCELTA" = nuova partita o carica, "INTRODUZIONE", LIVELLO_N
stato_gioco = "MENU"

# --- FONT BOTTONI---
font_bottoni = pygame.font.SysFont("Constantia", 25, bold=True)

# --- IMMAGINE DI SFONDO ---
try:
    sfondo = pygame.image.load('sfondo.jpeg').convert()
    sfondo = pygame.transform.scale(sfondo, (800, 600))
except:
    sfondo = pygame.Surface((800, 600)) #alrimenti grigia
    sfondo.fill((40, 40, 40))

# --- DEFINIZIONE PULSANTI ---
larghezza_btn = 200 # Leggermente più largo per far stare il testo lungo
altezza_btn = 45
x_centrata = (800 - larghezza_btn) // 2 

# Pulsanti Menu
btn_start = pygame.Rect(x_centrata, 350, larghezza_btn, altezza_btn)
btn_settings = pygame.Rect(x_centrata, 415, larghezza_btn, altezza_btn)
btn_exit = pygame.Rect(x_centrata, 480, larghezza_btn, altezza_btn)

# Pulsanti Sotto-menu (Scelta salvataggio)
btn_nuovo = pygame.Rect(x_centrata, 380, larghezza_btn, altezza_btn)
btn_carica = pygame.Rect(x_centrata, 445, larghezza_btn, altezza_btn)

# --- DIALOGHI ---
intro_frasi = [
    ["Ti svegli, confuso…", "Che strano sogno! Meglio alzarsi"], 
    ["C'era una cosa chr volevi fare, ma cosa?"],
    ["Ah, certo! Provare il nuovo gioco!"],
    ["Lo prendi in mano e… starnutisci!", "È impolverato, meglio pulirlo prima."],
    ["Prendi un panno, lo pulisci e lo inserisci nel lettore…", "L’oscurità ti avvolge…"]
]

livello0_frasi = [
    [],
    ["Apri gli occhi… tutto è nero.", "Un senso di disagio ti avvolge."], 
    ["Davanti a te, un ragazzo come te… ma dove siete?"],
    ["Ti avvicini, provi a parlargli… nulla.", "Sembra perso quanto te."],
    ["All’improvviso, nel buio… una scritta appare!"],
    ["_Benvenuti nella vostra nuova avventura. D\'ora in poi collaborerete per vincere_", "_Se non lo farete rimarrete qui per sempre_"],
    ["Inserite i vostri nomi"]
]


indice_lettura = 0

def scrivi_testo(testo, rettangolo_bottone, colore_testo):  #scrivere una stringa centrata dentro un rettangolo
    superficie_testo = font_bottoni.render(testo, True, colore_testo)   #immagine con destro scritta che poi mette nel bottone
    pos_testo = superficie_testo.get_rect(center=rettangolo_bottone.center) #get_rect() crea un rettangolo della stessa dimensione del testo
                                                                            #Metti il centro del testo uguale al centro del bottone
    screen.blit(superficie_testo, pos_testo)    #“Copia superficie_testo su screen nella posizione pos_testo”




#RUNNING GAME
running = True
while running:
    pos_mouse = pygame.mouse.get_pos()  #Ottieni (x, y) del mouse in tempo reale

    for event in pygame.event.get():    #scorre tutti gli eventi
        if event.type == pygame.QUIT:   #se clicchi su X chiudi
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:   # click sinistro
               
                # MENU
                if stato_gioco == "MENU": 
                    if btn_start.collidepoint(pos_mouse):
                        stato_gioco = "SCELTA"
                    if btn_settings.collidepoint(pos_mouse):
                        print("SETTINGS")
                    if btn_exit.collidepoint(pos_mouse):
                        running = False
                
                # SCELTA
                elif stato_gioco == "SCELTA":
                    if btn_nuovo.collidepoint(pos_mouse):
                        stato_gioco = "INTRODUZIONE"
                        indice_lettura = 0  # reset indice
                    if btn_carica.collidepoint(pos_mouse):
                        print("Caricamento dati...")

                # INTRODUZIONE
                elif stato_gioco == "INTRODUZIONE":
                    indice_lettura += 1
                    if indice_lettura >= len(intro_frasi):
                        stato_gioco = "LIVELLO_0"
                        indice_lettura = 0  # reset per livello0

                # LIVELLO 0
                elif stato_gioco == "LIVELLO_0":
                    indice_lettura += 1
                    if indice_lettura >= len(livello0_frasi):
                        stato_gioco = "LIVELLO_1"
                        indice_lettura = 0  # reset per livello1


    # ---- DISEGNO SFONDO ----
    screen.blit(sfondo, (0, 0))  

    # ---- TITOLO ----
    f_label = pygame.font.SysFont("Constantia", 60, True)
    testo = "Beyond the screen"
    x_titolo = 400 - f_label.size(testo)[0] // 2
    y_titolo = 10
    screen.blit(f_label.render(testo, True, (50,50,50)), (x_titolo+2, y_titolo+2))
    screen.blit(f_label.render(testo, True, (150,150,150)), (x_titolo+1, y_titolo+1))
    screen.blit(f_label.render(testo, True, (255,255,255)), (x_titolo, y_titolo))


    # ---- LOGICA MENU ----
    if stato_gioco == "MENU":
        h_s = btn_start.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (46,204,113) if h_s else (39,174,96), btn_start, border_radius=8)
        scrivi_testo("START", btn_start, (255,255,255))
        h_st = btn_settings.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (149,165,166) if h_st else (127,140,141), btn_settings, border_radius=8)
        scrivi_testo("SETTINGS", btn_settings, (255,255,255))
        h_e = btn_exit.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (231,76,60) if h_e else (192,57,43), btn_exit, border_radius=8)
        scrivi_testo("EXIT", btn_exit, (255,255,255))

    # ---- LOGICA SCELTA ----
    elif stato_gioco == "SCELTA":
        h_n = btn_nuovo.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (52,152,219) if h_n else (41,128,185), btn_nuovo, border_radius=8)
        scrivi_testo("NUOVA PARTITA", btn_nuovo, (255,255,255))
        h_c = btn_carica.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (52,152,219) if h_c else (41,128,185), btn_carica, border_radius=8)
        scrivi_testo("CARICA PARTITA", btn_carica, (255,255,255))

    # ---- LOGICA INTRODUZIONE ----
    elif stato_gioco == "INTRODUZIONE":
        try:
            sfondo_stanza = pygame.image.load('stanza.jpeg').convert()
            sfondo_stanza = pygame.transform.scale(sfondo_stanza, (800,600))
        except:
            sfondo_stanza = pygame.Surface((800,600))
            sfondo_stanza.fill((60,60,100))
        screen.blit(sfondo_stanza, (0,0))

        # label più larga e alta
        larghezza_label = 760
        altezza_label = 100
        x_label = 20
        y_label = 500
        pygame.draw.rect(screen, (0,0,0,200), (x_label,y_label,larghezza_label,altezza_label))
        pygame.draw.rect(screen, (255,255,255), (x_label,y_label,larghezza_label,altezza_label),2)

        font_intro = pygame.font.SysFont("Constantia", 22, True)
        righe = intro_frasi[indice_lettura]
        for i,riga in enumerate(righe):
            screen.blit(font_intro.render(riga, True, (255,255,255)), (x_label+10, y_label+10 + i*25))

    # ---- LOGICA LIVELLO 0 ----
    elif stato_gioco == "LIVELLO_0":
        try:
            sfondo_livello0 = pygame.image.load('sfondo_livello0.jpeg').convert()
            sfondo_livello0 = pygame.transform.scale(sfondo_livello0, (800, 600))
        except:
            sfondo_livello0 = pygame.Surface((800, 600))
            sfondo_livello0.fill((30, 30, 30))
        screen.blit(sfondo_livello0, (0,0))

        # Scritta grande all'inizio
        if indice_lettura == 0:
            font_welcome = pygame.font.SysFont("Constantia", 40, True)  # più piccola per entrare nello sfondo
            testo_welcome = "WELCOME IN YOUR WORST NIGHTMARE"
            larghezza_testo = font_welcome.size(testo_welcome)[0]
            x_testo = (800 - larghezza_testo) // 2
            y_testo = 50  # in alto, sopra la label
            screen.blit(font_welcome.render(testo_welcome, True, (255, 255, 255)), (x_testo, y_testo))

        # Label in basso a sinistra
        larghezza_label = 760
        altezza_label = 120  # più alta
        x_label = 20
        y_label = 460
        pygame.draw.rect(screen, (0,0,0,200), (x_label, y_label, larghezza_label, altezza_label))
        pygame.draw.rect(screen, (255,255,255), (x_label, y_label, larghezza_label, altezza_label), 2)

        font_normale = pygame.font.SysFont("Constantia", 22)
        font_corsivo = pygame.font.SysFont("Constantia", 22, italic=True)
        righe = livello0_frasi[indice_lettura]  # frase corrente
        for i, riga in enumerate(righe):
            if riga.startswith("_") and riga.endswith("_"):
                testo_da_disegnare = riga[1:-1]  # rimuove i marcatori
                screen.blit(font_corsivo.render(testo_da_disegnare, True, (255,255,255)), (x_label+10, y_label+10 + i*25))
            else:
                screen.blit(font_normale.render(riga, True, (255,255,255)), (x_label+10, y_label+10 + i*25))


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()