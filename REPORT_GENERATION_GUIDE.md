# Guide de Génération de Rapports Word

## 📝 Vue d'ensemble

Le générateur de rapports permet de créer automatiquement des documents Word (.docx) professionnels à partir des résultats d'analyse des besoins et des cas d'usage IA.

## 🎯 Fonctionnalités

### Format du rapport généré

Le rapport suit scrupuleusement le template du fichier `1107-V0 Cas d'usages IA - Cousin.docx` :

- **Logo Aiko** en haut à droite (si disponible)
- **Section 1 : LES BESOINS IDENTIFIÉS DE [COMPANY_NAME]**
  - Besoins organisés par thème
  - Citations pour chaque besoin
  - Emojis 🔹 pour les sous-titres
  
- **Section 2 : LES CAS D'USAGES IA PRIORITAIRES**
  - Texte d'introduction personnalisé avec le nom de l'entreprise
  - **Famille "Quick Wins"** : Automatisation & assistance intelligente
  - **Famille "Structuration IA à moyen et long terme"** : Scalabilité & qualité prédictive
  - Pour chaque cas d'usage :
    - Titre
    - IA utilisée (en italique)
    - Description détaillée

### Nom du fichier généré

Le fichier est automatiquement nommé selon le format :
```
{JJMM}-V0-Cas_d_usages_IA-{company_name}.docx
```

**Exemple** : `1410-V0-Cas_d_usages_IA-Cousin_Surgery.docx`

## 🚀 Utilisation

### 1. Via l'interface Streamlit

1. Lancez l'application Streamlit :
   ```bash
   cd /home/addeche/aiko/aikoGPT
   uv run streamlit run app/app.py
   ```

2. Complétez le workflow complet :
   - Zone 1 : Upload des fichiers Excel (ateliers)
   - Zone 2 : Upload des fichiers PDF (transcriptions)
   - Zone 3 : Saisie du nom de l'entreprise
   - Lancez l'analyse et validez les besoins
   - Validez les cas d'usage

3. Une fois les cas d'usage validés, cliquez sur le bouton :
   **📄 Générer le rapport Word**

4. Le rapport sera automatiquement :
   - Généré dans `/home/addeche/aiko/aikoGPT/outputs/`
   - Proposé en téléchargement direct

### 2. Via un script Python

```python
from utils.report_generator import ReportGenerator

# Initialiser le générateur
report_generator = ReportGenerator()

# Option 1 : Générer depuis les fichiers JSON
output_path = report_generator.generate_report_from_json_files(
    company_name="Cousin Surgery",
    needs_json_path="outputs/need_analysis_results.json",
    use_cases_json_path="outputs/use_case_analysis_results.json",
    output_dir="outputs"
)

# Option 2 : Générer depuis des données en mémoire
output_path = report_generator.generate_report(
    company_name="Cousin Surgery",
    final_needs=final_needs,
    final_quick_wins=final_quick_wins,
    final_structuration_ia=final_structuration_ia,
    output_dir="outputs"
)

print(f"Rapport généré : {output_path}")
```

### 3. Test rapide

Testez la génération de rapport avec les données existantes :

```bash
cd /home/addeche/aiko/aikoGPT
uv run test_report_generator.py
```

## 📂 Structure des fichiers

```
/home/addeche/aiko/aikoGPT/
├── assets/
│   ├── README.md
│   └── aiko_logo.png         ← Placez votre logo ici
├── outputs/
│   ├── need_analysis_results.json
│   ├── use_case_analysis_results.json
│   └── {JJMM}-V0-Cas_d_usages_IA-{company_name}.docx  ← Rapport généré
├── utils/
│   └── report_generator.py   ← Module de génération
└── app/
    └── app.py                ← Interface Streamlit avec bouton
```

## 🎨 Personnalisation

### Logo Aiko

1. Placez votre logo PNG dans `/home/addeche/aiko/aikoGPT/assets/aiko_logo.png`
2. Dimensions recommandées : 300x100 pixels
3. Le logo sera redimensionné automatiquement à 1.5 pouces de largeur

