from operator import pos
import pygame
import sys
import os
from LogicaGioco import *
from livelli import GestoreLivelli
from main import *

# 1. Otteniamo lo sprite grafico
personaggio1, personaggio2, sprite_temp = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA)

# CREA IL BOSS SOLO SE NON ESISTE (nuova partita)
if manager_gioco.boss_attuale is None:
    boss_logico = Goblin(x=sprite_temp.pos[0] + 60, y=sprite_temp.pos[1])
    manager_gioco.boss_attuale = boss_logico
    boss_logico.attach(facade.auto_saver) 
    sincronizza_hud()

#mostra_intro_turno = True
#timer_intro_turno = pygame.time.get_ticks()
#testo_intro_turno = "PREPARATI A COMBATTERE!"
#fade_intro_turno = 255

testo_turno = "Turno Giocatore 1"

# 3. Assegniamo la grafica
boss_visual = sprite_temp
BOSS_MAP = {
    0: Goblin,
    1: Anubi,
    2: Chica,
    3: Yeti,
    4: SerpenteTreTeste
}

mostra_messaggio_livello = False    # da True quando un boss viene sconfitto (serve per la scritta BOSS SCONFITTO)
timer_messaggio = 0 
testo_passaggio = " " # sempre per BOSS SCONFITTO

# --- VARIABILI LABEL LIVELLO ---
mostra_label_livello = True   #è la variabile “interruttore” generale che decide se il banner del livello deve essere mostrato o no. DA CAMBIARE NOME IN mostra_label
indice_testo_label = 0        # Per scorrere tutte le frasi che ho
mostra_testo_boss = False

# --- VARIABILI TURNO ---
player_turn = 1  # 1 = Player1, 2 = Player2, 3 = Mostro
saltata_turno_mostro = 0
giocatori_fuggiti = [False, False]

