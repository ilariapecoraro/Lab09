from turtledemo.penrose import start

from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO
from model.tour import Tour
import copy

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione
        self.relazioni = {}
        self.tour_per_regione = []

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

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

        for relazione in relazioni:
            id_tour = relazione["id_tour"]
            id_attrazione = relazione["id_attrazione"]

            # Recupera gli oggetti dal dizionario
            tour = self.tour_map.get(id_tour)
            attrazione = self.attrazioni_map.get(id_attrazione)

            # Tour con Attrazioni
            try:
                tour.attrazioni.append(attrazione)
            except AttributeError:
                tour.attrazioni = [attrazione]

            # Attrazioni con Tour
            try:
                attrazione.tour.append(tour)
            except AttributeError:
                attrazione.tour = [tour]



    # funzione che crea una lista di oggetti Tour in base al mese scelto
    def tour_regione(self, regione):
        self.tour_per_regione.clear()
        # essendo un dizionario, bisogna iterare sui valori
        for tour in self.tour_map.values(): # se non si mette .values si itera sulle chiavi
            if tour.id_regione == regione:
                self.tour_per_regione.append(tour)

        return self.tour_per_regione

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

        self._max_giorni = max_giorni
        self._max_budget = max_budget

        self.tour_regione(id_regione)
        self._ricorsione(0,[],0,0,0, set())
        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, attrazioni_usate: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""
        # caso terminale
        if start_index == len(self.tour_per_regione):

            if valore_corrente > self._valore_ottimo:
                self._valore_ottimo = valore_corrente
                self._pacchetto_ottimo = copy.deepcopy(pacchetto_parziale) # così da non cambiare la lista originale ma farne solo una copia
                self._costo = costo_corrente
            return
        else:
            # tour corrente
            tour = self.tour_per_regione[start_index]
            valore_tour = sum(a.valore_culturale for a in tour.attrazioni)
            # devo fare due casi:
            # caso 1) non prendo il primo, ma vado al secondo
            # se no parto sempre dall'indice 0

            self._ricorsione(start_index + 1, pacchetto_parziale, durata_corrente, costo_corrente, valore_corrente, attrazioni_usate)

            # caso 2) prendo il primo e poi il secondo
            if self.attrazioni_nuove(tour.attrazioni, attrazioni_usate):
                nuove_attrazioni = {a.id for a in tour.attrazioni}  # tutti gli ID in un colpo
                nuova_durata = durata_corrente + tour.durata_giorni
                nuovo_costo = costo_corrente + tour.costo
                nuovo_valore = valore_corrente + valore_tour
                if self.vincoli_soddisfatti(nuova_durata, nuovo_costo):
                    attrazioni_usate |= nuove_attrazioni # aggiungi elementi del set
                    pacchetto_parziale.append(tour)
                    # richiamo la ricorsione per aggiungere gli altri tour
                    self._ricorsione(start_index + 1, pacchetto_parziale, nuova_durata, nuovo_costo, nuovo_valore, attrazioni_usate)
                    # backtracking
                    pacchetto_parziale.pop()
                    attrazioni_usate -= nuove_attrazioni
        print(
            f"Tour: {tour.nome}, costo: {tour.costo}, durata: {tour.durata_giorni}, valore: {sum(a.valore_culturale for a in tour.attrazioni)}")

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno

    def attrazioni_nuove(self, attrazioni: list, attrazioni_usate: set):
        # le attrazioni della regione non si devono ripetere nei vari pacchetti
        for attrazione in attrazioni:
            if attrazione.id in attrazioni_usate:
                return False
        return True

    def vincoli_soddisfatti(self, durata, costo):
        # controllo durata
        if self._max_giorni is not None and durata > self._max_giorni:
            return False
        # controllo vincolo prezzo da non superare
        if self._max_budget is not None and costo > self._max_budget:
            return False
        return True

