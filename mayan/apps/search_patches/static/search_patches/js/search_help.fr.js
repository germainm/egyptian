/**
 * search_help.fr.js — Traductions françaises + exemples contextuels par champ
 * Mayan EDMS — Aide contextuelle formulaires de recherche avancée
 */
window.SEARCH_HELP_I18N = {

  ui: {
    helpButtonTitle:  'Aide pour ce champ',
    helpButtonText:   '?',
    closePanel:       '\u00d7',
    panelTitlePrefix: 'Aide \u2014 ',
    opsTitle:         'Op\u00e9rateurs disponibles',
    examplesTitle:    'Exemples',
    toggleShow:       'Aide \u00e0 la recherche',
    toggleHide:       'Masquer l\'aide',
    globalTitle:      'Aide \u00e0 la recherche avanc\u00e9e',
    backendLabel:     'Backend\u00a0: ',
    prefixesTitle:    'PR\u00c9FIXES D\'OP\u00c9RATEUR',
    regexTitle:       'EXEMPLES \u2014 EXPRESSIONS R\u00c9GULI\u00c8RES (PR\u00c9FIXE %)',
    regexWarning:     '\u26a0 Les tirets (-) sont convertis en _ dans l\'index. Utilisez _ dans vos patterns regex.',
    wildcardsTitle:   'EXEMPLES \u2014 WILDCARDS * ET ?',
    wildcardsNote:    '* = z\u00e9ro ou plusieurs caract\u00e8res \u00b7 ? = exactement un caract\u00e8re',
    datesTitle:       'FORMATS DE DATES ACCEPT\u00c9S'
  },

  operators: {
    partial:    { alias: '(d\u00e9faut)', label: 'Recherche partielle',          example: 'rapport' },
    exact:      { alias: '=',            label: 'Correspondance exacte',        example: '=Contrat' },
    phrase:     { alias: '"..."',        label: 'Phrase exacte',                example: '"rapport annuel"' },
    fuzzy:      { alias: '~',            label: 'Approximatif (fuzzy)',         example: '~raport' },
    regex:      { alias: '%',            label: 'Expression r\u00e9guli\u00e8re', example: '%contrat_\\d{4}' },
    gt:         { alias: '>',            label: 'Sup\u00e9rieur strict',        example: '>2024-01-01' },
    gte:        { alias: '>=',           label: 'Sup\u00e9rieur ou \u00e9gal',  example: '>=1000000' },
    lt:         { alias: '<',            label: 'Inf\u00e9rieur strict',        example: '<2024-06-01' },
    lte:        { alias: '<=',           label: 'Inf\u00e9rieur ou \u00e9gal',  example: '<=200000' },
    range:      { alias: '[]',           label: 'Intervalle inclusif',          example: '[]2024-01-01..2024-12-31' },
    range_excl: { alias: '{}',           label: 'Intervalle exclusif',          example: '{}100000..5000000' }
  },

  // ── Exemples par champ spécifique ──────────────────────────────────────────
  // Clé = nom du champ dans le formulaire Mayan
  // Priorité sur fieldTypes.examples si le champ est trouvé ici

  fieldExamples: {

    'label': [
      { q: 'contrat',              desc: 'Documents contenant "contrat" dans le label' },
      { q: '=contrat-fournisseur-abc.pdf', desc: 'Label exact (insensible casse)' },
      { q: '"rapport annuel"',     desc: 'Les deux mots adjacents dans cet ordre' },
      { q: '%contrat_2024_\\d+',   desc: 'Regex \u2014 contrat-2024-001.pdf, etc.' },
      { q: '%^facture_\\d{4}_',    desc: 'Commence par facture-XXXX-' },
      { q: '~raport',              desc: 'Approximatif \u2014 trouve "rapport"' }
    ],

    'document__label': [
      { q: 'contrat',              desc: 'Label du document contient "contrat"' },
      { q: '%^facture_2024',       desc: 'Label commence par facture-2024' },
      { q: '"rapport annuel"',     desc: 'Phrase exacte dans le label' }
    ],

    'filename': [
      { q: 'ikea',                 desc: 'Nom de fichier contient "ikea"' },
      { q: '=ikea_1989.pdf',       desc: 'Nom exact (avec extension)' },
      { q: '%^facture_\\d{4}_\\d{3}\\.pdf', desc: 'facture-2024-001.pdf (tirets \u2192 _)' },
      { q: 'mao*',                 desc: 'Commence par "mao" (wildcard)' },
      { q: '*2024*',               desc: 'Contient "2024" n\'importe o\u00f9' },
      { q: '~zedong',              desc: 'Approximatif \u2014 tolère les variantes' }
    ],

    'document_type__label': [
      { q: 'contrat',              desc: 'Type contient "contrat"' },
      { q: '=Facture',             desc: 'Type exactement "Facture"' },
      { q: '=Contrat',             desc: 'Type exactement "Contrat"' },
      { q: '%^(Contrat|Facture)',   desc: 'Type = Contrat ou Facture (regex)' }
    ],

    'document__document_type__label': [
      { q: '=Facture',             desc: 'Type exactement "Facture"' },
      { q: '=Rapport',             desc: 'Type exactement "Rapport"' },
      { q: 'contrat',              desc: 'Type contient "contrat"' }
    ],

    'description': [
      { q: 'urgent',               desc: 'Description contient "urgent"' },
      { q: '"à signer"',           desc: 'Phrase exacte dans la description' },
      { q: '%livraison.*2024',      desc: 'Regex \u2014 livraison quelque chose 2024' }
    ],

    'datetime_created': [
      { q: '[]2024-01-01..2024-12-31', desc: 'Toute l\'ann\u00e9e 2024' },
      { q: '>=2024-03-01',         desc: '\u00c0 partir du 1er mars 2024' },
      { q: '>last week',           desc: 'Cr\u00e9\u00e9 la semaine derni\u00e8re' },
      { q: '<2024-06-01',          desc: 'Avant le 1er juin 2024' },
      { q: '[]2024-01-15..2024-01-15', desc: 'ES\u00a0: jour exact (m\u00eame borne)' }
    ],

    'mimetype': [
      { q: 'application/pdf',      desc: 'Tous les fichiers PDF' },
      { q: '=application/pdf',     desc: 'PDF uniquement (exact)' },
      { q: 'image/',               desc: 'Toutes les images (jpeg, png, etc.)' },
      { q: '%^image/',             desc: 'Regex \u2014 tout type image' },
      { q: '=image/jpeg',          desc: 'JPEG uniquement' }
    ],

    'files__mimetype': [
      { q: 'application/pdf',      desc: 'Fichiers PDF' },
      { q: 'image/jpeg',           desc: 'Images JPEG' },
      { q: '%^image/',             desc: 'Toutes les images' },
      { q: 'application/vnd.openxmlformats', desc: 'Fichiers Office (docx, xlsx…)' }
    ],

    'files__size': [
      { q: '>=1000000',            desc: 'Fichiers \u2265 1\u00a0MB' },
      { q: '<200000',              desc: 'Fichiers < 200\u00a0KB' },
      { q: '[]100000..5000000',    desc: 'Entre 100\u00a0KB et 5\u00a0MB' },
      { q: '=0',                   desc: 'Fichiers vides (0 octet)' }
    ],

    'size': [
      { q: '>=1000000',            desc: 'Taille \u2265 1\u00a0MB' },
      { q: '<200000',              desc: 'Taille < 200\u00a0KB' },
      { q: '[]100000..5000000',    desc: 'Entre 100\u00a0KB et 5\u00a0MB' }
    ],

    'checksum': [
      { q: 'a1b2c3',               desc: 'Début du hash (recherche partielle)' },
      { q: '=a1b2c3d4e5f6...',     desc: 'Checksum exact complet' }
    ],

    'comment': [
      { q: 'approuvé',             desc: 'Commentaire contient "approuv\u00e9"' },
      { q: '"version finale"',     desc: 'Phrase exacte dans le commentaire' }
    ],

    'metadata__value': [
      { q: 'ABC Corp',             desc: 'Valeur de m\u00e9tadonn\u00e9e contient "ABC Corp"' },
      { q: '=2024-001',            desc: 'Valeur exacte du num\u00e9ro' },
      { q: '[]2024-01-01..2024-12-31', desc: 'Si la valeur est une date' }
    ],

    'metadata__metadata_type__name': [
      { q: 'fournisseur',          desc: 'Nom du type de m\u00e9tadonn\u00e9e = "fournisseur"' },
      { q: '=numero_contrat',      desc: 'Type exact "numero_contrat"' },
      { q: 'date',                 desc: 'Types contenant "date"' }
    ],

    'metadata__metadata_type__label': [
      { q: 'Fournisseur',          desc: 'Label du type contient "Fournisseur"' },
      { q: '=Num\u00e9ro de contrat', desc: 'Label exact' }
    ],

    'tags__label': [
      { q: 'urgent',               desc: 'Tag contient "urgent"' },
      { q: '=urgent',              desc: 'Tag exactement "urgent"' },
      { q: '=\u00e0 signer',       desc: 'Tag exactement "\u00e0 signer"' }
    ],

    'cabinets__label': [
      { q: 'RH',                   desc: 'Cabinet contient "RH"' },
      { q: '=Ressources humaines', desc: 'Cabinet exact' },
      { q: 'finance',              desc: 'Cabinets contenant "finance"' }
    ],

    'groups__name': [
      { q: 'admin',                desc: 'Groupe contient "admin"' },
      { q: '=Administrateurs',     desc: 'Groupe exact "Administrateurs"' },
      { q: 'comptab',              desc: 'Groupes contenant "comptab"' },
      { q: '~admins',              desc: 'Approximatif \u2014 trouve "admin"' }
    ],

    'name': [
      { q: 'admin',                desc: 'Nom contient "admin"' },
      { q: '=Comptabilité',        desc: 'Nom exact' },
      { q: '%^[A-Z]',              desc: 'Regex \u2014 noms commençant par une majuscule' }
    ],

    'value': [
      { q: 'Facture',              desc: 'N\u0153ud d\'index contient "Facture"' },
      { q: '=2024',                desc: 'Valeur exacte "2024"' },
      { q: '%^2024',               desc: 'Valeur commence par 2024' }
    ],

    'versions__pages__ocr_content__content': [
      { q: 'non-conformit\u00e9', desc: 'OCR contient ce terme' },
      { q: '"date de livraison"',  desc: 'Phrase exacte dans le texte OCR' },
      { q: '~conformite',          desc: 'Approximatif \u2014 tolère accents manquants' }
    ],

    'file_pages__content__content': [
      { q: 'facture',              desc: 'Contenu de page contient "facture"' },
      { q: '"total HT"',           desc: 'Phrase exacte dans la page' }
    ],

    'file_metadata_drivers__entries__key': [
      { q: 'Author',               desc: 'Cl\u00e9 m\u00e9tadonn\u00e9e = "Author"' },
      { q: 'Creator',              desc: 'Cl\u00e9 = "Creator"' },
      { q: '=PDF:Producer',        desc: 'Cl\u00e9 exacte "PDF:Producer"' }
    ],

    'file_metadata_drivers__entries__value': [
      { q: 'Adobe',                desc: 'Valeur contient "Adobe"' },
      { q: 'Microsoft Word',       desc: 'Valeur contient "Microsoft Word"' }
    ],

    'source_metadata__key': [
      { q: 'filename',             desc: 'Cl\u00e9 source = "filename"' },
      { q: '=original_filename',   desc: 'Cl\u00e9 exacte' }
    ],

    'source_metadata__value': [
      { q: 'scan',                 desc: 'Valeur source contient "scan"' }
    ],

    'uuid': [
      { q: '550e8400',             desc: 'D\u00e9but de l\'UUID (recherche partielle)' },
      { q: '=550e8400-e29b-41d4-a716-446655440000', desc: 'UUID complet avec tirets (ORM)' },
      { q: '=550e8400e29b41d4a716446655440000', desc: 'UUID sans tirets (ES)' }
    ],

    'document__uuid': [
      { q: '550e8400',             desc: 'D\u00e9but de l\'UUID du document' }
    ],

    'versions__active': [
      { q: '=true',                desc: 'Version active uniquement' },
      { q: '=false',               desc: 'Versions non actives' }
    ]
  },

  // ── Types de champs — fallback si champ non dans fieldExamples ─────────────

  fieldTypes: {
    text: {
      label: 'Texte',
      notes: 'Les tirets (-) sont convertis en _ lors de l\'indexation. Utilisez _ dans les regex.',
      notesWarn: false,
      examples: [
        { q: 'contrat',             desc: 'Contient "contrat"' },
        { q: '=Valeur exacte',      desc: 'Correspondance exacte' },
        { q: '"deux mots"',         desc: 'Phrase exacte' },
        { q: '~aproxi',             desc: 'Approximatif (fuzzy)' },
        { q: '%^[A-Z]{2,5}_\\d+',   desc: 'Regex \u2014 codes structurés' }
      ]
    },
    datetime: {
      label: 'Date',
      notes: 'ES\u00a0: = (exact) non support\u00e9 \u2014 utilisez [] avec la m\u00eame borne des deux c\u00f4t\u00e9s.',
      notesWarn: true,
      examples: [
        { q: '[]2024-01-01..2024-12-31', desc: 'Toute l\'ann\u00e9e 2024' },
        { q: '>=2024-03-01',         desc: '\u00c0 partir du 1er mars 2024' },
        { q: '>last week',           desc: 'La semaine derni\u00e8re' },
        { q: '[]2024-01-15..2024-01-15', desc: 'ES\u00a0: jour exact' }
      ]
    },
    integer: {
      label: 'Nombre entier',
      notes: 'ES\u00a0: recherche partielle non support\u00e9e \u2014 utilisez = ou >=.',
      notesWarn: true,
      examples: [
        { q: '>=1000000',            desc: '\u2265 1\u00a0MB' },
        { q: '<200000',              desc: '< 200\u00a0KB' },
        { q: '[]100000..5000000',    desc: 'Entre 100\u00a0KB et 5\u00a0MB' }
      ]
    },
    uuid: {
      label: 'UUID',
      notes: 'ES\u00a0: tirets supprim\u00e9s. ORM/Whoosh\u00a0: tirets remplac\u00e9s par _.',
      notesWarn: false,
      examples: [
        { q: '550e8400',             desc: 'D\u00e9but de l\'UUID' },
        { q: '=550e8400e29b41d4a716446655440000', desc: 'UUID complet (ES, sans tirets)' }
      ]
    },
    boolean: {
      label: 'Bool\u00e9en',
      notes: 'Seul = (exact) est support\u00e9. Valeurs\u00a0: true ou false.',
      notesWarn: false,
      examples: [
        { q: '=true',                desc: 'Valeur vraie' },
        { q: '=false',               desc: 'Valeur fausse' }
      ]
    }
  },

  regexExamples: [
    { pattern: '%facture_2024_\\d{3}',   desc: 'facture-2024-001.pdf (tirets \u2192 _)' },
    { pattern: '%^[A-Z]{2,5}_\\d{4}',    desc: 'Codes : ABC_1234, FACT_2024' },
    { pattern: '%rapport.*(2023|2024)',   desc: 'Rapports de 2023 ou 2024' },
    { pattern: '%\\d{4}_\\d{2}_\\d{2}',  desc: 'Date dans le nom\u00a0: 2024_01_15' },
    { pattern: '%^(contrat|facture)',     desc: 'Commence par contrat ou facture' },
    { pattern: '%mao\\.zedong',           desc: 'Nom avec point (. \u00e9chapp\u00e9)' }
  ],

  wildcardExamples: [
    { pattern: 'rapport*',       desc: 'Commence par "rapport"' },
    { pattern: '*2024*',         desc: 'Contient "2024"' },
    { pattern: 'contrat*2024*',  desc: 'Commence par "contrat" et contient "2024"' },
    { pattern: 'facture_2024_*', desc: 'facture-2024-XXX (tirets \u2192 _ dans l\'index)' }
  ],

  dateExamples: [
    { q: '[]2024-01-01..2024-12-31', desc: 'Toute l\'ann\u00e9e 2024' },
    { q: '>=2024-03-01',             desc: '\u00c0 partir du 1er mars 2024' },
    { q: '>last week',               desc: 'La semaine derni\u00e8re' },
    { q: '<yesterday',               desc: 'Avant hier' },
    { q: '>3 days ago',              desc: 'Dans les 3 derniers jours' },
    { q: '[]Jan 2024..Mar 2024',     desc: 'De janvier \u00e0 mars 2024' }
  ]
};
