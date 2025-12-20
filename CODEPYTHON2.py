import random
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import time
from datetime import datetime, timedelta

class Etage:
    """Représente un étage dans le bâtiment."""
    def __init__(self, numero):
        self.numero = numero

class Appel:
    """Représente un appel d'ascenseur."""
    def __init__(self, origine, destination, heure_appel, poids=1, priorite=1):
        self.origine = origine
        self.destination = destination
        self.heure_appel = heure_appel
        self.poids = poids
        self.priorite = priorite
        self.traite = False
        self.temps_debut_attente = heure_appel
        self.temps_fin_attente = None
        self.ascenseur_assigne = None

class Ascenseur:
    """Représente un ascenseur dans le système."""
    def __init__(self, id, capacite_max=8, vitesse=2.0, accel_decel=1.0, conso_base=0.5):
        self.id = id
        self.position_actuelle = 0  # Étage actuel (numérique)
        self.destination = None
        self.direction = 0  # -1 (descente), 0 (arrêt), 1 (montée)
        self.capacite_max = capacite_max  # Nombre de personnes
        self.charge_actuelle = 0
        self.vitesse = vitesse  # étages par seconde
        self.accel_decel = accel_decel
        self.conso_base = conso_base  # kWh par étage
        self.appels_assignes = []
        self.plan_arrets = []
        self.temps_derniere_maj = 0
        self.distance_parcourue = 0
        self.energie_consommee = 0
        self.en_mouvement = False
        self.temps_arret = 0
    
    def ajouter_appel(self, appel):
        """Ajoute un appel à la liste des appels assignés."""
        if appel not in self.appels_assignes and self.charge_actuelle + appel.poids <= self.capacite_max:
            self.appels_assignes.append(appel)
            self.charge_actuelle += appel.poids
            appel.ascenseur_assigne = self
            self._mettre_a_jour_plan_arrets()
            return True
        return False
    
    def _mettre_a_jour_plan_arrets(self):
        """Met à jour le plan d'arrêts basé sur les appels assignés."""
        etages_a_visiter = set()
        for appel in self.appels_assignes:
            if not appel.traite:
                etages_a_visiter.add(appel.origine.numero)
                etages_a_visiter.add(appel.destination.numero)
        
        if etages_a_visiter:
            self.plan_arrets = sorted(list(etages_a_visiter))
            # Optimiser l'ordre selon la direction
            if self.direction == -1:
                self.plan_arrets.reverse()
    
    def simuler_mouvement(self, temps_simulation):
        """Simule le mouvement de l'ascenseur pendant un temps donné."""
        if not self.plan_arrets:
            return
        
        if self.en_mouvement:
            # Calculer la distance parcourue
            distance = self.vitesse * temps_simulation
            self.distance_parcourue += distance
            
            # Calculer la consommation d'énergie
            facteur_charge = 1 + (self.charge_actuelle / self.capacite_max) * 0.3
            self.energie_consommee += distance * self.conso_base * facteur_charge
            
            # Vérifier si on atteint la destination
            if abs(self.position_actuelle - self.plan_arrets[0]) <= distance:
                self.position_actuelle = self.plan_arrets[0]
                self.plan_arrets.pop(0)
                self.en_mouvement = False
                self.temps_arret = 2.0  # Temps d'arrêt en secondes
                self._traiter_appels_etage()
        else:
            # En arrêt
            if self.temps_arret > 0:
                self.temps_arret -= temps_simulation
            elif self.plan_arrets:
                # Reprendre le mouvement vers le prochain étage
                self.en_mouvement = True
                self.direction = 1 if self.plan_arrets[0] > self.position_actuelle else -1
    
    def _traiter_appels_etage(self):
        """Traite les appels à l'étage actuel."""
        appels_a_supprimer = []
        for appel in self.appels_assignes:
            if appel.origine.numero == self.position_actuelle and not appel.traite:
                # Personne monte dans l'ascenseur
                appel.traite = True
                appel.temps_fin_attente = time.time()
            elif appel.destination.numero == self.position_actuelle and appel.traite:
                # Personne descend de l'ascenseur
                self.charge_actuelle -= appel.poids
                appels_a_supprimer.append(appel)
        
        for appel in appels_a_supprimer:
            self.appels_assignes.remove(appel)

