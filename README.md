# ACI Contract Parser & Visualizer

![Python](https://img.shields.io/badge/python-v3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Un outil professionnel d'analyse et de visualisation des contrats Cisco ACI (Application Centric Infrastructure) conçu pour l'administration réseau et le troubleshooting.

## 🎯 Vue d'ensemble

Le **ACI Contract Parser** est un analyseur avancé qui permet aux administrateurs réseau de :
- Visualiser les relations de contrats à travers multiple fabrics ACI
- Générer des rapports détaillés des configurations réseau
- Explorer interactivement les relations provider/consumer
- Analyser les EPGs (Endpoint Groups) et leurs dépendances

## 🚀 Fonctionnalités

### ✨ Analyse Complète
- **Rapport Fabric-Wide** : Analyse complète de tous les contrats sur le fabric
- **Mode Interactif** : Consultation interactive des contrats spécifiques
- **Multi-Tenant** : Support des environnements multi-tenant
- **Visualisation des Relations** : Mapping des relations provider/consumer

### 🔧 Capacités Techniques
- Authentification sécurisée via API APIC
- Extraction automatique des VRFs, contrats et EPGs
- Gestion des EPGs internes et externes
- Récupération des informations de sous-réseaux
- Filtrage intelligent des tenants système

## 📋 Prérequis

### Environnement
- **Python** : 3.6 ou supérieur
- **Accès réseau** : Connectivité vers l'APIC Controller
- **Permissions** : Accès en lecture aux APIs ACI

### Dépendances Python
```bash
requests>=2.25.0
urllib3>=1.26.0
```

## 🛠️ Installation

### 1. Cloner le repository
```bash
git clone https://github.com/JFGrenier07/ACI_CONTRACT_PARSER.git
cd ACI_CONTRACT_PARSER
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configuration
Copiez le fichier de configuration d'exemple :
```bash
cp config_example.py config.py
```

Éditez `config.py` avec vos paramètres de connexion ACI :
```python
FABRICS = {
    "PROD": {
        "apic_ip": "10.1.1.1",
        "username": "admin",
        "password": "your_password"
    }
}
```

## 🎮 Instructions d'Exécution

### Mode 1 : Rapport Complet
Génère un rapport détaillé de tous les contrats du fabric :
```bash
python contract_parser.py
```
**Sélectionnez l'option 1** dans le menu interactif

### Mode 2 : Consultation Interactive
Explore des contrats spécifiques :
```bash
python contract_parser.py
```
**Sélectionnez l'option 2** dans le menu interactif

### Exemples d'Utilisation

#### Rapport Fabric-Wide
```bash
$ python contract_parser.py
Sélectionnez le mode d'opération:
1. Générer un rapport complet des contrats
2. Mode consultation interactive
Choix: 1

Sélectionnez le fabric:
1. PROD
2. LAB
3. Tous les fabrics
Choix: 1

[Génération du rapport...]
```

#### Mode Interactif
```bash
$ python contract_parser.py
Choix: 2
Entrez le nom du tenant: Production
Entrez le nom du contrat: Web-DB-Contract
[Affichage des détails du contrat...]
```

## 📊 Sortie du Programme

### Format de Rapport
```
=== RAPPORT DES CONTRATS ACI ===
Fabric: PRODUCTION
Date: 2025-09-20 14:30:15

TENANT: Production
├── VRF: Production-VRF
├── CONTRACT: Web-DB-Contract
│   ├── Provider EPGs:
│   │   └── Database-EPG (10.1.100.0/24)
│   └── Consumer EPGs:
│       └── Web-Server-EPG (10.1.200.0/24)
```

### Informations Extraites
- **Tenants** et leurs VRFs associés
- **Contrats** avec détails provider/consumer
- **EPGs** internes et externes
- **Sous-réseaux** et adressage IP
- **Relations** inter-tenant

## 🏗️ Architecture Technique

### Classes Principales
```python
ACISession()      # Gestion authentification et sessions API
ACIAnalyzer()     # Extraction et analyse des données
ReportGenerator() # Génération des rapports formatés
InteractiveMode() # Interface utilisateur interactive
```

### Flux de Données
1. **Authentification** → Connexion sécurisée à l'APIC
2. **Extraction** → Récupération des données via REST API
3. **Analyse** → Traitement et structuration des informations
4. **Génération** → Production des rapports formatés

## 🔒 Sécurité

- Authentification par token sécurisée
- Gestion des timeouts de session
- Validation des certificats SSL
- Logs de sécurité pour audit

## 🎯 Cas d'Usage Professionnels

### Administration Réseau
- **Audit de conformité** : Vérification des politiques de sécurité
- **Troubleshooting** : Diagnostic rapide des problèmes de connectivité
- **Documentation** : Génération automatique de la documentation réseau

### Migration et Planification
- **Analyse d'impact** : Évaluation des changements avant migration
- **Cartographie** : Visualisation des dépendances applicatives
- **Optimisation** : Identification des contrats redondants

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteur

**Jean-François Grenier**
- GitHub: [@JFGrenier07](https://github.com/JFGrenier07)
- LinkedIn: [Votre profil LinkedIn]

## 🔗 Projets Connexes

- [ACI Tools Collection](https://github.com/JFGrenier07/ACI)
- [Network Automation Portfolio](https://github.com/JFGrenier07)

---
*Développé pour simplifier l'administration des infrastructures Cisco ACI*