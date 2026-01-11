from operator import pos
import pygame
import sys
import os
from LogicaGioco import *
from main import *
import random

#Otteniamo lo sprite grafico
personaggio1, personaggio2, sprite_temp = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

#CREA IL BOSS SOLO SE NON ESISTE (nuova partita)
if manager_gioco.boss_attuale is None:
    boss_logico = Goblin(x=sprite_temp.pos[0] + 60, y=sprite_temp.pos[1])
    manager_gioco.boss_attuale = boss_logico
    boss_logico.attach(facade.auto_saver)
    sincronizza_hud()

def disegna_flash_sagoma(target_surface, sprite_visual, colore, alpha):
    # Crea una maschera dai pixel non trasparenti dello sprite
    mask = pygame.mask.from_surface(sprite_visual.frames[0])
    # Crea una superficie colorata della forma della maschera
    surf_flash = mask.to_surface(setcolor=(colore[0], colore[1], colore[2], alpha), unsetcolor=(0,0,0,0))
    # Disegna la sagoma colorata sopra lo sprite
    target_surface.blit(surf_flash, sprite_visual.pos)

# Assegniamo la grafica
boss_visual = sprite_temp
BOSS_MAP = {
    0: Goblin,
    1: Anubi,
    2: Chica,
    3: Yeti,
    4: SerpenteTreTeste
}
# --- SISTEMA NPC ---
lista_npc = [VecchioSaggio(), GuardiaCorrotta(), VecchioSaggio(), GuardiaCorrotta(), VecchioSaggio()]   #da capire perchè ne metti 5
npc_attivo = None
btn_opzioni_npc = [] # Conterrà i Rect dei pulsanti per le risposte

mostra_messaggio_livello = False    # da True quando un boss viene sconfitto (serve per la scritta BOSS SCONFITTO)
timer_messaggio = 0 
testo_passaggio = " " # sempre per BOSS SCONFITTO

# --- VARIABILI LABEL LIVELLO ---
mostra_label_livello = True   #è la variabile “interruttore” generale che decide se il banner del livello deve essere mostrato o no. DA CAMBIARE NOME IN mostra_label
indice_testo_label = 0        # Per scorrere tutte le frasi che ho
mostra_testo_boss = False
colore_banner_attuale = (255, 255, 255)
# --- VARIABILI TURNO ---
#scritta per i turni
if len(manager_gioco.giocatori) > 0: testo_turno = f"Turno di {manager_gioco.giocatori[0].nome}"
else: testo_turno = "Turno Giocatore 1"
player_turn = 1  # 1 = Player1, 2 = Player2, 3 = Mostro
saltata_turno_mostro = 0
giocatori_fuggiti = [False, False]

# Gestione feedback visivo nuovi oggetti
mostra_notifica_item = False
timer_notifica_item = 0
testo_notifica_item = ""
alpha_notifica_item = 0

# --- VARIABILI EFFETTI ---
boss_attacco_visual = False
timer_boss_attacco = 0
p1_danno_visual = False
timer_p1_danno = 0
p2_danno_visual = False
timer_p2_danno = 0

# --- VARIABILI EFFETTI ---
durata_effetto = 1300  # dura poco più di un secondo
nascondi_turno_timer = 0
durata_effetto = 600 # durata in millisecondi
shake_intensity = 0
timer_shake = 0

# --- GRAFICA NPC ---
# Carichiamo gli sprite animati per gli NPC (usa i percorsi corretti delle tue cartelle)
grafica_npc = {
    "VecchioSaggio": AnimatedSprite("old.png", 5, 1, 0, 0, scale=1.1),
    "GuardiaOscura": AnimatedSprite("guard.png", 5, 1, 0, 0, scale=0.9) }
sfondo_dialogo_img = pygame.image.load("sfondo_dialogo.png").convert_alpha()
sfondo_dialogo_img = pygame.transform.scale(sfondo_dialogo_img, (LARGHEZZA, ALTEZZA))
# Debug: controlla che l'immagine sia caricata correttamente
print("Sfondo dialogo dimensioni:", sfondo_dialogo_img.get_size())