def calculer_detour_reel(ascenseur, appel):
    """Calcule le détour réel que l'ascenseur doit faire."""
    if not ascenseur.plan_arrets:
        # Ascenseur libre - distance directe
        distance_origine = abs(ascenseur.position_actuelle - appel.origine.numero)
        distance_trajet = abs(appel.origine.numero - appel.destination.numero)
        return distance_origine + distance_trajet
    
    # Calculer le chemin actuel
    chemin_actuel = [ascenseur.position_actuelle] + ascenseur.plan_arrets
    distance_actuelle = sum(abs(chemin_actuel[i+1] - chemin_actuel[i]) 
                           for i in range(len(chemin_actuel)-1))
    
    # Calculer le nouveau chemin avec l'appel
    nouveaux_arrets = set(ascenseur.plan_arrets)
    nouveaux_arrets.add(appel.origine.numero)
    nouveaux_arrets.add(appel.destination.numero)
    nouveau_chemin = [ascenseur.position_actuelle] + sorted(list(nouveaux_arrets))
    
    # Optimiser selon la direction
    if ascenseur.direction == -1:
        nouveau_chemin[1:] = sorted(nouveau_chemin[1:], reverse=True)
    
    nouvelle_distance = sum(abs(nouveau_chemin[i+1] - nouveau_chemin[i]) 
                           for i in range(len(nouveau_chemin)-1))
    
    return max(0, nouvelle_distance - distance_actuelle)

def estimer_energie_consommation(ascenseur, appel):
    """Estime la consommation d'énergie pour traiter un appel."""
    distance_origine = abs(ascenseur.position_actuelle - appel.origine.numero)
    distance_trajet = abs(appel.origine.numero - appel.destination.numero)
    
    # Facteur de charge (plus lourd = plus de consommation)
    facteur_charge = ((ascenseur.charge_actuelle + appel.poids) / ascenseur.capacite_max)
    
    # Consommation de base
    energie_deplacement = (distance_origine + distance_trajet) * ascenseur.conso_base * facteur_charge
    
    # Pénalité pour les arrêts (ouverture/fermeture des portes)
    energie_arrets = 2 * 0.2  # 2 arrêts, 0.2 kWh par arrêt
    
    return energie_deplacement + energie_arrets

def estimer_temps_attente(ascenseur, appel):
    """Estime le temps d'attente pour un appel."""
    if not ascenseur.plan_arrets:
        # Ascenseur libre
        distance = abs(ascenseur.position_actuelle - appel.origine.numero)
        return distance / ascenseur.vitesse + ascenseur.accel_decel
    
    # Calculer le temps pour atteindre l'origine de l'appel
    temps_total = 0
    position_courante = ascenseur.position_actuelle
    
    # Temps pour traiter les arrêts existants
    for arret in ascenseur.plan_arrets:
        distance = abs(arret - position_courante)
        temps_total += distance / ascenseur.vitesse + ascenseur.accel_decel + 2.0  # +2s pour l'arrêt
        position_courante = arret
        
        if arret == appel.origine.numero:
            break
    
    # Si l'origine n'est pas dans les arrêts existants
    if appel.origine.numero not in ascenseur.plan_arrets:
        distance_finale = abs(position_courante - appel.origine.numero)
        temps_total += distance_finale / ascenseur.vitesse + ascenseur.accel_decel
    
    return temps_total

