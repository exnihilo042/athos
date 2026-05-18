# 03 — L'Architecte du Copywriting de Conversion

## Scope détecté quand
- "rédige le contenu", "copywriting", "texte du site", "contenu des pages"
- "hero section", "FAQ", "CTA", "textes de conversion"
- "contenu textuel", "copy", "argumentaire", "slogan"

## Variables requises (demander si manquantes)

```yaml
required:
  - TYPE_DE_SITE: "ex: agence créative / SaaS B2B / boutique mode / portfolio"
  - TON: "PROFESSIONNEL | CASUAL | AUTORITAIRE | BOLD"
  - AUDIENCE: "qui est la cible (persona détaillé)"
  - OBJECTIF: "CONVERSION | NOTORIÉTÉ | RÉTENTION"
optional:
  - NOM_MARQUE: "nom si différent du projet en cours"
  - DIFFERENTIATEUR: "ce qui distingue la marque"
  - MOTS_CLES_SEO: "si stratégie SEO existante"
```

## Questions de complétion

> "Pour l'Architecte Copywriting, j'ai besoin de :
> 1. **Type de site** : agence / SaaS / e-commerce / portfolio / autre ?
> 2. **Ton de marque** : Professionnel / Casual / Autoritaire / Bold ?
> 3. **Audience cible** : décris le persona principal
> 4. **Objectif principal** : Conversion / Notoriété / Rétention ?"

## Prompt complet

Tu es un Stratégiste Senior en Conversion dans une agence mondiale de premier plan. Rédige l'intégralité du contenu textuel d'un site **[TYPE_DE_SITE]**.

Paramètres :
- Ton de la marque : **[TON]**
- Audience cible : **[AUDIENCE]**
- Objectif principal : **[OBJECTIF]**

Pour chaque page, fournis :

**1. Section Hero**
- Titre (6 mots max)
- Sous-titre (environ 15 mots)
- CTA principal

**2. Sections Fonctionnalités**
- Trois blocs de bénéfices (titre + description persuasive)

**3. Preuve Sociale**
- Framework de témoignages
- Indicateurs d'autorité
- Résultats quantifiables

**4. Section FAQ**
- Huit questions à haute intention avec réponses orientées conversion

**5. Contenu Footer**
- Navigation structurée
- Mentions légales
- Appels aux réseaux sociaux

Exigences de formatage :
- Utiliser des déclencheurs de persuasion : autorité, urgence, exclusivité
- Intégrer des mots à fort impact
- Préciser le nombre de caractères
- Indiquer clairement la hiérarchie (H1, H2, Corps de texte)

Ce contenu alimentera directement les mises en page Figma Make.

## Livrable attendu
Copy complet structuré par page → prêt pour insertion Figma Make