running = True
while running:
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
                        # Questa funzione deve solo calcolare dove disegnare, non ricreare la logica
                        nuovo_p1, nuovo_p2, nuovo_visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, gestore_livelli.indice_corrente)
                        personaggio1, personaggio2 = nuovo_p1, nuovo_p2
                        boss_visual = nuovo_visual
                        
                        # 4. SINCRONIZZAZIONE LOGICA/GRAFICA BOSS
                        # Se il manager ha già caricato il boss dal disco, lo usiamo
                        if manager_gioco.boss_attuale:
                            # Aggiorniamo la sua posizione logica affinché la barra vita lo segua
                            manager_gioco.boss_attuale.pos = [boss_visual.pos[0], boss_visual.pos[1]]
                            # FONDAMENTALE: aggiorna la variabile 'goblin' usata nel loop principale
                            boss = manager_gioco.boss_attuale
                            print(f"Caricato Boss: {manager_gioco.boss_attuale.nome} con HP: {manager_gioco.boss_attuale.hp}")

                        else:
                            print("ERRORE GRAVE: boss_attuale mancante dopo il load")

                        # 5. Sincronizza l'HUD (Questo collega fisicamente la HealthBar ai dati del boss caricato)
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
                    testo_turno = "Turno Giocatore 1"
                                
                    # 1. Aggiorna grafica
                    p1, p2, visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, nuovo_indice)
                    boss_visual = visual
                    ClasseBoss = BOSS_MAP.get(nuovo_indice)

                    # CREA IL BOSS SOLO SE NON ESISTE (nuova partita)
                    if ClasseBoss and manager_gioco.boss_attuale is None:
                        manager_gioco.boss_attuale = ClasseBoss(
                            x=boss_visual.pos[0],
                            y=boss_visual.pos[1])

                    # 3. SINCRONIZZA HUD (Indispensabile per aggiornare l'Observer della barra)
                    sincronizza_hud()

            # --- GAMEPLAY ---    
            elif stato_gioco == "GAMEPLAY":
                # 🔒 BLOCCO TOTALE LOGICA se deve spunta "BOSS SCONFITTO"
                if mostra_messaggio_livello: pass
                else:
                    #aggiungi cose inventario
                    # --- AVANZA LABEL LIVELLO ---
                    if mostra_label_livello and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        indice_testo_label += 1
                        livello_corrente = gestore_livelli.indice_corrente
                        if indice_testo_label >= len(testi_livello[livello_corrente]):
                            mostra_label_livello = False
                            indice_testo_label = 0

            # 1. Recuperiamo il boss dal manager in modo sicuro
                    boss = manager_gioco.boss_attuale
                    # 2. Controllo Vittoria Livello
                    if boss and not boss.is_alive() and not mostra_messaggio_livello:   #Se il boss è morto e non stiamo già mostrando il messaggio
                        # mostra il messaggio
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
                            elif btn_ragiona.collidepoint(pos_mouse):
                                successo = player.ragiona(manager_gioco.boss_attuale)
                                if successo:
                                    saltata_turno_mostro += 1
                            # Aggiorna turno
                            if not giocatori_fuggiti[1]: 
                                player_turn = 2
                                testo_turno = "Turno Giocatore 2"
                            else: player_turn = 3
        
                        elif player_turn == 2 and not giocatori_fuggiti[1]:
                            player = manager_gioco.giocatori[1]
                            arma_corrente = next(iter(player._inventario), None).oggetto if len(player._inventario) > 0 else None

                            if btn_attacca.collidepoint(pos_mouse):
                                boss = manager_gioco.boss_attuale
                                player.attacca(boss, arma_corrente)
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
                            elif btn_ragiona.collidepoint(pos_mouse):
                                successo = player.ragiona(manager_gioco.boss_attuale)
                                if successo:
                                    saltata_turno_mostro += 1

                            # Aggiorna turno
                            player_turn = 3
                            # Mostra turno corrente

                        # --- TURNO DEL BOSS ---
                        if player_turn == 3:
                            boss = manager_gioco.boss_attuale

                            if all(giocatori_fuggiti):
                                print("Entrambi i giocatori sono fuggiti! Mostro sconfitto!")
                                boss.hp = 0
                                giocatori_fuggiti = [False, False]  # reset
                                player_turn = 1
                            else:
                                # Attacca solo i giocatori presenti
                                if saltata_turno_mostro > 0:
                                    testo_turno_boss = "Il mostro sembra confuso e salta il turno!"
                                    mostra_testo_boss = True
                                    timer_testo_boss = pygame.time.get_ticks()
                                    fade_testo_boss = 255
                                    saltata_turno_mostro -= 1
                                else:
                                    testo_turno_boss = f"Il mostro attacca e infligge {boss.danno} danni"
                                    mostra_testo_boss = True
                                    timer_testo_boss = pygame.time.get_ticks()
                                    fade_testo_boss = 255

                                    if not giocatori_fuggiti[0]: boss.attacca(manager_gioco.giocatori[0])
                                    if not giocatori_fuggiti[1]: boss.attacca(manager_gioco.giocatori[1])

                            # Riparti dal primo giocatore non fuggito
                            if not giocatori_fuggiti[0]:
                                player_turn = 1
                                testo_turno = "Turno Giocatore 1"
                            elif not giocatori_fuggiti[1]:
                                player_turn = 2
                                testo_turno = "Turno Giocatore 2"

    # --- 6. DISEGNO ---
    sfondo_base = None
    if stato_gioco in ["MENU", "SCELTA", "SETTINGS"]: 
        sfondo_base = sfondi["menu"]
    elif stato_gioco == "INTRODUZIONE": 
        sfondo_base = sfondi["stanza"]
    elif stato_gioco in ["LIVELLO_0", "SCELTA_MORALITA"]: 
        sfondo_base = sfondi["l0"]
    elif stato_gioco == "MAPPA_MONDI": 
        sfondo_base = sfondi["mondi"][0]
        '''if stato_gioco == "GAMEPLAY" and mostra_intro_turno:
            # Disegna la scritta prima del gioco
            tempo_trascorso_intro = pygame.time.get_ticks() - timer_intro_turno
            font_intro = pygame.font.SysFont("Constantia", 48, bold=True)
            txt_surf = font_intro.render(testo_intro_turno, True, (255, 255, 0))
            txt_surf.set_alpha(fade_intro_turno)
            screen.blit(txt_surf, (LARGHEZZA//2 - txt_surf.get_width()//2, ALTEZZA//2 - txt_surf.get_height()//2))

            # Fade out dopo 3 secondi
            if tempo_trascorso_intro > 3000:
                fade_intro_turno -= 5
                if fade_intro_turno <= 0:
                    fade_intro_turno = 0
                    mostra_intro_turno = False

            pygame.display.flip()
            clock.tick(60)
            continue  # Salta il resto del loop finché la scritta è visibile'''

    elif stato_gioco == "GAMEPLAY": 
        sfondo_base = gestore_livelli.get_livello_attuale()
    if sfondo_base:
        screen.blit(sfondo_base, (0, 0))

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
        # DISEGNA BANNER LIVELLO
        '''if mostra_label_livello and stato_gioco in ["LIVELLO_0","MAPPA_MONDI", "GAMEPLAY"]:
            livello_corrente = gestore_livelli.indice_corrente
            draw_label_livello(screen, testi_livello[livello_corrente], LARGHEZZA, ALTEZZA) # Poi banner'''

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
        # --- DISEGNO SFONDO ATTUALE ---
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
                gestore_livelli.indice_corrente += 1 
                manager_gioco.livello_corrente = gestore_livelli.indice_corrente + 1
                nuovo_idx = gestore_livelli.indice_corrente     
                mostra_label_livello = True   # Mostra il banner all’inizio del nuovo livello
                indice_testo_label = 0

                # --- RESET FONDAMENTALE ---
                manager_gioco.boss_attuale = None  # rimuovi boss vecchio
                # 1. Reset Grafico
                nuovo_p1, nuovo_p2, nuovo_visual = aggiorna_posizioni_e_scale(LARGHEZZA, ALTEZZA, nuovo_idx)
                personaggio1, personaggio2 = nuovo_p1, nuovo_p2
                boss_visual = nuovo_visual
                # 2. Reset Logico del Boss (CREAZIONE)
                ClasseBoss = BOSS_MAP.get(nuovo_idx)
                if ClasseBoss:
                    nuovo_boss = ClasseBoss(
                        x=boss_visual.pos[0],
                        y=boss_visual.pos[1]
                    )
                    manager_gioco.boss_attuale = nuovo_boss
                    mostra_label_livello = True  # attiva banner testo livello
                    indice_testo_label = 0
                    # FORZA STATO PULITO
                    nuovo_boss.hp = nuovo_boss.max_hp
                    # collega l'autosaver SOLO DOPO, senza notify
                    nuovo_boss.attach(facade.auto_saver)
                    # --- AGGIORNA ITEMS DEI GIOCATORI ---
                    '''factory = {
                        0: Livello1Item(),
                        1: Livello2Item(),
                        2: Livello3Item(),
                        3: Livello4Item(),
                        4: Livello5Item()
                    }[nuovo_idx]

                    # Aggiorna inventario dei giocatori
                    for player in manager_gioco.giocatori:
                        # Creiamo gli oggetti dal factory
                        arma = factory.create_arma()
                        pozione = factory.create_pozione()
                        armatura = factory.create_armatura()

                        # Li aggiungiamo correttamente come Item
                        InventoryUI.aggiorna_inventario(
                            player,
                            Item(nome=arma.__class__.__name__, tipo="Attacco", valore=getattr(arma, "danno", 0), oggetto=arma) if arma else None,
                            Item(nome=pozione.__class__.__name__, tipo="Cura", valore=getattr(pozione, "cura", 0), oggetto=pozione) if pozione else None,
                            Item(nome=armatura.__class__.__name__, tipo="Armatura", valore=0, oggetto=armatura) if armatura else None
                        )
                        # --- Usa automaticamente la prima pozione di tipo "Cura" se presente ---
                        pozione_item = next(
                            (item for item in player._inventario if item is not None and item.tipo == "Cura"), None)
                        if pozione_item and pozione_item.oggetto:  # prendi l'oggetto reale
                            pozione_obj = pozione_item.oggetto  # questo è tipo PozioneCura o KitPozioniFinale
                            pozione_obj.usa(player)  # usa la pozione sul player
                            print(f"Log: {player.nome} usa automaticamente {pozione_item.nome}. HP attuali: {player.hp}")
                            # Rimuoviamo la pozione dall'inventario
                            player._inventario._items.remove(pozione_item)'''

                stato_gioco = "MAPPA_MONDI"
                fase_transizione = "FINE"
                
        # ----------- DISEGNA BANNER LIVELLO --------
        if mostra_label_livello:
            livello_corrente = gestore_livelli.indice_corrente
            draw_label_livello(screen, testi_livello[livello_corrente], LARGHEZZA, ALTEZZA)
        else:
            # --- DISEGNO ENTITÀ ---
            boss_logico = manager_gioco.boss_attuale
            if boss_logico and boss_logico.is_alive() and not mostra_messaggio_livello:
                # Sincronizza la grafica alla logica
                boss_visual.pos = boss_logico.pos
                boss_visual.disegna(screen, con_ombra=True)

            personaggio1.disegna(screen, con_ombra=True)
            personaggio2.disegna(screen, con_ombra=True)

            # --- DISEGNO HUD ---
            font_hint = pygame.font.SysFont("Arial", 11, bold=True, italic=True)
            colore_hint = (200, 200, 200)

            # Font piccolo per altri testi normali
            font_piccolo = pygame.font.SysFont("Constantia", 18, bold=True)
            draw_text_centered(testo_turno, pygame.Rect(0, 10, LARGHEZZA, 40), (255, 255, 255), font_piccolo)

            # Testo del boss con fade
            if mostra_testo_boss:
                txt_surf = font_piccolo.render(testo_turno_boss, True, (255, 255, 0))
                txt_surf.set_alpha(fade_testo_boss)
                screen.blit(txt_surf, (LARGHEZZA // 2 - txt_surf.get_width() // 2, 50))

                # Fade out
                tempo_trascorso = pygame.time.get_ticks() - timer_testo_boss
                if tempo_trascorso > 500:  # dopo mezzo secondo inizia a scomparire
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

                # Barretta predefinita sopra la testa
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

    elif stato_gioco == "VITTORIA":
        screen.fill((10, 10, 20)) 
        
        font_titolo = pygame.font.SysFont("Constantia", 60, bold=True)
        draw_text_centered("IL MALE È STATO ABBATTUTO", pygame.Rect(2, ALTEZZA // 2 - 78, LARGHEZZA, 60), (50, 50, 50), font_titolo)
        draw_text_centered("IL MALE È STATO ABBATTUTO", pygame.Rect(0, ALTEZZA // 2 - 80, LARGHEZZA, 60), (255, 255, 255), font_titolo)
        draw_text_centered("FINALMENTE SEI LIBERO!", pygame.Rect(0, ALTEZZA // 2, LARGHEZZA, 50), (0, 255, 150), font_titolo)
        draw_text_centered("Premi ESC per tornare al menu", pygame.Rect(0, ALTEZZA - 100, LARGHEZZA, 30), (100, 100, 100), font_bottoni)

    # --- DISEGNO DEL FADE GLOBALE ---
    if alpha_fade > 0:
        fade_surf = pygame.Surface((LARGHEZZA, ALTEZZA))
        fade_surf.fill(colore_transizione) 
        fade_surf.set_alpha(alpha_fade)
        screen.blit(fade_surf, (0, 0))
        
        # Gestiamo qui tutte le uscite dai fade
        if fase_transizione == "FINE": alpha_fade -= 5
        elif fase_transizione == "SVELA_VITTORIA": alpha_fade -= 2 # Più lento per la vittoria
            
        if alpha_fade <= 0:
            alpha_fade = 0
            fase_transizione = None

    # --- SCHERMATE GAME OVER ---
    elif stato_gioco == "GAME_OVER":
        screen.fill((20, 0, 0)) # Sfondo rosso scuro/nero
        
        font_main = pygame.font.SysFont("Constantia", 70, bold=True)
        font_sub = pygame.font.SysFont("Constantia", 30, italic=True)
        
        # Testo principale "GAME OVER"
        draw_text_centered("HAI FALLITO LA MISSIONE", pygame.Rect(0, ALTEZZA // 2 - 60, LARGHEZZA, 70), (200, 0, 0), font_main)
        draw_text_centered("Premi ESC per tornare al menu", pygame.Rect(0, ALTEZZA - 100, LARGHEZZA, 30), (100, 100, 100), font_sub)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()