def ETAP(appels, ascenseurs, alpha=0.2, beta=0.7, gamma=0.1):
    """Algorithme ETAP ."""
    for appel in appels:
        if appel.traite:
            continue
        
        score_min = float('inf')
        ascenseur_optimal = None
        
        for ascenseur in ascenseurs:
            # Vérifier la capacité
            if ascenseur.charge_actuelle + appel.poids > ascenseur.capacite_max:
                continue
            
            # Calculer les métriques
            detour = calculer_detour_reel(ascenseur, appel)
            energie = estimer_energie_consommation(ascenseur, appel)
            temps = estimer_temps_attente(ascenseur, appel)
            
            # Normalisation adaptative basée sur les valeurs réelles
            max_temps = 120.0  # secondes
            max_energie = 10.0  # kWh
            max_detour = 50.0   # étages
            
            temps_norm = min(temps / max_temps, 1.0)
            energie_norm = min(energie / max_energie, 1.0)
            detour_norm = min(detour / max_detour, 1.0)
            
            # Bonus pour les ascenseurs inactifs
            bonus_inactif = 0.2 if not ascenseur.plan_arrets else 0.0
            
            # Score combiné avec pondération
            score = (alpha * temps_norm + 
                    beta * energie_norm + 
                    gamma * detour_norm - 
                    bonus_inactif)
            
            if score < score_min:
                score_min = score
                ascenseur_optimal = ascenseur
        
        # Assigner l'appel au meilleur ascenseur
        if ascenseur_optimal:
            ascenseur_optimal.ajouter_appel(appel)
            appel.traite = True

class ProfilTraficRealiste:
    """Génère des profils de trafic réalistes"""
    
    @staticmethod
    def bureaux(heure, etages_max=10):
        """Profil de trafic pour immeuble de bureaux"""
        # Définir les intensités selon les heures (plus réaliste)
        if 7 <= heure < 9:
            # Matin: forte montée (arrivées au bureau)
            intensite = 60 + 40 * np.sin((heure - 7) * np.pi / 2)
            return intensite, lambda: (0, random.randint(1, etages_max))
        elif 12 <= heure < 14:
            # Midi: mouvements mixtes (restaurants, réunions)
            intensite = 40 + 20 * np.sin((heure - 12) * np.pi / 2)
            return intensite, lambda: (random.randint(1, etages_max), 
                                     random.choice([0, random.randint(1, etages_max)]))
        elif 17 <= heure < 19:
            # Soir: forte descente (départs)
            intensite = 80 + 50 * np.sin((heure - 17) * np.pi / 2)
            return intensite, lambda: (random.randint(1, etages_max), 0)
        else:
            # Heures creuses
            intensite = 5 + 10 * random.random()
            return intensite, lambda: (random.randint(0, etages_max), 
                                     random.randint(0, etages_max))

class AlgorithmesReference:
    """Implémente les algorithmes de référence."""
    
    @staticmethod
    def FCFS(appels, ascenseurs):
        """First Come First Served"""
        appels_tries = sorted([a for a in appels if not a.traite], 
                             key=lambda x: x.heure_appel)
        
        for appel in appels_tries:
            for ascenseur in ascenseurs:
                if ascenseur.ajouter_appel(appel):
                    appel.traite = True
                    break
    
    @staticmethod
    def SCAN(appels, ascenseurs):
        """Algorithme SCAN """
        for ascenseur in ascenseurs:
            appels_non_traites = [a for a in appels if not a.traite]
            if not appels_non_traites:
                continue
            
            # Déterminer la direction optimale
            if ascenseur.direction == 0:
                # Déterminer la direction selon les appels
                appels_montee = [a for a in appels_non_traites if a.origine.numero > ascenseur.position_actuelle]
                appels_descente = [a for a in appels_non_traites if a.origine.numero < ascenseur.position_actuelle]
                
                if len(appels_montee) >= len(appels_descente):
                    ascenseur.direction = 1
                else:
                    ascenseur.direction = -1
            
            # Trier selon la direction
            if ascenseur.direction >= 0:
                appels_tries = sorted(appels_non_traites, key=lambda a: a.origine.numero)
            else:
                appels_tries = sorted(appels_non_traites, key=lambda a: a.origine.numero, reverse=True)
            
            for appel in appels_tries:
                if ascenseur.ajouter_appel(appel):
                    appel.traite = True
    
    @staticmethod
    def LOOK(appels, ascenseurs):
        """Algorithme LOOK"""
        for ascenseur in ascenseurs:
            appels_non_traites = [a for a in appels if not a.traite]
            if not appels_non_traites:
                continue
            
            position = ascenseur.position_actuelle
            
            # Séparer les appels selon la direction
            if ascenseur.direction >= 0:
                appels_direction = [a for a in appels_non_traites 
                                  if a.origine.numero >= position]
                appels_direction.sort(key=lambda a: a.origine.numero)
            else:
                appels_direction = [a for a in appels_non_traites 
                                  if a.origine.numero <= position]
                appels_direction.sort(key=lambda a: a.origine.numero, reverse=True)
            
            # Si pas d'appels dans cette direction, prendre les autres
            if not appels_direction:
                appels_direction = appels_non_traites
                appels_direction.sort(key=lambda a: abs(a.origine.numero - position))
            
            for appel in appels_direction[:3]:  # Limiter à 3 appels par ascenseur
                if ascenseur.ajouter_appel(appel):
                    appel.traite = True

