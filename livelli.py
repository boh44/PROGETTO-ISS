import pygame
import os
import sys

class GestoreLivelli:
    def __init__(self, larghezza, altezza):
        # Percorsi delle tue immagini sequenziali
        self.percorsi = [
            'sfondo_livello1.jpeg',
            'sfondo_livello2.jpg',
            'sfondo_livello3.jpeg',
            'sfondo_livello4.jpeg',
            'sfondo_livello5.jpeg'
        ]


        # Carichiamo i "Master" (originali)
        self.master_images = []
        for p in self.percorsi:
            try:
                img = pygame.image.load(p).convert()
                self.master_images.append(img)
            except:
                # Fallback se l'immagine manca (rettangolo blu)
                fallback = pygame.Surface((800, 600))
                fallback.fill((0, 0, 100))
                self.master_images.append(fallback)
        
        # Sfondi pronti per il disegno (scalati)
        self.sfondi_scalati = []
        self.ridimensiona_tutto(larghezza, altezza)
        
        self.indice_corrente = 0

    def ridimensiona_tutto(self, L, A):
        """Richiamata quando la finestra cambia dimensione"""
        self.sfondi_scalati = [pygame.transform.scale(img, (L, A)) for img in self.master_images]

    # In livelli.py

    def get_livello_attuale(self): # Rimuovi 'sfondi_dict' da qui!
        # Usiamo la lista interna della classe (quella generata dai percorsi)
        if 0 <= self.indice_corrente < len(self.sfondi_scalati):
            return self.sfondi_scalati[self.indice_corrente]
        else:
            return self.sfondi_scalati[-1] # Fallback sull'ultimo se l'indice è fuori

    def prossimo_livello(self):
        if self.indice_corrente < len(self.sfondi_scalati) - 1:
            self.indice_corrente += 1
            return True
        return False # Gioco finito