#per dire cosa succede nel combattimento#
def disegna_banner_notifica(schermo, testo, colore_bordo):
    larghezza_schermo = schermo.get_width()
    altezza_banner = 70
    y_pos = 150  # Posizione verticale del banner
    
    # 1. Rettangolo di sfondo (nero con trasparenza)
    superficie_banner = pygame.Surface((larghezza_schermo, altezza_banner), pygame.SRCALPHA)
    superficie_banner.fill((0, 0, 0, 200)) # 200 è l'opacità
    schermo.blit(superficie_banner, (0, y_pos))
    
    # 2. Linee di bordo (sopra e sotto per stile)
    pygame.draw.line(schermo, colore_bordo, (0, y_pos), (larghezza_schermo, y_pos), 3)
    pygame.draw.line(schermo, colore_bordo, (0, y_pos + altezza_banner), (larghezza_schermo, y_pos + altezza_banner), 3)
    
    # 3. Testo (usa il tuo font già definito)
    font_banner = pygame.font.SysFont("Arial", 30, bold=True) # O il tuo font
    testo_render = font_banner.render(testo, True, (255, 255, 255))
    rect_testo = testo_render.get_rect(center=(larghezza_schermo // 2, y_pos + altezza_banner // 2))
    schermo.blit(testo_render, rect_testo)
running = True
while running:
    #gestione eventi
    pos_mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:    
            if event.key == pygame.K_ESCAPE:    #Se il tasto premuto è ESC, e lo stato del gioco è VITTORIA o GAME_OVER
                if stato_gioco in ["VITTORIA", "GAME_OVER"]:
                    manager_gioco.resetGameData()
                    stato_gioco = "MENU" # Torna al menu iniziale

        # --- GESTIONE RIDIMENSIONAMENTO FINESTRA ---
        if event.type == pygame.VIDEORESIZE:
            LARGHEZZA, ALTEZZA = event.w, event.h
            # 1. Aggiorna la finestra
            if not (screen.get_flags() & pygame.FULLSCREEN):
                screen = pygame.display.set_mode((LARGHEZZA, ALTEZZA), pygame.RESIZABLE)
            # 2. Ottieni l'indice del livello in modo sicuro
            indice_attuale = gestore_livelli.indice_corrente 
            # 3. Ricalcola posizioni, scale e BOTTONI
            nuovo_p1, nuovo_p2, nuovo_visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, indice_attuale)
            # 4. Assegna i nuovi oggetti grafici
            personaggio1, personaggio2 = nuovo_p1, nuovo_p2
            boss_visual = nuovo_visual
            # 5. Sincronizza l'HUD (per spostare barre vita e inventari)
            sincronizza_hud()
            # 6. Ridimensiona gli sfondi
            gestore_livelli.ridimensiona_tutto(LARGHEZZA, ALTEZZA)
            sfondo_dialogo_img = pygame.transform.scale(sfondo_dialogo_img, (LARGHEZZA, ALTEZZA))
            # 7. Sincronizza la logica del Boss alla sua nuova posizione grafica
            if manager_gioco.boss_attuale and boss_visual:
                manager_gioco.boss_attuale.pos = [boss_visual.pos[0], boss_visual.pos[1]]

        # --- GESTIONE TASTI PREMUTI ---
        if event.type == pygame.KEYDOWN:
            # --- TEST BOSS UCCISO CON K ---
            if event.key == pygame.K_k: #se premi K: Uccide il boss
                if manager_gioco.boss_attuale:
                    manager_gioco.boss_attuale.hp = 0

            # --- TEST PLAYER 1 (Tasto L) ---
            if event.key == pygame.K_l: #se premi L: Danneggia il Player 1 di 50 HP
                if stato_gioco == "GAMEPLAY" and manager_gioco.vite_rimanenti > 0:
                    boss = manager_gioco.boss_attuale
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
            
            # Tasto BACKSLASH per le stats del Player 2
            if event.key == pygame.K_BACKSLASH:
                stats_p2_aperte = not stats_p2_aperte

            # GESTIONE INPUT NOME NELL'INTRODUZIONE
            if input_nome_attivo:
                if event.key == pygame.K_RETURN and len(nome_inserito) > 1: #se inserisci un nome con almeno 2 caratteri e premi ENTER
                    input_nome_attivo = False 
                    stato_gioco = "SCELTA_MORALITA"
                elif event.key == pygame.K_BACKSPACE:   #se premi BACKSPACE cancella l'ultimo carattere
                    nome_inserito = nome_inserito[:-1] 
                else: 
                    if len(nome_inserito) < 12: 
                        nome_inserito += event.unicode

        # --- GESTIONE CLICK MOUSE ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  #Controlla se il mouse viene premuto con il tasto sinistro

            # --- MENU PRINCIPALE ---
            if stato_gioco == "MENU":   #Cambia lo stato di gioco in base al pulsante cliccato: avvia nuova partita, apri le impostazioni o esci dal gioco.
                if btn_start.collidepoint(pos_mouse): stato_gioco = "SCELTA"
                elif btn_settings.collidepoint(pos_mouse): stato_gioco = "SETTINGS"
                elif btn_exit.collidepoint(pos_mouse): running = False

            # -- SETTINGS --
            elif stato_gioco == "SETTINGS":
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

            # -- SCELTA --
            elif stato_gioco == "SCELTA":
                #-- NUOVA PARTITA --
                if btn_nuovo.collidepoint(pos_mouse):
                    manager_gioco.livello_corrente = 1
                    gestore_livelli.indice_corrente = 0
                    stato_gioco, indice_lettura = "INTRODUZIONE", 0
                    
                # -- CARICA PARTITA --
                elif btn_carica.collidepoint(pos_mouse):
                    if facade.carica_da_disco():
                        # 1. Recupera l'indice corretto dal manager caricato
                        indice_caricato = max(0, manager_gioco.livello_corrente - 1)
                        gestore_livelli.indice_corrente = indice_caricato
                        # 2. Riattacca gli osservatori ai player ripristinati
                        for p in manager_gioco.giocatori:
                            p.attach(facade.auto_saver)
                        # 3. Rigenera la GRAFICA (Posizioni e Scale)
                        nuovo_p1, nuovo_p2, nuovo_visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, gestore_livelli.indice_corrente)
                        personaggio1, personaggio2 = nuovo_p1, nuovo_p2
                        boss_visual = nuovo_visual
    
                        # 4. SINCRONIZZAZIONE LOGICA/GRAFICA BOSS
                        if manager_gioco.boss_attuale:  #Se il manager ha già caricato il boss dal disco, lo usiamo
                            manager_gioco.boss_attuale.pos = [boss_visual.pos[0], boss_visual.pos[1]]   ## Aggiorniamo la sua posizione logica affinché la barra vita lo segua
                            boss = manager_gioco.boss_attuale
                            print(f"Caricato Boss: {manager_gioco.boss_attuale.nome} con HP: {manager_gioco.boss_attuale.hp}")
                        else:
                            print("ERRORE GRAVE: boss_attuale mancante dopo il load")

                        # 5.Sincronizza l'HUD
                        sincronizza_hud()
                        # 6. Avvia il gioco
                        stato_gioco = "GAMEPLAY"
                        #mostra_label_livello = True    #levato per evitare che appaia di nuovo il banner
                        indice_testo_label = 0
                    else: 
                        print("Errore: Nessun salvataggio trovato.")

            # --- INTRODUZIONE E LIVELLO 0 ---
            elif stato_gioco == "INTRODUZIONE":
                indice_lettura += 1
                if indice_lettura >= len(intro_frasi): 
                    stato_gioco, indice_lettura = "LIVELLO_0", 0    #Passa al livello 0 dopo l'introduzione e resetta l'indice di lettura
                    mostra_label_livello = True
                    indice_testo_label = 0

            # --- LIVELLO 0 ---
            elif stato_gioco == "LIVELLO_0":
                if indice_lettura == len(livello0_frasi) - 1: #se abbiamo finito le frasi del livello 0
                    input_nome_attivo = True    #attiva l'input per il nome del giocatore
                else:   #altrimenti continua a leggere le frasi
                    indice_lettura += 1
            
            # -- SCELTA MORALITA --
            elif stato_gioco == "SCELTA_MORALITA":
                scelta = None
                if btn_eroe.collidepoint(pos_mouse): scelta = "eroe altruista"
                elif btn_mercenario.collidepoint(pos_mouse): scelta = "mercenario egoista"
                elif btn_indifferente.collidepoint(pos_mouse): scelta = "anima indifferente"

                if scelta:
                    creator = Player1Creator() if player_corrente == 1 else Player2Creator()
                    nome = valida_nome(nome_inserito, player_corrente)
                    p = creator.create_character(nome, 0)
                    # assegna item iniziali
                    p.add_item(Item("SpadaBase", "Attacco", 10, oggetto=SpadaBase()))
                    # aggiungi al manager e collega l'auto-saver
                    manager_gioco.giocatori.append(p)
                    p.attach(facade.auto_saver)
                    assegna_moralita(p, scelta)
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
                        gestore_livelli.indice_corrente = 0

            #-- MAPPA MONDI --
            elif stato_gioco == "MAPPA_MONDI":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    stato_gioco = "GAMEPLAY"
                    nuovo_indice = gestore_livelli.indice_corrente
                    mostra_label_livello = True
                    indice_testo_label = 0
                    # RESET TURNO PLAYER
                    player_turn = 1
                    nome_p1 = manager_gioco.giocatori[0].nome if len(manager_gioco.giocatori) > 0 else "P1"
                    testo_turno = f"Turno di {nome_p1}"
                                
                    # 1. Aggiorna grafica
                    p1, p2, visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, nuovo_indice)
                    boss_visual = visual
                    ClasseBoss = BOSS_MAP.get(nuovo_indice)

                    # CREA IL BOSS SOLO SE NON ESISTE (nuova partita)
                    if ClasseBoss and manager_gioco.boss_attuale is None:
                        manager_gioco.boss_attuale = ClasseBoss(
                            x=boss_visual.pos[0],
                            y=boss_visual.pos[1])
                    sincronizza_hud()
                    
            # --- DIALOGO NPC ---
            elif stato_gioco == "DIALOGO_NPC":
                for i, btn in enumerate(btn_opzioni_npc):   #per ogni pulsante di risposta
                    if btn.collidepoint(pos_mouse):         #se il mouse clicca su quel pulsante
                        # Applica gli effetti della scelta
                        for p in manager_gioco.giocatori:
                            npc_attivo.interagisci(p, i)

                        # Torna alla mappa mondi
                        stato_gioco = "MAPPA_MONDI"
                        fase_transizione = "FINE"

            # --- GAMEPLAY ---    
            elif stato_gioco == "GAMEPLAY":
                click_valido = False

                # 🔒 BLOCCO TOTALE LOGICA se deve spunta "BOSS SCONFITTO"
                if mostra_messaggio_livello: pass
                elif mostra_label_livello:
                    # --- MOSTRA LABEL LIVELLO INIZIALE ---
                    livello_corrente = gestore_livelli.indice_corrente
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        indice_testo_label += 1
                        #click_valido = True
                        if indice_testo_label >= len(testi_livello[livello_corrente]):
                            mostra_label_livello = False
                            indice_testo_label = 0
                else:
                    #Recuperiamo il boss dal manager in modo sicuro
                    boss = manager_gioco.boss_attuale
                    # Controllo Vittoria Livello
                    if boss and not boss.is_alive() and not mostra_messaggio_livello:   #Se il boss è morto e non stiamo già mostrando il messaggio
                        if gestore_livelli.indice_corrente < 4: 
                            mostra_messaggio_livello = True
                            timer_messaggio = pygame.time.get_ticks()
                            testo_passaggio = "BOSS SCONFITTO!"
                            fase_transizione = "INIZIO"
                            print(f"Log: {boss.nome} sconfitto! Preparazione passaggio livello...")
                        else:  # Caso Boss Finale
                            stato_gioco = "VITTORIA"
                            alpha_fade = 255
                            colore_transizione = (255, 255, 255)
                            fase_transizione = "SVELA_VITTORIA"   
                    else:                    
                        # --- PLAYER 1 INVENTARIO ---
                        tab_p1_cliccata = False
                        if inv_p1_aperto:
                            if 90 < pos_mouse[1] < 125: 
                                if 20 < pos_mouse[0] < 80: idx_cat_p1 = 0; tab_p1_cliccata = True
                                elif 80 < pos_mouse[0] < 140: idx_cat_p1 = 1; tab_p1_cliccata = True
                                elif 140 < pos_mouse[0] < 200: idx_cat_p1 = 2; tab_p1_cliccata = True
                        # Se non abbiamo cliccato una TAB, allora controlliamo il pulsante INV
                        if not tab_p1_cliccata and rect_btn_p1.collidepoint(pos_mouse):
                            inv_p1_aperto = not inv_p1_aperto
                            
                        # --- PLAYER 2 INVENTARIO ---
                        tab_p2_cliccata = False
                        x_inv_p2 = LARGHEZZA - 305 
                        if inv_p2_aperto:
                            if 90 < pos_mouse[1] < 125:
                                if x_inv_p2 < pos_mouse[0] < x_inv_p2 + 60:
                                    idx_cat_p2 = 0; tab_p2_cliccata = True
                                elif x_inv_p2 + 60 < pos_mouse[0] < x_inv_p2 + 120:
                                    idx_cat_p2 = 1; tab_p2_cliccata = True
                                elif x_inv_p2 + 120 < pos_mouse[0] < x_inv_p2 + 180:
                                    idx_cat_p2 = 2; tab_p2_cliccata = True
                        # Solo se NON ho cliccato una tab, controllo se devo chiudere l'inventario
                        if not tab_p2_cliccata and rect_btn_p2.collidepoint(pos_mouse):
                            inv_p2_aperto = not inv_p2_aperto
                            
                        # --- GESTIONE TURNI ---
                        if player_turn == 1 and not giocatori_fuggiti[0]:
                            player = manager_gioco.giocatori[0]
                            arma_corrente = next(iter(player._inventario), None).oggetto if len(player._inventario) > 0 else None

                            if btn_attacca.collidepoint(pos_mouse):
                                boss = manager_gioco.boss_attuale
                                player.attacca(boss, arma_corrente)
                                click_valido = True
                                # Controllo immediato morte boss
                                if boss and not boss.is_alive() and not mostra_messaggio_livello:
                                    mostra_messaggio_livello = True
                                    timer_messaggio = pygame.time.get_ticks()
                                    testo_passaggio = "BOSS SCONFITTO!"
                                    fase_transizione = "INIZIO"
                                    print(f"Log: {boss.nome} sconfitto! Preparazione passaggio livello...")

                            elif btn_fuggi.collidepoint(pos_mouse):
                                successo = player.fuggi(manager_gioco.boss_attuale)
                                if successo:
                                    giocatori_fuggiti[0] = True
                                click_valido = True
                            elif btn_ragiona.collidepoint(pos_mouse):
                                successo = player.ragiona(manager_gioco.boss_attuale)
                                if successo:
                                    saltata_turno_mostro += 1
                                click_valido = True

                            # Aggiorna turno
                            if click_valido:
                                if not giocatori_fuggiti[1]: 
                                    player_turn = 2
                                    nome_p2 = manager_gioco.giocatori[1].nome if len(manager_gioco.giocatori) > 1 else "P2"
                                    testo_turno = f"Turno di {nome_p2}"
                                else:
                                    player_turn = 3
        
                        elif player_turn == 2 and not giocatori_fuggiti[1]:
                            player = manager_gioco.giocatori[1]
                            arma_corrente = next(iter(player._inventario), None).oggetto if len(player._inventario) > 0 else None

                            if btn_attacca.collidepoint(pos_mouse):
                                boss = manager_gioco.boss_attuale
                                player.attacca(boss, arma_corrente)
                                click_valido = True
                                if boss and not boss.is_alive() and not mostra_messaggio_livello:
                                    mostra_messaggio_livello = True
                                    timer_messaggio = pygame.time.get_ticks()
                                    testo_passaggio = "BOSS SCONFITTO!"
                                    fase_transizione = "INIZIO"
                                    print(f"Log: {boss.nome} sconfitto! Preparazione passaggio livello...")

                            elif btn_fuggi.collidepoint(pos_mouse):
                                successo = player.fuggi(manager_gioco.boss_attuale)
                                if successo:
                                    giocatori_fuggiti[1] = True
                                click_valido = True

                            elif btn_ragiona.collidepoint(pos_mouse):
                                successo = player.ragiona(manager_gioco.boss_attuale)
                                if successo:
                                    saltata_turno_mostro += 1
                                click_valido = True
                                
                            # Aggiorna turno
                            if click_valido: player_turn = 3

                        # --- TURNO DEL BOSS ---
                        if player_turn == 3:
                            boss = manager_gioco.boss_attuale

                            if all(giocatori_fuggiti):
                                testo_turno_boss = "ENTRAMBI I GIOCATORI SONO FUGGITI!" # Aggiungi questa riga!
                                colore_banner_attuale = (0, 255, 255) 
                                mostra_testo_boss = True
                                fade_testo_boss = 255
                                timer_testo_boss = pygame.time.get_ticks()
                                
                                # Non azzerare gli HP qui se vuoi che il boss resti visibile mentre appare il banner
                                boss.hp = 0 
                                giocatori_fuggiti = [False, False]
                                player_turn = 1
                            else:
                                # Attacca solo i giocatori presenti
                                if saltata_turno_mostro > 0:
                                    testo_turno_boss = "Il mostro sembra confuso e salta il turno!"
                                    colore_banner_attuale = (255, 255, 0) 
                                    mostra_testo_boss = True
                                    timer_testo_boss = pygame.time.get_ticks()
                                    fade_testo_boss = 255
                                    saltata_turno_mostro -= 1
                                else:
                                    # --- 1. ATTIVAZIONE EFFETTO BOSS (Flash Bianco/Giallo) ---
                                    boss_attacco_visual = True
                                    timer_boss_attacco = pygame.time.get_ticks()

                                    # --- 2. ATTIVAZIONE TERREMOTO (Screen Shake) ---
                                    shake_intensity = 10  # Intensità del colpo
                                    timer_shake = pygame.time.get_ticks()

                                    testo_turno_boss = f"Il mostro attacca e infligge {boss.danno} danni"
                                    colore_banner_attuale = (255, 0, 0) 
                                    mostra_testo_boss = True
                                    timer_testo_boss = pygame.time.get_ticks()
                                    fade_testo_boss = 255

                                    # --- 3. ATTACCO AI GIOCATORI + EFFETTO ROSSO ---
                                    if not giocatori_fuggiti[0]: 
                                        boss.attacca(manager_gioco.giocatori[0])
                                        p1_danno_visual = True
                                        timer_p1_danno = pygame.time.get_ticks()

                                    if not giocatori_fuggiti[1]: 
                                        boss.attacca(manager_gioco.giocatori[1])
                                        p2_danno_visual = True
                                        timer_p2_danno = pygame.time.get_ticks()

                            # --- PASSAGGIO TURNO ---
                            # Aspettiamo il primo giocatore disponibile che non sia fuggito
                            nascondi_turno_timer = pygame.time.get_ticks()
                            if not giocatori_fuggiti[0]:
                                player_turn = 1
                                nome_p1 = manager_gioco.giocatori[0].nome if len(manager_gioco.giocatori) > 0 else "P1"
                                testo_turno = f"Turno di {nome_p1}"
                            elif not giocatori_fuggiti[1]:
                                player_turn = 2
                                nome_p2 = manager_gioco.giocatori[1].nome if len(manager_gioco.giocatori) > 1 else "P2"
                                testo_turno = f"Turno di {nome_p2}"
                            else:
                                player_turn = 1 # Fallback

            
    #--- DISEGNO SCHERMATE ---
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
    
    #2. Disegno dello sfondo
    if sfondo_base:
        screen.blit(sfondo_base, (0, 0))

    #3. Disegno HUD e pulsanti nello specifico stato
    if stato_gioco in ["MENU", "SCELTA"]:
        draw_text_centered("Beyond the screen", pygame.Rect(0, 20, LARGHEZZA, 100), (255, 255, 255), font_titolo)   #disegna il titolo del gioco in alto

    if stato_gioco == "MENU":
        for btn, txt, col in [(btn_start, "START", (39, 174, 96)), (btn_settings, "SETTINGS", (127, 140, 141)), (btn_exit, "EXIT", (192, 57, 43))]: #disegna i pulsanti del menu principale con i relativi colori
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
        draw_text_centered("RESET DATI", btn_reset_data, (255, 255, 255))   #Disegna il pulsante “RESET DATI” con colore rosso se esiste un salvataggio, altrimenti grigio scuro.
        pygame.draw.rect(screen, (149, 165, 166), btn_back_menu, border_radius=8)
        draw_text_centered("INDIETRO", btn_back_menu, (255, 255, 255))  #Disegna il pulsante “INDIETRO”
        
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
        frasi = intro_frasi[indice_lettura] if stato_gioco == "INTRODUZIONE" else livello0_frasi[indice_lettura]   #Se lo stato è INTRODUZIONE, usa le frasi dell'introduzione, altrimenti usa quelle del LIVELLO_0. 
        for i, riga in enumerate(frasi):
            is_corsivo = riga.startswith("_") and riga.endswith("_")    #Controlla se la riga è in corsivo (se inizia e finisce con "_")
            testo = riga.replace("_", "")   #Rimuove i caratteri "_" per il rendering.
            font = pygame.font.SysFont("Constantia", int(ALTEZZA * 0.035), italic=is_corsivo)   #Crea il font con il corsivo
            testo_surf = font.render(testo, True, (255, 255, 255))
            screen.blit(testo_surf, (40, (ALTEZZA - h_box) + i * 30))

        if input_nome_attivo:   #far vedere sullo schermo il nome mentre lo scrivi, con il cursore lampeggiante.
            txt_in = font_bottoni.render(f"P{player_corrente} Nome: {nome_inserito}|", True, (255, 255, 0))
            screen.blit(txt_in, (LARGHEZZA // 2 - txt_in.get_width() // 2, ALTEZZA - 55))

    elif stato_gioco == "SCELTA_MORALITA":
        font_piccolo = pygame.font.SysFont("Constantia", 18, bold=True)
        draw_text_centered("Che individuo sei davvero? Un eroe altruista, un mercenario egoista o un'anima indifferente?", pygame.Rect(0, ALTEZZA//4, LARGHEZZA, 50), (255, 255, 255), font_piccolo)
        for btn, txt, col in [(btn_eroe, "EROE", (46, 204, 113)), (btn_mercenario, "MERCENARIO", (231, 76, 60)), (btn_indifferente, "NEUTRALE", (149, 165, 166))]:
            pygame.draw.rect(screen, col, btn, border_radius=8)  #Disegna i pulsanti per scegliere la moralità con i relativi colori
            draw_text_centered(txt, btn, (255, 255, 255))

    elif stato_gioco == "MAPPA_MONDI":
        screen.blit(sfondi["mondi"][gestore_livelli.indice_corrente], (0, 0)) # Prima sfondo

        overlay = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA) #testi MAPPA_MONDI
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        draw_text_centered("I MONDI SI ALLINEANO", pygame.Rect(0, ALTEZZA // 2 - 50, LARGHEZZA, 50), (255, 255, 255), font_titolo)
        
        # Calcolo del numero livello: indice 0 -> Livello 1, indice 1 -> Livello 2...
        num_livello = gestore_livelli.indice_corrente + 1
        f_istruzioni = pygame.font.SysFont("Constantia", 22, italic=True)
        testo_dinamico = f"Clicca per iniziare la tua avventura nel Livello {num_livello}"
        draw_text_centered(testo_dinamico, pygame.Rect(0, ALTEZZA // 2 + 30, LARGHEZZA, 30), (200, 200, 200), f_istruzioni)
    

    elif stato_gioco == "GAMEPLAY":
        # ------- DISEGNO SFONDO ATTUALE ------
        # Recupera lo sfondo basandosi sull'indice appena aggiornato
        idx = gestore_livelli.indice_corrente
        sfondo_attuale = gestore_livelli.get_livello_attuale()    
        screen.blit(sfondo_attuale, (0, 0))
            
        # ------------ LOGICA DI GIOCO -------------------
        # CONTROLLO VITE (GAME OVER)
        if manager_gioco.vite_rimanenti <= 0:
            stato_gioco = "GAME_OVER"
            alpha_fade = 255
            colore_transizione = (0, 0, 0) # Fade verso il nero
            fase_transizione = "SVELA_VITTORIA"
            continue # Salta il resto del disegno per questo frame

        # --- TRANSIZIONE DOPO LA MORTE DEL BOSS --- 
        if mostra_messaggio_livello:
            tempo_trascorso = pygame.time.get_ticks() - timer_messaggio
            if tempo_trascorso > 1500:
                alpha_fade = min(255, alpha_fade + 5) 
            
            if tempo_trascorso > 2500: 
                mostra_messaggio_livello = False
                
                # 1. Memorizziamo quale livello abbiamo appena FINITO
                livello_appena_finito = gestore_livelli.indice_corrente 
                
                # 2. Avanziamo all'indice del PROSSIMO livello
                gestore_livelli.indice_corrente += 1 
                manager_gioco.livello_corrente = gestore_livelli.indice_corrente + 1
                nuovo_idx = gestore_livelli.indice_corrente 

                # --- LOGICA DI REINDIRIZZAMENTO ---
                # Se abbiamo finito il Livello 1 (indice 0) o il Livello 2 (indice 1)
                if livello_appena_finito < 2:
                    stato_gioco = "MAPPA_MONDI"
                # Se abbiamo finito il Livello 3 (Chica - indice 2) o Livello 4 (Yeti - indice 3)
                elif livello_appena_finito in [2, 3]:
                    # Assegna l'NPC corretto
                    npc_attivo = lista_npc[0] if livello_appena_finito == 2 else lista_npc[1]
                    stato_gioco = "DIALOGO_NPC"
                else:
                    # Fallback per sicurezza
                    stato_gioco = "MAPPA_MONDI"

                # Forza la scomparsa del nero della transizione
                alpha_fade = 0 
                fase_transizione = None

                # 3. RESET GRAFICO E LOGICO (Necessario per caricare il boss successivo)
                manager_gioco.boss_attuale = None 
                nuovo_p1, nuovo_p2, nuovo_visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, nuovo_idx)
                personaggio1, personaggio2 = nuovo_p1, nuovo_p2
                boss_visual = nuovo_visual

                # 4. Creazione Logica del nuovo Boss
                ClasseBoss = BOSS_MAP.get(nuovo_idx)
                if ClasseBoss:
                    nuovo_boss = ClasseBoss(x=boss_visual.pos[0], y=boss_visual.pos[1])
                    manager_gioco.boss_attuale = nuovo_boss
                    nuovo_boss.hp = nuovo_boss.max_hp
                    nuovo_boss.attach(facade.auto_saver)
                    
                    # Mostra il banner del nuovo livello SOLO se non siamo in dialogo
                    if stato_gioco != "DIALOGO_NPC":
                        mostra_label_livello = True
                        indice_testo_label = 0

                # 5. CONSEGNA ITEMS (Factory del livello)
                factory_map = {0: Livello1Item(), 1: Livello2Item(), 2: Livello3Item(), 3: Livello4Item(), 4: Livello5Item()}
                factory = factory_map.get(min(nuovo_idx, 4))
                if factory:
                    for player in manager_gioco.giocatori:
                        arma_logica = factory.create_arma()
                        pozione_logica = factory.create_pozione()
                        armatura_logica = factory.create_armatura()
                        InventoryUI.aggiorna_inventario(player, arma_logica, pozione_logica, armatura_logica)

                        #Banner di notifica oggetti ricevuti
                        ricevuti = []
                        if arma_logica: ricevuti.append(arma_logica.__class__.__name__)
                        if pozione_logica: ricevuti.append(pozione_logica.__class__.__name__)
                        if armatura_logica: ricevuti.append(armatura_logica.__class__.__name__)
                        if ricevuti:
                            mostra_notifica_item = True
                            timer_notifica_item = pygame.time.get_ticks()
                            alpha_notifica_item = 255
                            nomi_oggetti = ", ".join(ricevuti)
                            testo_notifica_item = f"RICEVUTI: {nomi_oggetti}!"
                
        # ----------- DISEGNA BANNER LIVELLO --------
        if mostra_label_livello:
            livello_corrente = gestore_livelli.indice_corrente
            draw_label_livello(screen, testi_livello[livello_corrente], LARGHEZZA, ALTEZZA)
        else:
            # --- CALCOLO SCREEN SHAKE ---
            offset_shake = [0, 0]
            if pygame.time.get_ticks() - timer_shake < 300: # Il terremoto dura 0.3 secondi
                offset_shake = [random.randint(-shake_intensity, shake_intensity), 
                                random.randint(-shake_intensity, shake_intensity)]
            
            # --- DISEGNO ENTITÀ (Con offset per lo shake) ---
            boss_logico = manager_gioco.boss_attuale
            if boss_logico and boss_logico.is_alive() and not mostra_messaggio_livello:
                # Salviamo la posizione originale, applichiamo lo shake e disegnamo
                pos_originale = boss_visual.pos
                boss_visual.pos = (pos_originale[0] + offset_shake[0], pos_originale[1] + offset_shake[1])
                boss_visual.disegna(screen, con_ombra=True)
                
                # Effetto Sagoma Bianca Boss
                if boss_attacco_visual:
                    tempo = pygame.time.get_ticks() - timer_boss_attacco
                    if tempo < durata_effetto:
                        alpha = 200 - int((tempo / durata_effetto) * 200)
                        disegna_flash_sagoma(screen, boss_visual, (255, 255, 200), alpha)
                    else: boss_attacco_visual = False
                
                boss_visual.pos = pos_originale # Ripristina posizione

            # --- PERSONAGGIO 1 (Effetto Rosso + Shake) ---
            pos_orig_p1 = personaggio1.pos
            personaggio1.pos = (pos_orig_p1[0] + offset_shake[0], pos_orig_p1[1] + offset_shake[1])
            personaggio1.disegna(screen, con_ombra=True)
            if p1_danno_visual:
                tempo = pygame.time.get_ticks() - timer_p1_danno
                if tempo < durata_effetto:
                    alpha = 180 - int((tempo / durata_effetto) * 180)
                    disegna_flash_sagoma(screen, personaggio1, (255, 0, 0), alpha)
                else: p1_danno_visual = False
            personaggio1.pos = pos_orig_p1

            # --- PERSONAGGIO 2 (Effetto Rosso + Shake) ---
            pos_orig_p2 = personaggio2.pos
            personaggio2.pos = (pos_orig_p2[0] + offset_shake[0], pos_orig_p2[1] + offset_shake[1])
            personaggio2.disegna(screen, con_ombra=True)
            if p2_danno_visual:
                tempo = pygame.time.get_ticks() - timer_p2_danno
                if tempo < durata_effetto:
                    alpha = 180 - int((tempo / durata_effetto) * 180)
                    disegna_flash_sagoma(screen, personaggio2, (255, 0, 0), alpha)
                else: p2_danno_visual = False
            personaggio2.pos = pos_orig_p2

            if mostra_notifica_item:
                tempo_corrente = pygame.time.get_ticks()
                # Mostra per 3 secondi, poi inizia a sparire
                if tempo_corrente - timer_notifica_item > 8000:
                    alpha_notifica_item -= 8 # Velocità del fade out
                    if alpha_notifica_item <= 0:
                        mostra_notifica_item = False
                
                if mostra_notifica_item:
                    font_notifica = pygame.font.SysFont("Constantia", 30, bold=True, italic=True)
                    # Creiamo una fascia nera semitrasparente larga quanto lo schermo
                    surf_bg = pygame.Surface((LARGHEZZA, 60), pygame.SRCALPHA)
                    # Usiamo l'alpha della notifica per far sfumare anche il rettangolo
                    bg_alpha = int(alpha_notifica_item * 0.7) # 70% dell'opacità attuale
                    surf_bg.fill((0, 0, 0, bg_alpha))
                    rect_bg = surf_bg.get_rect(center=(LARGHEZZA // 2, 300))
                    screen.blit(surf_bg, rect_bg)
                    
                    # Colore Oro per dare l'idea di un premio raro
                    surf_notifica = font_notifica.render(testo_notifica_item, True, (255, 215, 0))
                    surf_notifica.set_alpha(alpha_notifica_item)
                    # Posizionamento al centro dello schermo (parte alta)
                    rect_notifica = surf_notifica.get_rect(center=(LARGHEZZA // 2, 300))
                    # Un piccolo bagliore nero dietro per leggere meglio
                    ombra = font_notifica.render(testo_notifica_item, True, (0, 0, 0))
                    ombra.set_alpha(alpha_notifica_item)
                    screen.blit(ombra, (rect_notifica.x + 2, rect_notifica.y + 2))
                    
                    screen.blit(surf_notifica, rect_notifica)
                    
            # --- DISEGNO HUD ---
            font_hint = pygame.font.SysFont("Arial", 11, bold=True, italic=True)
            colore_hint = (200, 200, 200)
            font_piccolo = pygame.font.SysFont("Constantia", 18, bold=True)
            # --- Disegna il turno solo se è finito il secondo di pausa ---
            if pygame.time.get_ticks() - nascondi_turno_timer > 1000:
                draw_text_centered(testo_turno, pygame.Rect(0, 10, LARGHEZZA, 40), (255, 255, 255), font_piccolo)

                        # Testo del boss con fade
                        # --- DISEGNO BANNER NOTIFICA BOSS (Attacco, Fuga, Confusione) ---
            if mostra_testo_boss:
                # 1. Creazione della fascia nera semitrasparente
                altezza_banner = 60
                y_banner = 50 # Posizione verticale
                surf_banner = pygame.Surface((LARGHEZZA, altezza_banner), pygame.SRCALPHA)
                
                # Usiamo lo stesso fade_testo_boss per far sparire anche il banner
                bg_alpha = int(fade_testo_boss * 0.9) # 60% dell'opacità attuale
                surf_banner.fill((0, 0, 0, bg_alpha))
                screen.blit(surf_banner, (0, y_banner - 10))

                # 2. Rendering del testo (Usa il colore_banner_attuale impostato nella logica)
                # Se non hai ancora definito colore_banner_attuale, usa (255, 255, 0) di default
                txt_surf = font_piccolo.render(testo_turno_boss, True, colore_banner_attuale)
                txt_surf.set_alpha(fade_testo_boss)
                
                # Centratura testo nel banner
                txt_rect = txt_surf.get_rect(center=(LARGHEZZA // 2, y_banner + altezza_banner // 2 - 10))
                screen.blit(txt_surf, txt_rect)

                # 3. Logica di Fade Out (già presente nel tuo codice)
                tempo_trascorso = pygame.time.get_ticks() - timer_testo_boss
                if tempo_trascorso > 1500:  # Aumentato a 1.5 secondi per dare tempo di leggere
                    fade_testo_boss -= 5
                    if fade_testo_boss <= 0:
                        fade_testo_boss = 0
                        mostra_testo_boss = False


            # 1. Player 1
            cat_p1 = categorie_disponibili[idx_cat_p1]
            if hud["p1_health"]:
                hud["p1_health"].disegna(screen)
                screen.blit(font_hint.render("[TAB] STATS", True, colore_hint), (20, 48))
            pygame.draw.rect(screen, (60, 60, 60), rect_btn_p1, border_radius=5)
            draw_text_centered("INV", rect_btn_p1, (255, 215, 0), pygame.font.SysFont("Arial", 10, bold=True))
            if inv_p1_aperto and hud["p1_inv"]: hud["p1_inv"].disegna(screen, cat_p1)
            if stats_p1_aperte and len(manager_gioco.giocatori) > 0: 
                disegna_pannello_stats(screen, manager_gioco.giocatori[0], 20, 100)

            # 2. Player 2
            cat_p2 = categorie_disponibili[idx_cat_p2]
            if hud["p2_health"]: 
                hud["p2_health"].rect.x = LARGHEZZA - 220 
                hud["p2_health"].disegna(screen)
                txt_p2 = font_hint.render("[ \\ ] STATS", True, colore_hint)
                screen.blit(txt_p2, (LARGHEZZA - txt_p2.get_width() - 20, 48))
            pygame.draw.rect(screen, (60, 60, 60), rect_btn_p2, border_radius=5)
            draw_text_centered("INV", rect_btn_p2, (255, 215, 0), pygame.font.SysFont("Arial", 10, bold=True))
            if inv_p2_aperto and hud["p2_inv"]:
                hud["p2_inv"].x = LARGHEZZA - 265
                hud["p2_inv"].disegna(screen, cat_p2)   
            if stats_p2_aperte and len(manager_gioco.giocatori) > 1: 
                disegna_pannello_stats(screen, manager_gioco.giocatori[1], LARGHEZZA - 170, 100)

            # 3. BOSS HEALTH BAR
            if hud.get("boss_health") and manager_gioco.boss_attuale and manager_gioco.boss_attuale.is_alive():
                boss_logico = manager_gioco.boss_attuale
                nome = boss_logico.nome.strip().lower()
                # Prendi coordinate attuali dello sprite
                boss_x, boss_y = boss_visual.pos
                frame = boss_visual.frames[0]
                larg_boss, alt_boss = frame.get_width(), frame.get_height()
                # Dimensioni barra
                w_b, h_b = 140, 12
                off_y = 10
                # Posizione predefinita della barra sopra la testa
                bx = boss_x + (larg_boss // 2) - (w_b // 2)
                by = boss_y - h_b - off_y

                # Barra predefinita sopra la testa
                if nome == "goblin":
                    # bx centrato rispetto al boss, poi piccolo aggiustamento
                    bx = boss_visual.pos[0] + (larg_boss // 2) - (w_b // 2) - 100  
                    by = boss_visual.pos[1] + alt_boss - 430  # sotto il corpo del Goblin
                elif nome == "serpente a tre teste":
                    bx = boss_visual.pos[0] + (larg_boss // 2) - (w_b // 2) + 60
                    by = boss_visual.pos[1] + alt_boss - 300
                elif nome == "yeti delle nevi":
                    bx = boss_visual.pos[0] + (larg_boss // 2) - (w_b // 2)
                    by = boss_visual.pos[1] + alt_boss - 350

                # Aggiorna la HUD
                hud["boss_health"].rect.update(bx, by, w_b, h_b)
                hud["boss_health"].disegna(screen)

                # Scritta Nome Boss centrata sopra la barra
                f_boss = pygame.font.SysFont("Constantia", 18, bold=True)
                txt_nome = f_boss.render(boss_logico.nome.upper(), True, (255, 255, 255))
                screen.blit(txt_nome, (bx + (w_b // 2) - (txt_nome.get_width() // 2), by - 18))

            # 4. BOTTONI AZIONI (Sempre in primo piano)
            for btn, txt, col in [
                (btn_attacca, "ATTACCA", (192, 57, 43)), 
                (btn_fuggi, "FUGGI", (127, 140, 141)), 
                (btn_ragiona, "RAGIONA", (39, 174, 96))
            ]:
                pygame.draw.rect(screen, col, btn, border_radius=8)
                draw_text_centered(txt, btn, (255, 255, 255))

            # 2. NON CAPITPO
            pygame.draw.rect(screen, (60, 60, 60), rect_btn_p2, border_radius=5)
            draw_text_centered("INV", rect_btn_p2, (255, 215, 0), pygame.font.SysFont("Arial", 10, bold=True))
            if inv_p2_aperto and hud["p2_inv"]:
                hud["p2_inv"].x = LARGHEZZA - 265
                hud["p2_inv"].disegna(screen, cat_p2)   
            if stats_p2_aperte and len(manager_gioco.giocatori) > 1: disegna_pannello_stats(screen, manager_gioco.giocatori[1], LARGHEZZA - 170, 100)


            # --- OVERLAY LIVELLO (Boss Sconfitto) ---
            if mostra_messaggio_livello:
                # Scurisce leggermente lo sfondo per far risaltare il testo
                overlay = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 100))
                screen.blit(overlay, (0, 0))

                box_msg = pygame.Surface((LARGHEZZA, 120), pygame.SRCALPHA)
                box_msg.fill((0, 0, 0, 200)) 
                screen.blit(box_msg, (0, ALTEZZA // 2 - 60))
                
                font_vittoria = pygame.font.SysFont("Constantia", 50, bold=True)
                draw_text_centered(testo_passaggio, pygame.Rect(0, ALTEZZA // 2 - 60, LARGHEZZA, 120), (255, 215, 0), font_vittoria)
    

    #4. NPC e animazioni
    elif stato_gioco == "DIALOGO_NPC":
        # 1. Sfondo del dialogo (sempre scalato correttamente)
        screen.blit(sfondo_dialogo_img, (0, 0))

        # --- 2. DISEGNO NPC ANIMATO DINAMICO ---
        if npc_attivo:
            npc_visual = grafica_npc.get(npc_attivo.nome)
            if npc_visual:
                # Recuperiamo le dimensioni reali del frame corrente
                sprite_w = npc_visual.frames[int(npc_visual.index)].get_width()
                sprite_h = npc_visual.frames[int(npc_visual.index)].get_height()

                if "Guardia" in npc_attivo.nome:
                    # POSIZIONE GUARDIA:
                    # X: 5% della larghezza
                    # Y: Allineata in modo che la testa sia sempre visibile (offset basato su altezza sprite)
                    npc_visual.pos = [int(LARGHEZZA * 0.05), int(ALTEZZA *0.1 )]
                else:
                    # POSIZIONE VECCHIO SAGGIO:
                    # X: 10% della larghezza
                    # Y: 20% dell'altezza (essendo più basso della guardia)
                    npc_visual.pos = [int(LARGHEZZA * 0.1), int(ALTEZZA * 0.2)]
                
                npc_visual.disegna(screen, con_ombra=True)

        # --- 3. BOX DOMANDA ADATTIVO (INGRANDITO) ---
        # Aumentiamo box_w (da 0.8 a 0.9) e box_h (da 0.15 a 0.25)
        box_w = int(LARGHEZZA * 0.9)
        box_h = int(ALTEZZA * 0.25)
        box_x = (LARGHEZZA - box_w) // 2
        # Lo abbassiamo un po' dal bordo superiore (da 0.05 a 0.07) per estetica
        box_y = int(ALTEZZA * 0.07) 
        
        box_domanda = pygame.Rect(box_x, box_y, box_w, box_h)
        box_surf = pygame.Surface(box_domanda.size, pygame.SRCALPHA)
        box_surf.fill((40, 40, 40, 230)) # Leggermente più opaco (230) per dialoghi lunghi
        screen.blit(box_surf, box_domanda.topleft)
        
        # Bordo un po' più spesso (3 invece di 2) per sostenerne la grandezza
        pygame.draw.rect(screen, (255, 215, 0), box_domanda, 3, border_radius=15)

        # --- 4. FONT DINAMICI ---
        # Aumentiamo leggermente anche la dimensione del font per riempire il box nuovo
        size_domanda = max(22, int(ALTEZZA * 0.015)) 
        size_opzioni = max(18, int(ALTEZZA * 0.038))
        
        font_domanda = pygame.font.SysFont("Constantia", size_domanda, bold=True)
        f_npc = pygame.font.SysFont("Constantia", size_opzioni)

        testo = f"{npc_attivo.nome}: {npc_attivo.domanda}"
        draw_text_centered(testo, box_domanda, (255, 255, 255), font_domanda)

        # --- 5. OPZIONI (PULSANTI) DINAMICHE ---
        btn_opzioni_npc.clear()
        padding = int(ALTEZZA * 0.02)
        btn_h = int(ALTEZZA * 0.08)
        btn_w = int(LARGHEZZA * 0.5)
        # Le opzioni partono dal 55% dell'altezza per non coprire l'NPC
        start_y = int(ALTEZZA * 0.55)

        for i, opzione in enumerate(npc_attivo.opzioni):
            rect = pygame.Rect((LARGHEZZA - btn_w) // 2, start_y + i * (btn_h + padding), btn_w, btn_h)
            btn_opzioni_npc.append(rect)

            colore = (100, 100, 100) if rect.collidepoint(pos_mouse) else (60, 60, 60)
            pygame.draw.rect(screen, colore, rect, border_radius=8)
            pygame.draw.rect(screen, (255, 215, 0), rect, 2, border_radius=8)

            draw_text_centered(opzione.testo, rect, (255, 255, 255), f_npc)


    elif stato_gioco == "VITTORIA":
        screen.fill((10, 10, 20))

        # --- SCALE DINAMICHE ---
        h = ALTEZZA
        w = LARGHEZZA

        titolo_size = int(h * 0.08)
        sub_size = int(h * 0.06)
        hint_size = int(h * 0.035)

        font_titolo = pygame.font.SysFont("Constantia", titolo_size, bold=True)
        font_bottoni = pygame.font.SysFont("Constantia", hint_size)

        y_titolo = int(h * 0.45)
        y_sub = int(h * 0.55)
        y_hint = int(h * 0.90)

        draw_text_centered("IL MALE È STATO ABBATTUTO", pygame.Rect(2, y_titolo + 2, w, titolo_size), (50, 50, 50), font_titolo)
        draw_text_centered("IL MALE È STATO ABBATTUTO",pygame.Rect(0, y_titolo, w, titolo_size),(255, 255, 255),font_titolo)
        draw_text_centered("FINALMENTE SEI LIBERO!",pygame.Rect(0, y_sub, w, sub_size),(0, 255, 150),font_titolo)
        draw_text_centered("Premi ESC per tornare al menu",pygame.Rect(0, y_hint, w, hint_size),(100, 100, 100),font_bottoni)

    # 7. Gestione Fade e Transizioni
    if alpha_fade > 0:
        fade_surf = pygame.Surface((LARGHEZZA, ALTEZZA))
        fade_surf.fill(colore_transizione)
        fade_surf.set_alpha(alpha_fade)
        screen.blit(fade_surf, (0, 0))

        if fase_transizione == "FINE":alpha_fade -= 5
        elif fase_transizione == "SVELA_VITTORIA":alpha_fade -= 2
        if alpha_fade <= 0:
            alpha_fade = 0
            fase_transizione = None

    # --- SCHERMATA GAME OVER ---
    elif stato_gioco == "GAME_OVER":
        screen.fill((20, 0, 0))

        h = ALTEZZA
        w = LARGHEZZA

        main_size = int(h * 0.09)
        sub_size = int(h * 0.04)

        font_main = pygame.font.SysFont("Constantia", main_size, bold=True)
        font_sub = pygame.font.SysFont("Constantia", sub_size, italic=True)

        y_main = int(h * 0.45)
        y_hint = int(h * 0.90)

        draw_text_centered("HAI FALLITO LA MISSIONE",pygame.Rect(0, y_main, w, main_size), (200, 0, 0), font_main)
        draw_text_centered("Premi ESC per tornare al menu", pygame.Rect(0, y_hint, w, sub_size),(100, 100, 100),font_sub)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()