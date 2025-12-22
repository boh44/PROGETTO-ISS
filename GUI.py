import pygame
import sys

# 1. Inizializzazione
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Menu di Gioco")
clock = pygame.time.Clock()

# --- STATO DEL GIOCO ---
# "MENU" = schermata principale, "SCELTA" = nuova partita o carica
stato_gioco = "MENU"

# --- FONT ---
font_bottoni = pygame.font.SysFont("Constantia", 25, bold=True)

# --- IMMAGINE DI SFONDO ---
try:
    sfondo = pygame.image.load('sfondo.jpeg').convert()
    sfondo = pygame.transform.scale(sfondo, (800, 600))
except:
    sfondo = pygame.Surface((800, 600))
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

def scrivi_testo(testo, rettangolo_bottone, colore_testo):
    superficie_testo = font_bottoni.render(testo, True, colore_testo)
    pos_testo = superficie_testo.get_rect(center=rettangolo_bottone.center)
    screen.blit(superficie_testo, pos_testo)

running = True
while running:
    pos_mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Logica Click MENU
                if stato_gioco == "MENU":
                    if btn_start.collidepoint(pos_mouse):
                        stato_gioco = "SCELTA"
                    if btn_settings.collidepoint(pos_mouse):
                        print("SETTINGS")
                    if btn_exit.collidepoint(pos_mouse):
                        running = False
                
                # Logica Click SCELTA
                elif stato_gioco == "SCELTA":
                    if btn_nuovo.collidepoint(pos_mouse):
                        print("Inizio da zero!")
                        # Qui potresti mettere stato_gioco = "LIVE"
                    if btn_carica.collidepoint(pos_mouse):
                        print("Caricamento dati...")


    screen.blit(sfondo, (0, 0))

    # Definizione Font e Testo
    f_label = pygame.font.SysFont("Constantia", 60, True)
    testo = "Beyond the screen"
    x_titolo = 400 - f_label.size(testo)[0] // 2
    y_titolo = 10

    # Effetto Sfumatura/Ombra (3 livelli)
    screen.blit(f_label.render(testo, True, (50, 50, 50)), (x_titolo + 2, y_titolo + 2))   # Ombra profonda
    screen.blit(f_label.render(testo, True, (150, 150, 150)), (x_titolo + 1, y_titolo + 1)) # Sfumatura media
    screen.blit(f_label.render(testo, True, (255, 255, 255)), (x_titolo, y_titolo))         # Testo bianco brillante
        
    if stato_gioco == "MENU":
        # Start
        h_s = btn_start.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (46, 204, 113) if h_s else (39, 174, 96), btn_start, border_radius=8)
        scrivi_testo("START", btn_start, (255, 255, 255))

        # Settings
        h_st = btn_settings.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (149, 165, 166) if h_st else (127, 140, 141), btn_settings, border_radius=8)
        scrivi_testo("SETTINGS", btn_settings, (255, 255, 255))

        # Exit
        h_e = btn_exit.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (231, 76, 60) if h_e else (192, 57, 43), btn_exit, border_radius=8)
        scrivi_testo("EXIT", btn_exit, (255, 255, 255))

    elif stato_gioco == "SCELTA":
        # Nuovo Gioco
        h_n = btn_nuovo.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (52, 152, 219) if h_n else (41, 128, 185), btn_nuovo, border_radius=8)
        scrivi_testo("DA ZERO", btn_nuovo, (255, 255, 255))

        # Carica Gioco
        h_c = btn_carica.collidepoint(pos_mouse)
        pygame.draw.rect(screen, (155, 89, 182) if h_c else (142, 68, 173), btn_carica, border_radius=8)
        scrivi_testo("CARICA", btn_carica, (255, 255, 255))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()