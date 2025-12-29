import pygame

class GestoreLivelli:
    def __init__(self, larghezza, altezza):
        # Percorsi delle tue immagini sequenziali
        self.percorsi = [
            'livello_1.jpeg',
            'livello_2.jpeg',
            'livello_3.jpeg',
            'livello_4.jpeg',
            'livello_5.jpeg'
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

    def get_livello_attuale(self):
        return self.sfondi_scalati[self.indice_corrente]

    def prossimo_livello(self):
        if self.indice_corrente < len(self.sfondi_scalati) - 1:
            self.indice_corrente += 1
            return True
        return False # Gioco finito