class SimulateurOptimise:
    """Simulateur optimisé"""
    
    def __init__(self, nb_etages=10, nb_ascenseurs=4):
        self.nb_etages = nb_etages
        self.nb_ascenseurs = nb_ascenseurs
        self.etages = [Etage(i) for i in range(nb_etages + 1)]
        self.reset_systeme()
    
    def reset_systeme(self):
        """Remet le système à zéro."""
        self.ascenseurs = []
        for i in range(self.nb_ascenseurs):
            asc = Ascenseur(
                id=i,
                capacite_max=8,  # personnes
                vitesse=2.0,     # étages/s
                accel_decel=1.0, # secondes
                conso_base=0.5   # kWh/étage
            )
            asc.position_actuelle = random.randint(0, self.nb_etages)
            asc.direction = random.choice([-1, 0, 1])
            self.ascenseurs.append(asc)
    
    def generer_appels_realistes(self, heure, duree_minutes=60):
        """Génère des appels selon le profil réaliste."""
        appels = []
        
        intensite, generateur = ProfilTraficRealiste.bureaux(heure, self.nb_etages)
        
        # Calculer le nombre d'appels basé sur l'intensité
        nb_appels = max(int(intensite * duree_minutes / 60), 1)
        
        for i in range(nb_appels):
            minute = random.randint(0, duree_minutes - 1)
            heure_appel = heure + minute / 60.0
            
            origine_num, dest_num = generateur()
            
            # Éviter les appels identiques
            while origine_num == dest_num:
                origine_num, dest_num = generateur()
            
            # Poids réaliste (1-4 personnes)
            poids = random.randint(1, 4)
            
            appel = Appel(
                origine=self.etages[origine_num],
                destination=self.etages[dest_num],
                heure_appel=heure_appel,
                poids=poids
            )
            appels.append(appel)
        
        return sorted(appels, key=lambda a: a.heure_appel)
    
    def simuler_algorithme_realiste(self, algorithme, appels):
        """Simule un algorithme avec des métriques réalistes."""
        self.reset_systeme()
        
        # Copier les appels
        appels_copie = [Appel(a.origine, a.destination, a.heure_appel, a.poids) 
                       for a in appels]
        
        # Appliquer l'algorithme
        if algorithme == "ETAP":
            ETAP(appels_copie, self.ascenseurs)
        elif algorithme == "FCFS":
            AlgorithmesReference.FCFS(appels_copie, self.ascenseurs)
        elif algorithme == "SCAN":
            AlgorithmesReference.SCAN(appels_copie, self.ascenseurs)
        elif algorithme == "LOOK":
            AlgorithmesReference.LOOK(appels_copie, self.ascenseurs)
        
        # Simulation du mouvement (simplifiée)
        for ascenseur in self.ascenseurs:
            ascenseur.simuler_mouvement(60)  # 1 minute de simulation
        
        # Calculer les métriques
        temps_attente_total = 0
        energie_totale = 0
        appels_traites = 0
        
        for appel in appels_copie:
            if appel.traite and appel.ascenseur_assigne:
                temps = estimer_temps_attente(appel.ascenseur_assigne, appel)
                energie = estimer_energie_consommation(appel.ascenseur_assigne, appel)
                
                temps_attente_total += temps
                energie_totale += energie
                appels_traites += 1
        
        return {
            'temps_attente_moyen': temps_attente_total / max(appels_traites, 1),
            'energie_totale': energie_totale,
            'appels_traites': appels_traites,
            'taux_traitement': appels_traites / len(appels_copie) * 100
        }

