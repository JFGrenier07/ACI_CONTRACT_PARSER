"""
Configuration d'exemple pour ACI Contract Parser
Copiez ce fichier vers config.py et adaptez vos paramètres
"""

# Configuration des Fabrics ACI
FABRICS = {
    "PRODUCTION": {
        "apic_ip": "10.1.1.1",
        "username": "admin",
        "password": "your_secure_password",
        "verify_ssl": False,
        "timeout": 30
    },
    "STAGING": {
        "apic_ip": "10.2.2.1",
        "username": "admin",
        "password": "your_secure_password",
        "verify_ssl": False,
        "timeout": 30
    },
    "LAB": {
        "apic_ip": "192.168.1.100",
        "username": "lab_admin",
        "password": "lab_password",
        "verify_ssl": False,
        "timeout": 15
    }
}

# Tenants à exclure du rapport
EXCLUDED_TENANTS = ["mgmt", "infra", "common"]

# Configuration de sortie
OUTPUT_CONFIG = {
    "format": "text",  # text, json, csv
    "include_subnets": True,
    "include_external_epgs": True,
    "verbose": False
}

# Configuration des logs
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "file": "aci_parser.log",
    "max_size": "10MB",
    "backup_count": 5
}