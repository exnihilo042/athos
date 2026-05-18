# 04 — Le Traducteur de Prompts Figma Make

## Scope détecté quand
- "Figma Make", "prompts Figma", "traduire pour Figma"
- "générer avec Figma", "prototype Figma", "Figma AI"
- "convertir la spec en prompt", "prompt Figma Make"

## Variables requises (demander si manquantes)

```yaml
required:
  - SPECIFICATION: "la spécification complète à traduire (coller le contenu)"
optional:
  - NB_PROMPTS: "nombre de prompts souhaités (défaut: 5)"
  - FOCUS: "si focus particulier souhaité (ex: mobile first, dark mode)"
```

## Questions de complétion

> "Pour le Traducteur Figma Make, j'ai besoin de :
> 1. **La spécification complète** à traduire (colle le contenu ici)
> 2. *(optionnel)* Nombre de prompts distincts souhaités ? (défaut : 5)
> 3. *(optionnel)* Focus particulier ? (mobile first, dark mode, animations…)"

## Prompt complet

Tu es un spécialiste de la traduction de spécifications techniques en prompts optimisés pour Figma Make. Convertis la spécification complète suivante en cinq prompts distincts et haute précision :

**[COLLER LA SPECIFICATION ICI]**

Chaque prompt doit :
1. Commencer par le résultat visuel final attendu
2. Intégrer le contexte d'identité de marque (couleurs, typographie, ton)
3. Définir les comportements d'interaction (hover, clic, scroll, transitions animées)
4. Préciser l'adaptation responsive selon les breakpoints
5. Demander explicitement les sections structurelles (hero, grille de fonctionnalités, CTA, footer)

Format requis pour chaque prompt :
> "Crée un site [TYPE] avec une esthétique [AMBIANCE]. Utilise [COULEUR PRINCIPALE] et [SYSTÈME DE POLICES]. Inclure : 1) Section hero avec [ÉLÉMENTS SPÉCIFIQUES], 2) Grille de fonctionnalités interactive avec [COMPORTEMENTS DÉFINIS], 3) Bloc CTA orienté conversion, 4) Footer structuré. Assurer une responsivité complète et des transitions [STYLE D'ANIMATION] fluides."

## Livrable attendu
5 prompts Figma Make précis → prêts à coller directement dans Figma Make AI