def comparer_algorithmes():
    """Compare les algorithmes avec des paramètres réalistes."""
    simulateur = SimulateurOptimise()
    algorithmes = ["FCFS", "SCAN", "LOOK", "ETAP"]
    resultats = {}
    
    print("Simulation comparative")
    print("=" * 50)
    
    charges = [20, 40, 60, 80, 100]
    
    for charge in charges:
        print(f"Charge {charge}%...")
        resultats[charge] = {}
        
        for algo in algorithmes:
            temps_attentes = []
            energies = []
            # Plusieurs simulations pour la robustesse
            for _ in range(1000):
                appels_jour = []
                
                # Générer des appels pour différentes heures
                for heure in [8, 12, 17]:  # Heures de pointe
                    appels_heure = simulateur.generer_appels_realistes(heure, 60)
                    # Ajuster selon la charge
                    nb_appels = int(len(appels_heure) * charge / 100)
                    if nb_appels > 0:
                        appels_jour.extend(random.sample(appels_heure, 
                                                       min(nb_appels, len(appels_heure))))
                
                if appels_jour:
                    resultats_sim = simulateur.simuler_algorithme_realiste(algo, appels_jour)
                    temps_attentes.append(resultats_sim['temps_attente_moyen'])
                    energies.append(resultats_sim['energie_totale'])
            
            if temps_attentes and energies:
                resultats[charge][algo] = {
                    'temps_attente': np.mean(temps_attentes),
                    'energie': np.mean(energies),
                    'ecart_type': np.std(temps_attentes)
                }
            else:
                resultats[charge][algo] = {
                    'temps_attente': 0,
                    'energie': 0,
                    'ecart_type': 0
                }
    
    return resultats

