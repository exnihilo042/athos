# ATHOS Architect Prompts

5 personas experts activables par ATHOS, Claude et Codex.

## Détection de scope

Quand ATHOS détecte l'un de ces scopes dans une demande, il doit :
1. Identifier le persona correspondant
2. Lister les variables manquantes
3. Poser les questions de complétion (une seule fois, groupées)
4. Exécuter le prompt complet avec les infos collectées

## Personas disponibles

| # | Fichier | Scope détecté |
|---|---------|---------------|
| 01 | `01_architecte_systemes.md` | Architecture site, sitemap, blueprint technique, stack |
| 02 | `02_architecte_visuel.md` | Design system, tokens, typographie, couleurs, composants |
| 03 | `03_architecte_copywriting.md` | Copywriting site complet, hero, FAQ, CTA, footer |
| 04 | `04_traducteur_figma_make.md` | Traduction spec → prompts Figma Make |
| 05 | `05_ingenieur_interaction.md` | Composants interactifs React, state machines, formulaires |

## Usage

```
# Claude / ATHOS
"Architecte Systèmes pour [projet]"
"Crée le design system de [marque]"
"Écris le copy pour [type de site]"
"Traduis cette spec pour Figma Make"
"Conçois les modules interactifs"

# Codex
Même syntaxe — ATHOS détecte et route vers le bon persona
```
