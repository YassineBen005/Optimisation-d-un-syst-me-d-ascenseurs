# Optimisation d'un système d'ascenseurs par réseaux de Petri

**TIPE — BEN YOUSSEF Yassine, Juin 2025**

Simulation et comparaison d'algorithmes d'ordonnancement pour un système multi-ascenseurs, modélisé à l'aide des réseaux de Petri colorés. L'objectif est de minimiser simultanément le **temps d'attente** des usagers et la **consommation énergétique**.

---

## Problématique

> Comment optimiser le fonctionnement d'un système d'ascenseurs pour minimiser le temps d'attente des usagers tout en réduisant la consommation énergétique ?

---

## Algorithmes comparés

| Algorithme | Description |
|------------|-------------|
| **FCFS** | First Come First Served — traitement dans l'ordre d'arrivée |
| **SCAN** | Balayage continu dans une direction puis retournement |
| **LOOK** | Variante de SCAN — retournement dès qu'il n'y a plus de requêtes |
| **ETAP** | Algorithme original — score combiné temps + énergie + détour |

### Fonction de score ETAP

```
score = α · temps + β · énergie + γ · détour
```

Avec les paramètres par défaut : `α = 0.2`, `β = 0.7`, `γ = 0.1`

---

## Structure du code

```
CODEPYTHON2.py
│
├── class Etage              # Représente un étage du bâtiment
├── class Appel              # Requête d'ascenseur (origine, destination, heure, poids)
├── class Ascenseur          # État d'un ascenseur (position, direction, charge, énergie)
│     ├── ajouter_appel()
│     ├── simuler_mouvement()
│     └── _traiter_appels_etage()
│
├── class ProfilTraficRealiste   # Génère des appels réalistes selon l'heure
│     ├── bureaux()              # Pics matin (arrivées) et soir (départs)
│     └── residentiels()         # Flux inversé, distribution étalée
│
├── class AlgorithmesReference   # Algorithmes de référence
│     ├── FCFS()
│     ├── SCAN()
│     └── LOOK()
│
├── class SimulateurOptimise     # Moteur de simulation principal
│     ├── generer_appels_realistes()
│     ├── simuler_algorithme_realiste()
│     └── comparer_algorithmes()
│
├── def ETAP()                   # Algorithme d'optimisation original
├── def comparer_algorithmes()   # Benchmark des 4 algorithmes
├── def simulation_24h()         # Simulation sur une journée complète
└── def generer_graphiques()     # Export des graphiques matplotlib
```

---

## Paramètres de simulation

| Paramètre | Valeur |
|-----------|--------|
| Nombre d'étages | 10 |
| Nombre d'ascenseurs | 4 |
| Capacité par ascenseur | 8 personnes |
| Vitesse | 2 étages/s |
| Consommation de base | 0.5 kWh/étage |
| Durée de simulation | 24 heures |
| Niveaux de charge testés | 20%, 40%, 60%, 80%, 100% |

---

## Modèle énergétique

```
E_total = Σ (E_déplacement,i + E_arrêt,i)

E_déplacement = distance × conso_base × facteur_charge
E_arrêt       = 2 × 0.2 kWh   (ouverture + fermeture des portes)

facteur_charge = 1 + (charge_actuelle / capacité_max) × 0.3
```

---

## Exécution : 

```bash
pip install numpy matplotlib
python CODEPYTHON2.py
```

Le script exécute automatiquement :
1. La comparaison des 4 algorithmes sur 5 niveaux de charge (1000 simulations par point)
2. La simulation sur 24 heures (LOOK vs ETAP)
3. La génération de deux graphiques :
   - `comparaison_algorithmes.png` — temps d'attente et énergie en fonction de la charge
   - `temps_attente_24h.png` — évolution sur la journée avec zones de pointe

---

## Résultats obtenus

### Temps d'attente (vs LOOK)
- Réduction de **25%** en moyenne
- **80%** des usagers attendent moins de 30 secondes avec ETAP
- Avantage maintenu à tous les niveaux de charge

### Consommation énergétique
- Réduction de **38%** par rapport à FCFS
- Réduction de **20%** par rapport à LOOK

### Distribution des temps d'attente

| Tranche | LOOK | ETAP |
|---------|------|------|
| < 15 s  | 18%  | 32%  |
| 15–30 s | 45%  | 48%  |
| 30–45 s | 25%  | 15%  |
| > 45 s  | 12%  |  5%  |

---

## Perspectives

- Prédiction de la demande à partir de l'historique de trafic
- Intégration d'un algorithme d'apprentissage automatique (reinforcement learning)
- Extension à des bâtiments mixtes (bureaux + résidentiel)

---