def generer_graphiques(resultats):
    """Génère les graphiques."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    charges = sorted(resultats.keys())
    algorithmes = ["FCFS", "SCAN", "LOOK", "ETAP"]
    couleurs = ['red', 'blue', 'green', 'purple']
    
    # Graphique 1: Temps d'attente en fct de Charge
    for i, algo in enumerate(algorithmes):
        temps_attente = [resultats[c][algo]['temps_attente'] for c in charges]
        ax1.plot(charges, temps_attente, marker='o', color=couleurs[i], 
                label=algo, linewidth=2, markersize=6)
    
    ax1.set_xlabel('Charge du système (%)', fontsize=12)
    ax1.set_ylabel('Temps d\'attente moyen (s)', fontsize=12)
    ax1.set_title('Temps d\'attente en fonction de la charge', fontsize=14)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, None)
    
    # Graphique 2: Consommation énergétique
    energies_moyennes = []
    for algo in algorithmes:
        energie_moy = np.mean([resultats[c][algo]['energie'] for c in charges])
        energies_moyennes.append(energie_moy)
    
    bars = ax2.bar(algorithmes, energies_moyennes, color=couleurs, alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Consommation énergétique (kWh/jour)', fontsize=12)
    ax2.set_title('Comparaison de la consommation énergétique', fontsize=14)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Ajouter les valeurs sur les barres
    for bar, energie in zip(bars, energies_moyennes):
        if energie > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{energie:.1f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('comparaison_algorithmes.png', dpi=300, bbox_inches='tight')
    plt.show()

def simulation_24h():
    """Simulation 24h."""
    simulateur = SimulateurOptimise()
    resultats_24h = {"LOOK": [], "ETAP": []}
    
    print("Simulation 24h ...")
    
    for heure in range(24):
        print(f"Heure {heure:02d}:00")
        
        for algo in ["LOOK", "ETAP"]:
            appels = simulateur.generer_appels_realistes(heure, 60)
            if appels:
                resultats = simulateur.simuler_algorithme_realiste(algo, appels)
                temps_attente = resultats['temps_attente_moyen']
                resultats_24h[algo].append(temps_attente)
            else:
                resultats_24h[algo].append(0)
    
    return resultats_24h

def generer_graphique_24h(resultats_24h):
    """Génère le graphique 24h."""
    plt.figure(figsize=(12, 6))
    heures = range(24)
    
    plt.plot(heures, resultats_24h["LOOK"], marker='o', 
             label='LOOK', linewidth=2, color='green', markersize=5)
    plt.plot(heures, resultats_24h["ETAP"], marker='s', 
             label='ETAP', linewidth=2, color='purple', markersize=5)
    
    plt.xlabel('Heure de la journée', fontsize=12)
    plt.ylabel('Temps d\'attente moyen (s)', fontsize=12)
    plt.title('Évolution du temps d\'attente sur 24h', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xticks(range(0, 25, 4))
    
    # Ajouter les zones de pointe
    plt.axvspan(7, 9, alpha=0.2, color='red', label='Pointe matin')
    plt.axvspan(12, 14, alpha=0.2, color='orange', label='Pointe midi')
    plt.axvspan(17, 19, alpha=0.2, color='red', label='Pointe soir')
    
    plt.tight_layout()
    plt.savefig('temps_attente_24h.png', dpi=300, bbox_inches='tight')
    plt.show()

def afficher_statistiques(resultats):
    """Affiche les statistiques ."""
    print("\n" + "="*70)
    print("="*70)
    
    print(f"{'Algorithme':<12} {'Temps (s)':<12} {'Énergie (kWh)':<15} {'Amélioration':<20}")
    print("-" * 70)
    
    # Référence FCFS à charge 100%
    ref_temps = resultats[100]["FCFS"]["temps_attente"]
    ref_energie = resultats[100]["FCFS"]["energie"]
    
    for algo in ["FCFS", "SCAN", "LOOK", "ETAP"]:
        temps = resultats[100][algo]["temps_attente"]
        energie = resultats[100][algo]["energie"]
        
        amelioration_temps = ((ref_temps - temps) / ref_temps) * 100 if ref_temps > 0 else 0
        amelioration_energie = ((ref_energie - energie) / ref_energie) * 100 if ref_energie > 0 else 0
        
        print(f"{algo:<12} {temps:<12.1f} {energie:<15.1f} "
              f"T:{amelioration_temps:+5.1f}% E:{amelioration_energie:+5.1f}%")
    
    print("\n" + "="*70)
if __name__ == "__main__":
    print("Lancement de la simulation complète du système d'ascenseurs...")
    print("Cette simulation peut prendre quelques minutes...\n")
    
    try:
        # 1. Comparaison des algorithmes
        resultats = comparer_algorithmes()
        
        # 2. Génération des graphiques pour la comparaison par charge
        generer_graphiques(resultats)
        
        # 3. Simulation sur 24h
        print("\nSimulation d'une journée complète...")
        resultats_24h = simulation_24h()
        
        # 4. Génération du graphique 24h (fonction séparée)
        generer_graphique_24h(resultats_24h)
        
        # 5. Affichage des statistiques
        afficher_statistiques(resultats)
        
        print("\nSimulation terminée avec succès!")
        print("Les graphiques ont été sauvegardés :")
        print("- 'comparaison_algorithmes.png' (comparaison par charge)")
        print("- 'temps_attente_24h.png' (évolution sur 24h)")
        
    except Exception as e:
        print(f"Erreur lors de la simulation: {e}")
        import traceback
        traceback.print_exc()