Voir `assets/README.md` pour plus de détails.

### Styles du document

Les styles sont définis dans `utils/report_generator.py` :

- **Marges** : 0.5 pouces (haut/bas), 0.8 pouces (gauche/droite)
- **Titres niveau 2** : 16pt, gras, bleu foncé (RGB 31, 73, 125)
- **Titres niveau 4** : 12pt, gras, bleu foncé
- **Liste** : Style "List Paragraph" pour les besoins et cas d'usage

### Modifier le template

Pour personnaliser davantage le rapport, modifiez les méthodes dans `report_generator.py` :

- `_setup_document_styles()` : Configuration des styles
- `_add_logo()` : Position et taille du logo
- `_add_needs_section()` : Structure de la section besoins
- `_add_use_cases_section()` : Structure de la section cas d'usage

## 🔍 Résolution de problèmes

### Le logo n'apparaît pas

**Problème** : Message "Logo Aiko non trouvé"

**Solution** :
1. Vérifiez que le fichier existe : `/home/addeche/aiko/aikoGPT/assets/aiko_logo.png`
2. Vérifiez les permissions de lecture du fichier
3. Le rapport sera généré sans logo si le fichier n'existe pas

### Erreur de génération

**Problème** : Erreur lors de la génération du rapport

**Solutions** :
1. Vérifiez que `python-docx` est installé :
   ```bash
   uv pip install python-docx
   ```

2. Vérifiez que les fichiers JSON existent :
   - `/home/addeche/aiko/aikoGPT/outputs/need_analysis_results.json`
   - `/home/addeche/aiko/aikoGPT/outputs/use_case_analysis_results.json`

3. Vérifiez les permissions d'écriture dans le dossier `outputs/`

### Format JSON incorrect

**Problème** : Les données ne s'affichent pas correctement dans le rapport

**Solution** :
Assurez-vous que vos données JSON suivent la structure attendue :

```json
{
  "final_needs": [
    {
      "theme": "Nom du thème",
      "quotes": [
        "« Citation 1 »",
        "« Citation 2 »"
      ]
    }
  ],
  "final_quick_wins": [
    {
      "titre": "Titre du cas d'usage",
      "ia_utilisee": "Type d'IA utilisée",
      "description": "Description détaillée..."
    }
  ],
  "final_structuration_ia": [...]
}
```

## 📊 Exemple de sortie

Voici ce que contient un rapport généré :

1. **Logo Aiko** (si disponible)
2. **Section Besoins** organisée par thèmes avec citations
3. **Texte d'introduction** personnalisé avec le nom de l'entreprise
4. **Quick Wins** : 5+ cas d'usage d'automatisation
5. **Structuration IA** : 5+ cas d'usage à moyen/long terme

Le rapport est prêt à être partagé avec les clients !

## 🔄 Intégration au workflow

La génération de rapport est intégrée dans le workflow principal :

1. **Zone 1-3** : Upload des données et saisie entreprise
2. **Workflow** : Analyse des besoins → Validation → Analyse use cases → Validation
3. **Génération** : Bouton "Générer le rapport Word" disponible après validation des use cases
4. **Export** : Téléchargement direct du fichier .docx

## 📝 Notes importantes

- Le logo de l'entreprise client (ex: Cousin Surgery) **n'est PAS inclus** dans le rapport généré
- Seul le logo Aiko est ajouté au rapport
- Le nom de l'entreprise est automatiquement remplacé dans tous les textes
- Le format de date dans le nom du fichier utilise le format jour/mois (JJMM)
- Les fichiers sont sauvegardés dans le dossier `outputs/` par défaut

## 🆘 Support

Pour toute question ou problème :
1. Consultez les logs de génération dans la console
2. Vérifiez le fichier de test : `test_report_generator.py`
3. Examinez le code source : `utils/report_generator.py`

