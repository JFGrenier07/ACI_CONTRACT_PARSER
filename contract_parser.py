#!/usr/bin/env python3
"""
ACI Contract Visualizer - Version Finale Optimisée

Script pour visualiser et analyser les contrats ACI via l'API REST native.
Offre deux modes :
1. Génération de rapports complets par fabric
2. Consultation interactive des contrats par tenant

Author: JFG
Version: 2.2 (Finale Optimisée)
Compatible: Python 3.6+
Dependencies: requests, urllib3
"""

import json
import getpass
import requests
import urllib3
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
FABRICS = [
    {"name": "Simulateur", "ip": "192.168.0.245"},
    {"name": "DC2-FabricB", "ip": "10.2.2.10"},
    {"name": "Lab-Fabric", "ip": "192.168.100.50"},
]

EXCLUDED_TENANTS = {"mgmt", "infra", "common"}
REQUEST_TIMEOUT = 30

# Configuration d'affichage
REPORT_WIDTH = 140
PROVIDER_COLUMN_WIDTH = 65
CONSUMER_COLUMN_WIDTH = 65


class ACISession:
    """Gestionnaire de session ACI avec authentification et requêtes API."""
    
    def __init__(self, apic_url: str, username: str, password: str):
        self.apic_url = apic_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.cookies = None
        
    def login(self) -> bool:
        """Authentification sur l'APIC."""
        login_url = f"{self.apic_url}/api/aaaLogin.json"
        payload = {
            "aaaUser": {
                "attributes": {
                    "name": self.username,
                    "pwd": self.password
                }
            }
        }
        
        try:
            response = self.session.post(login_url, json=payload, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                self.cookies = response.cookies
                return True
            else:
                print(f"❌ Erreur d'authentification: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def get(self, url_path: str) -> Optional[Dict]:
        """Requête GET sur l'API ACI."""
        url = f"{self.apic_url}/api{url_path}"
        try:
            response = self.session.get(url, cookies=self.cookies, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erreur API: {response.status_code} - {url}")
                return None
        except Exception as e:
            print(f"❌ Erreur requête: {e}")
            return None


class ACIAnalyzer:
    """Analyseur de configuration ACI pour extraire les informations des contrats."""
    
    def __init__(self, session: ACISession):
        self.session = session
    
    def get_tenants(self) -> List[Dict]:
        """Récupère la liste des tenants avec leurs VRFs."""
        data = self.session.get("/node/class/fvTenant.json")
        if not data:
            return []
        
        tenants = []
        for item in data.get("imdata", []):
            tenant_name = item["fvTenant"]["attributes"]["name"]
            if tenant_name not in EXCLUDED_TENANTS:
                tenant_dn = item["fvTenant"]["attributes"]["dn"]
                vrfs = self._get_tenant_vrfs(tenant_dn)
                tenants.append({
                    "name": tenant_name,
                    "dn": tenant_dn,
                    "vrfs": vrfs
                })
        return sorted(tenants, key=lambda t: t["name"])
    
    def _get_tenant_vrfs(self, tenant_dn: str) -> List[Dict]:
        """Récupère les VRFs d'un tenant."""
        data = self.session.get(f"/node/mo/{tenant_dn}.json?query-target=children&target-subtree-class=fvCtx")
        if not data:
            return []
        
        return [
            {
                "name": item["fvCtx"]["attributes"]["name"],
                "dn": item["fvCtx"]["attributes"]["dn"]
            }
            for item in data.get("imdata", [])
        ]
    
    def get_contracts(self, tenant_dn: str) -> List[Dict]:
        """Récupère les contrats d'un tenant."""
        data = self.session.get(f"/node/mo/{tenant_dn}.json?query-target=children&target-subtree-class=vzBrCP")
        if not data:
            return []
        
        return [
            {
                "name": item["vzBrCP"]["attributes"]["name"],
                "dn": item["vzBrCP"]["attributes"]["dn"]
            }
            for item in data.get("imdata", [])
        ]
    
    def get_contract_relationships(self, contract_dn: str) -> Tuple[List[Dict], List[Dict]]:
        """Récupère les relations provider/consumer d'un contrat."""
        providers, consumers = [], []
        
        data = self.session.get(f"/node/mo/{contract_dn}.json?query-target=children&target-subtree-class=vzRtProv,vzRtCons")
        if not data:
            return providers, consumers
        
        for item in data.get("imdata", []):
            if "vzRtProv" in item:
                target_dn = item["vzRtProv"]["attributes"]["tDn"]
                epg_info = self._get_epg_info(target_dn)
                if epg_info:
                    providers.append(epg_info)
            elif "vzRtCons" in item:
                target_dn = item["vzRtCons"]["attributes"]["tDn"]
                epg_info = self._get_epg_info(target_dn)
                if epg_info:
                    consumers.append(epg_info)
        
        return providers, consumers
    
    def _get_epg_info(self, epg_dn: str) -> Optional[Dict]:
        """Récupère les informations d'un EPG (interne ou externe)."""
        if "/out-" in epg_dn:
            return self._get_external_epg_info(epg_dn)
        else:
            return self._get_internal_epg_info(epg_dn)
    
    def _get_external_epg_info(self, epg_dn: str) -> Optional[Dict]:
        """Récupère les informations d'un EPG externe."""
        data = self.session.get(f"/node/mo/{epg_dn}.json")
        if not data or not data.get("imdata"):
            return None
            
        epg_data = data["imdata"][0]["l3extInstP"]["attributes"]
        subnets = self._get_external_subnets(epg_dn)
        
        return {
            "name": epg_data["name"],
            "type": "external",
            "dn": epg_dn,
            "subnets": subnets
        }
    
    def _get_internal_epg_info(self, epg_dn: str) -> Optional[Dict]:
        """Récupère les informations d'un EPG interne."""
        data = self.session.get(f"/node/mo/{epg_dn}.json")
        if not data or not data.get("imdata"):
            return None
            
        epg_data = data["imdata"][0]["fvAEPg"]["attributes"]
        subnets = self._get_internal_subnets(epg_dn)
        
        return {
            "name": epg_data["name"],
            "type": "internal",
            "dn": epg_dn,
            "subnets": subnets
        }
    
    def _get_internal_subnets(self, epg_dn: str) -> List[Dict]:
        """Récupère les subnets d'un EPG interne via son Bridge Domain."""
        # Récupérer le Bridge Domain
        data = self.session.get(f"/node/mo/{epg_dn}.json?query-target=children&target-subtree-class=fvRsBd")
        if not data or not data.get("imdata"):
            return []
        
        bd_dn = data["imdata"][0]["fvRsBd"]["attributes"]["tDn"]
        
        # Récupérer les subnets du Bridge Domain
        subnet_data = self.session.get(f"/node/mo/{bd_dn}.json?query-target=children&target-subtree-class=fvSubnet")
        if not subnet_data or not subnet_data.get("imdata"):
            return []
        
        return [
            {
                "ip": item["fvSubnet"]["attributes"]["ip"],
                "description": item["fvSubnet"]["attributes"].get("descr", ""),
                "type": "internal"
            }
            for item in subnet_data["imdata"]
        ]
    
    def _get_external_subnets(self, ext_epg_dn: str) -> List[Dict]:
        """Récupère les subnets d'un EPG externe."""
        data = self.session.get(f"/node/mo/{ext_epg_dn}.json?query-target=children&target-subtree-class=l3extSubnet")
        if not data or not data.get("imdata"):
            return []
        
        subnets = []
        for item in data["imdata"]:
            subnet_attrs = item["l3extSubnet"]["attributes"]
            scope = subnet_attrs.get("scope", "")
            subnet_type = "exp" if "export-rtctrl" in scope else "ext"
            
            subnets.append({
                "ip": subnet_attrs["ip"],
                "description": subnet_attrs.get("name", ""),  # Utiliser 'name' pour les external EPG
                "type": subnet_type
            })
        
        return subnets


class ReportGenerator:
    """Générateur de rapports ACI optimisé."""
    
    def __init__(self, analyzer: ACIAnalyzer, fabric_name: str):
        self.analyzer = analyzer
        self.fabric_name = fabric_name
    
    def generate_complete_report(self):
        """Génère un rapport complet optimisé."""
        filename = f"rapport_complet_{self.fabric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        print("🔍 Collecte des données en cours...")
        
        tenants = self.analyzer.get_tenants()
        stats = {"contracts": 0, "providers": 0, "consumers": 0}
        
        with open(filename, "w", encoding="utf-8") as f:
            self._write_header(f)
            
            for tenant in tenants:
                contracts = self.analyzer.get_contracts(tenant["dn"])
                if not contracts:
                    continue
                
                stats["contracts"] += len(contracts)
                self._write_tenant_section(f, tenant, contracts, stats)
            
            self._write_summary(f, tenants, stats)
        
        print(f"\n✅ Rapport complet généré : {filename}")
        print(f"📊 Total de {stats['contracts']} contrats analysés.")
    
    def _write_header(self, f):
        """Écrit l'en-tête du rapport."""
        f.write("=" * REPORT_WIDTH + "\n")
        f.write(f"RAPPORT ACI CONTRACT VISUALIZER - FABRIC: {self.fabric_name.upper()}\n")
        f.write(f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
        f.write("=" * REPORT_WIDTH + "\n\n")
    
    def _write_tenant_section(self, f, tenant: Dict, contracts: List[Dict], stats: Dict):
        """Écrit la section d'un tenant dans le rapport."""
        # En-tête Tenant avec VRFs alignés avec la colonne CONSUMER
        vrf_list = ", ".join([vrf['name'] for vrf in tenant['vrfs']]) if tenant['vrfs'] else "Aucun VRF"
        tenant_part = f"TENANT: {tenant['name']}"
        vrf_part = f"VRFs: {vrf_list}"
        
        # Calculer l'espacement pour aligner VRFs avec CONSUMER
        vrf_position = PROVIDER_COLUMN_WIDTH + 1
        spacing = vrf_position - len(tenant_part)
        if spacing < 1:
            spacing = 1
        
        f.write(f"{tenant_part}{' ' * spacing}{vrf_part}\n")
        f.write("━" * REPORT_WIDTH + "\n\n")
        
        for contract in sorted(contracts, key=lambda c: c["name"]):
            providers, consumers = self.analyzer.get_contract_relationships(contract["dn"])
            
            if not providers and not consumers:
                continue
            
            stats["providers"] += len(providers)
            stats["consumers"] += len(consumers)
            
            self._write_contract_details(f, contract, providers, consumers)
    
    def _write_contract_details(self, f, contract: Dict, providers: List[Dict], consumers: List[Dict]):
        """Écrit les détails d'un contrat avec format optimisé."""
        f.write(f"CONTRACT: {contract['name']}\n")
        
        # En-tête des colonnes
        provider_header = f"{'PROVIDERS':<{PROVIDER_COLUMN_WIDTH}}"
        consumer_header = f"CONSUMERS"
        f.write(f"  {provider_header} {consumer_header}\n")
        
        # Ligne de séparation
        separator_line = "─" * PROVIDER_COLUMN_WIDTH + " " + "─" * CONSUMER_COLUMN_WIDTH
        f.write(f"  {separator_line}\n")
        
        provider_lines = self._build_epg_lines(providers)
        consumer_lines = self._build_epg_lines(consumers)
        
        # Afficher les colonnes côte à côte
        max_lines = max(len(provider_lines), len(consumer_lines))
        
        for i in range(max_lines):
            prov_content = self._format_column_content(provider_lines, i, PROVIDER_COLUMN_WIDTH)
            cons_content = consumer_lines[i] if i < len(consumer_lines) else ""
            
            f.write(f"  {prov_content} {cons_content}\n")
        
        f.write("\n")
    
    def _build_epg_lines(self, epgs: List[Dict]) -> List[str]:
        """Construit les lignes pour afficher les EPGs avec troncature intelligente."""
        lines = []
        
        for epg_idx, epg in enumerate(epgs):
            epg_type = "Ext-EPG" if epg["type"] == "external" else "EPG"
            lines.append(f"{epg_type}: {epg['name']}")
            
            if epg["subnets"]:
                for subnet_idx, subnet in enumerate(epg["subnets"]):
                    if epg["type"] == "external":
                        type_suffix = f" ({subnet['type']})"
                        if subnet['description']:
                            # Calculer l'espace disponible pour external EPG
                            available_space = PROVIDER_COLUMN_WIDTH - 6 - len(subnet['ip']) - len(type_suffix) - 2
                            if len(subnet['description']) > available_space:
                                desc_part = f" {subnet['description'][:available_space-3]}..."
                            else:
                                desc_part = f" {subnet['description']}"
                        else:
                            desc_part = ""
                        subnet_display = f"{subnet['ip']}{type_suffix}{desc_part}"
                    else:
                        # Pour les EPG internes
                        if subnet['description']:
                            # Calculer l'espace disponible pour EPG interne
                            available_space = PROVIDER_COLUMN_WIDTH - 6 - len(subnet['ip']) - 2
                            if len(subnet['description']) > available_space:
                                desc_part = f" {subnet['description'][:available_space-3]}..."
                            else:
                                desc_part = f" {subnet['description']}"
                        else:
                            desc_part = ""
                        subnet_display = f"{subnet['ip']}{desc_part}"
                    
                    prefix = "  └─" if subnet_idx == len(epg["subnets"]) - 1 else "  ├─"
                    lines.append(f"{prefix} {subnet_display}")
            else:
                lines.append("  └─ Aucun subnet")
            
            # Ligne vide entre EPGs (sauf pour le dernier)
            if epg_idx < len(epgs) - 1:
                lines.append("")
        
        return lines
    
    def _format_column_content(self, lines: List[str], index: int, width: int) -> str:
        """Formate le contenu d'une colonne avec la largeur spécifiée."""
        if index < len(lines):
            content = lines[index]
            if len(content) > width:
                content = content[:width-3] + "..."
            return f"{content:<{width}}"
        else:
            return " " * width
    
    def _write_summary(self, f, tenants: List[Dict], stats: Dict):
        """Écrit le résumé final du rapport."""
        f.write("━" * REPORT_WIDTH + "\n\n")
        f.write("═" * REPORT_WIDTH + "\n")
        f.write("RÉSUMÉ FINAL\n")
        f.write("═" * REPORT_WIDTH + "\n")
        f.write(f"Total Tenants analysés: {len([t for t in tenants if self.analyzer.get_contracts(t['dn'])])}\n")
        f.write(f"Total Contrats: {stats['contracts']}\n")
        f.write(f"Total EPGs Providers: {stats['providers']}\n")
        f.write(f"Total EPGs Consumers: {stats['consumers']}\n")
        f.write(f"Fabric: {self.fabric_name}\n")
        f.write("═" * REPORT_WIDTH + "\n")


class InteractiveMode:
    """Mode consultation interactive."""
    
    def __init__(self, analyzer: ACIAnalyzer):
        self.analyzer = analyzer
    
    def run(self):
        """Lance le mode consultation interactive."""
        while True:
            tenants = self.analyzer.get_tenants()
            if not tenants:
                print("❌ Aucun tenant disponible.")
                break

            tenant = self._select_tenant(tenants)
            if not tenant:
                break
                
            contracts = self.analyzer.get_contracts(tenant["dn"])
            if not contracts:
                choice = self._handle_no_contracts(tenant["name"])
                if choice == 1:
                    continue
                elif choice == 2:
                    break
                else:
                    return

            contract = self._select_contract(contracts)
            if not contract:
                continue
                
            self._display_contract(contract, tenant["name"])
            
            if not self._ask_continue():
                break
    
    def _select_tenant(self, tenants: List[Dict]) -> Optional[Dict]:
        """Sélectionne un tenant."""
        print("\n=== Sélectionnez un tenant ===")
        for idx, t in enumerate(tenants, 1):
            print(f"{idx}. {t['name']}")
            
        while True:
            try:
                choice = int(input("Numéro : ").strip())
                if 1 <= choice <= len(tenants):
                    return tenants[choice - 1]
            except ValueError:
                pass
            print("❌ Choix invalide.")
    
    def _select_contract(self, contracts: List[Dict]) -> Optional[Dict]:
        """Sélectionne un contrat."""
        print("\n=== Sélectionnez un contrat ===")
        contracts_sorted = sorted(contracts, key=lambda x: x["name"])
        for idx, c in enumerate(contracts_sorted, 1):
            print(f"{idx}. {c['name']}")
            
        while True:
            try:
                choice = int(input("Numéro : ").strip())
                if 1 <= choice <= len(contracts):
                    return contracts_sorted[choice - 1]
            except ValueError:
                pass
            print("❌ Choix invalide.")
    
    def _display_contract(self, contract: Dict, tenant_name: str):
        """Affiche les détails d'un contrat."""
        print(f"\nTenant: {tenant_name}  |  Contrat: {contract['name']}\n")
        
        providers, consumers = self.analyzer.get_contract_relationships(contract['dn'])
        
        if providers:
            print("Providers:")
            self._display_epgs(providers, "├──")
        if consumers:
            print("Consumers:")
            self._display_epgs(consumers, "└──")
        if not providers and not consumers:
            print("❌ Aucun EPG provider/consumer lié.")
    
    def _display_epgs(self, epgs: List[Dict], prefix: str):
        """Affiche les EPGs avec troncature pour le mode interactif."""
        for epg in epgs:
            epg_type = "Ext-EPG" if epg["type"] == "external" else "EPG"
            print(f"{prefix} {epg_type}-{epg['name']}")
            for subnet in epg["subnets"]:
                if epg["type"] == "external":
                    type_suffix = f" ({subnet['type']})"
                    if subnet['description']:
                        # Limiter à 50 caractères pour le mode interactif
                        if len(subnet['description']) > 50:
                            desc_part = f" {subnet['description'][:47]}..."
                        else:
                            desc_part = f" {subnet['description']}"
                    else:
                        desc_part = ""
                    subnet_display = f"{subnet['ip']}{type_suffix}{desc_part}"
                else:
                    if subnet['description']:
                        # Limiter à 60 caractères pour les EPG internes
                        if len(subnet['description']) > 60:
                            desc_part = f" {subnet['description'][:57]}..."
                        else:
                            desc_part = f" {subnet['description']}"
                    else:
                        desc_part = ""
                    subnet_display = f"{subnet['ip']}{desc_part}"
                
                print(f"    ├── {subnet_display}")
    
    def _handle_no_contracts(self, tenant_name: str) -> int:
        """Gère le cas sans contrats."""
        print(f"\n⚠️  Aucun contrat trouvé dans le tenant '{tenant_name}'.")
        print("Options disponibles:")
        print("1. Sélectionner un autre tenant")
        print("2. Revenir au menu principal")
        print("3. Quitter")
        
        while True:
            try:
                choice = int(input("\nVotre choix : ").strip())
                if choice in [1, 2, 3]:
                    return choice
            except ValueError:
                pass
            print("❌ Choix invalide. Veuillez entrer 1, 2 ou 3.")
    
    def _ask_continue(self) -> bool:
        """Demande si continuer."""
        while True:
            ans = input("\nVoulez-vous consulter un autre contrat/tenant ? (oui/non) : ").strip().lower()
            if ans in {"o", "oui", "y", "yes"}:
                return True
            if ans in {"n", "non", "no"}:
                return False
            print("❌ Répondez par oui/non.")


def choose_fabric() -> Dict:
    """Sélection du fabric."""
    print("\n=== Sélectionnez un fabric ===")
    for idx, f in enumerate(FABRICS, 1):
        print(f"{idx}. {f['name']} ({f['ip']})")
    while True:
        try:
            choice = int(input("\nEntrez le numéro du fabric : ").strip())
            if 1 <= choice <= len(FABRICS):
                return FABRICS[choice - 1]
        except ValueError:
            pass
        print("❌ Choix invalide.")


def main():
    """Fonction principale."""
    print("🚀 ACI Contract Visualizer (Version Finale Optimisée)")
    
    while True:
        print("\n=== Menu Principal ===")
        print("1. Rapport complet des contrats par fabric")
        print("2. Consultation interactive")
        print("3. Quitter")
        
        while True:
            try:
                mode = int(input("\nVotre choix : ").strip())
                if mode in [1, 2, 3]:
                    break
            except ValueError:
                pass
            print("❌ Choix invalide.")
        
        if mode == 3:
            print("👋 Au revoir.")
            break
        
        # Sélection du fabric et authentification
        fabric = choose_fabric()
        username = input("Username : ").strip()
        password = getpass.getpass("Password : ")
        
        session = ACISession(f"https://{fabric['ip']}", username, password)
        if not session.login():
            continue
        
        print("✅ Connexion réussie!")
        
        # Initialisation de l'analyseur
        analyzer = ACIAnalyzer(session)
        
        if mode == 1:
            # Mode rapport complet
            generator = ReportGenerator(analyzer, fabric["name"])
            generator.generate_complete_report()
        else:
            # Mode consultation interactive
            interactive = InteractiveMode(analyzer)
            interactive.run()


if __name__ == "__main__":
    main()
