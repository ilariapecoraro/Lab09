from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        self._tour_regione = []

        # Vincoli
        self._max_giorni = None
        self._max_budget = None

        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        relazioni = TourDAO.get_tour_attrazioni()
        # Restituisce una lista di dizionari [{"id_tour": ..., "id_attrazione": ...}]

        for relazione in relazioni:
            tour_id = relazione["tour_id"]
            attrazione_id = relazione["attrazioni_id"]

            # Collega Attrazione al Tour

            if tour_id in self.tour_map and attrazione_id in self.attrazioni_map:
                tour = self.tour_map[tour_id]
                attrazione = self.attrazioni_map[attrazione_id]

                tour.attrazioni.add(attrazione) # lista di oggetti Attrazione
                attrazione.tour.add(tour)


        # TODO

    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # TODO
        # Vincoli
        self._max_giorni = max_giorni
        self._max_budget = max_budget

        # Recupera una lista di oggetti tour disponibili per regione
        self._tour_regione = self._get_tour_per_regione(id_regione)

        # Avvia ricorsione
        self._ricorsione(0, [], 0, 0, 0, set())

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, attrazioni_usate: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno

        # Aggiornamento soluzione ottima
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente

        # Condizione terminale
        if start_index > len(self._tour_regione) or \
            (self._max_giorni is not None and durata_corrente >= self._max_giorni) or \
                (self._max_budget is not None and costo_corrente >= self._max_budget):
            return

        # Generazione di nuove soluzioni
        for i in range(start_index, len(self._tour_regione)):
            tour = self._tour_regione[i]

            # Controllo vincoli
            risultato = self.controllo_vincoli(tour, pacchetto_parziale, attrazioni_usate, durata_corrente, costo_corrente)
            if risultato is not None:
                nuova_durata, nuovo_costo = risultato

                # Aggiungi tour
                pacchetto_parziale.append(tour)
                attrazioni_usate.update(tour.attrazioni)
                nuovo_valore = valore_corrente + sum( a.valore_culturale for a in tour.attrazioni)

                # Ricorsione successiva
                self._ricorsione(i+1, pacchetto_parziale, nuova_durata, nuovo_costo, nuovo_valore, attrazioni_usate)

                # Backtracking
                pacchetto_parziale.pop()
                attrazioni_usate.difference_update(tour.attrazioni)


    def _get_tour_per_regione(self, id_regione: str):
        """ Restituisce tutti i tour disponibili per una regione specifica """
        lst_tour = []
        for tour in self.tour_map.values():
            if tour.id_regione == id_regione:
                lst_tour.append(tour)
        return lst_tour

    def controllo_vincoli(self, tour, pacchetto_parziale, attrazioni_usate, durata_corrente, costo_corrente):
        """
        Controlla i vincoli:
        * tour duplicati
        * attrazioni duplicate
        * durata massima
        * costo massimo
        """

        # L'assenza di tour duplicati è gia garantito grazie a start_index

        # Controlla attrazioni duplicate
        if attrazioni_usate.intersection(tour.attrazioni):
            return None

        # Calcola nuova durata e costo
        nuova_durata = durata_corrente + tour.durata
        nuovo_costo = costo_corrente + tour.costo

        # Filtro su durata e costo
        if self._max_giorni is not None and nuova_durata > self._max_giorni:
            return None
        if self._max_budget is not None and nuovo_costo > self._max_budget:
            return None

        return nuova_durata, nuovo_costo
