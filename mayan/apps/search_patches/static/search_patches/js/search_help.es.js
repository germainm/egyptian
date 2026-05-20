/**
 * search_help.es.js — Traducciones al español + ejemplos contextuales por campo
 * Mayan EDMS — Ayuda contextual para formularios de búsqueda avanzada
 */
window.SEARCH_HELP_I18N = {

  ui: {
    helpButtonTitle:  'Ayuda para este campo',
    helpButtonText:   '?',
    closePanel:       '\u00d7',
    panelTitlePrefix: 'Ayuda \u2014 ',
    opsTitle:         'Operadores disponibles',
    examplesTitle:    'Ejemplos',
    toggleShow:       'Ayuda de b\u00fasqueda',
    toggleHide:       'Ocultar ayuda',
    globalTitle:      'Ayuda de b\u00fasqueda avanzada',
    backendLabel:     'Backend: ',
    prefixesTitle:    'PREFIJOS DE OPERADOR',
    regexTitle:       'EJEMPLOS \u2014 EXPRESIONES REGULARES (PREFIJO %)',
    regexWarning:     '\u26a0 Los guiones (-) se convierten en _ en el \u00edndice. Use _ en sus patrones regex.',
    wildcardsTitle:   'EJEMPLOS \u2014 COMODINES * Y ?',
    wildcardsNote:    '* = cero o m\u00e1s caracteres \u00b7 ? = exactamente un car\u00e1cter',
    datesTitle:       'FORMATOS DE FECHA ACEPTADOS'
  },

  operators: {
    partial:    { alias: '(defecto)', label: 'B\u00fasqueda parcial',        example: 'informe' },
    exact:      { alias: '=',         label: 'Coincidencia exacta',         example: '=Factura' },
    phrase:     { alias: '"..."',     label: 'Frase exacta',                example: '"informe anual"' },
    fuzzy:      { alias: '~',         label: 'Aproximado (fuzzy)',          example: '~infome' },
    regex:      { alias: '%',         label: 'Expresi\u00f3n regular',      example: '%contrato_\\d{4}' },
    gt:         { alias: '>',         label: 'Mayor que',                   example: '>2024-01-01' },
    gte:        { alias: '>=',        label: 'Mayor o igual que',           example: '>=1000000' },
    lt:         { alias: '<',         label: 'Menor que',                   example: '<2024-06-01' },
    lte:        { alias: '<=',        label: 'Menor o igual que',           example: '<=200000' },
    range:      { alias: '[]',        label: 'Rango inclusivo',             example: '[]2024-01-01..2024-12-31' },
    range_excl: { alias: '{}',        label: 'Rango exclusivo',             example: '{}100000..5000000' }
  },

  fieldExamples: {

    'label': [
      { q: 'contrato',               desc: 'Documentos con "contrato" en el nombre' },
      { q: '=factura-2024-001.pdf',  desc: 'Nombre exacto (sin distinci\u00f3n may\u00fasculas)' },
      { q: '"informe anual"',        desc: 'Las dos palabras adyacentes en este orden' },
      { q: '%factura_2024_\\d+',     desc: 'Regex \u2014 factura-2024-001.pdf, etc.' },
      { q: '%^factura_\\d{4}_',      desc: 'Empieza por factura-XXXX-' },
      { q: '~infome',                desc: 'Aproximado \u2014 encuentra "informe"' }
    ],

    'filename': [
      { q: 'ikea',                   desc: 'Nombre de archivo contiene "ikea"' },
      { q: '=ikea_1989.pdf',         desc: 'Nombre exacto (con extensi\u00f3n)' },
      { q: '%^factura_\\d{4}_\\d{3}\\.pdf', desc: 'factura-2024-001.pdf (guiones \u2192 _)' },
      { q: 'mao*',                   desc: 'Empieza por "mao" (comod\u00edn)' },
      { q: '*2024*',                 desc: 'Contiene "2024" en cualquier parte' }
    ],

    'document_type__label': [
      { q: 'contrato',               desc: 'Tipo contiene "contrato"' },
      { q: '=Factura',               desc: 'Tipo exactamente "Factura"' },
      { q: '=Contrato',              desc: 'Tipo exactamente "Contrato"' },
      { q: '%^(Contrato|Factura)',    desc: 'Tipo = Contrato o Factura (regex)' }
    ],

    'document__document_type__label': [
      { q: '=Factura',               desc: 'Tipo exactamente "Factura"' },
      { q: '=Informe',               desc: 'Tipo exactamente "Informe"' },
      { q: 'contrato',               desc: 'Tipo contiene "contrato"' }
    ],

    'description': [
      { q: 'urgente',                desc: 'Descripci\u00f3n contiene "urgente"' },
      { q: '"para firmar"',          desc: 'Frase exacta en la descripci\u00f3n' }
    ],

    'datetime_created': [
      { q: '[]2024-01-01..2024-12-31', desc: 'Todo el a\u00f1o 2024' },
      { q: '>=2024-03-01',           desc: 'Desde el 1 de marzo de 2024' },
      { q: '>last week',             desc: 'Creado la semana pasada' },
      { q: '<2024-06-01',            desc: 'Antes del 1 de junio de 2024' },
      { q: '[]2024-01-15..2024-01-15', desc: 'ES: d\u00eda exacto (mismo l\u00edmite)' }
    ],

    'mimetype': [
      { q: 'application/pdf',        desc: 'Todos los archivos PDF' },
      { q: '=application/pdf',       desc: 'Solo PDF (exacto)' },
      { q: 'image/',                 desc: 'Todas las im\u00e1genes' },
      { q: '=image/jpeg',            desc: 'Solo JPEG' }
    ],

    'files__size': [
      { q: '>=1000000',              desc: 'Archivos \u2265 1\u00a0MB' },
      { q: '<200000',                desc: 'Archivos < 200\u00a0KB' },
      { q: '[]100000..5000000',      desc: 'Entre 100\u00a0KB y 5\u00a0MB' }
    ],

    'metadata__value': [
      { q: 'ABC Corp',               desc: 'Valor de metadato contiene "ABC Corp"' },
      { q: '=2024-001',              desc: 'Valor exacto del n\u00famero' }
    ],

    'metadata__metadata_type__name': [
      { q: 'proveedor',              desc: 'Nombre del tipo = "proveedor"' },
      { q: '=numero_contrato',       desc: 'Tipo exacto "numero_contrato"' }
    ],

    'tags__label': [
      { q: 'urgente',                desc: 'Etiqueta contiene "urgente"' },
      { q: '=urgente',               desc: 'Etiqueta exactamente "urgente"' }
    ],

    'cabinets__label': [
      { q: 'RRHH',                   desc: 'Gabinete contiene "RRHH"' },
      { q: '=Recursos Humanos',      desc: 'Nombre exacto del gabinete' }
    ],

    'groups__name': [
      { q: 'admin',                  desc: 'Grupo contiene "admin"' },
      { q: '=Administradores',       desc: 'Grupo exactamente "Administradores"' },
      { q: 'contabilidad',           desc: 'Grupos que contienen "contabilidad"' },
      { q: '~admins',                desc: 'Aproximado \u2014 encuentra "admin"' }
    ],

    'name': [
      { q: 'admin',                  desc: 'Nombre contiene "admin"' },
      { q: '=Contabilidad',          desc: 'Nombre exacto' }
    ],

    'value': [
      { q: 'Factura',                desc: 'Nodo de \u00edndice contiene "Factura"' },
      { q: '=2024',                  desc: 'Valor exacto "2024"' }
    ],

    'versions__pages__ocr_content__content': [
      { q: 'no conformidad',         desc: 'Contenido OCR contiene este t\u00e9rmino' },
      { q: '"fecha de entrega"',     desc: 'Frase exacta en el texto OCR' }
    ],

    'uuid': [
      { q: '550e8400',               desc: 'Inicio del UUID (b\u00fasqueda parcial)' },
      { q: '=550e8400e29b41d4a716446655440000', desc: 'UUID completo sin guiones (ES)' }
    ],

    'versions__active': [
      { q: '=true',                  desc: 'Solo versiones activas' },
      { q: '=false',                 desc: 'Versiones inactivas' }
    ]
  },

  fieldTypes: {
    text: {
      label: 'Texto',
      notes: 'Los guiones (-) se convierten en _ al indexar. Use _ en regex y comodines.',
      notesWarn: false,
      examples: [
        { q: 'contrato',             desc: 'Contiene "contrato"' },
        { q: '=Valor exacto',        desc: 'Coincidencia exacta' },
        { q: '"dos palabras"',       desc: 'Frase exacta' },
        { q: '~aproxim',             desc: 'Aproximado (fuzzy)' },
        { q: '%^[A-Z]{2,5}_\\d+',    desc: 'Regex \u2014 c\u00f3digos estructurados' }
      ]
    },
    datetime: {
      label: 'Fecha',
      notes: 'ES: = (exacto) no soportado \u2014 use [] con el mismo valor en ambos lados.',
      notesWarn: true,
      examples: [
        { q: '[]2024-01-01..2024-12-31', desc: 'Todo el a\u00f1o 2024' },
        { q: '>=2024-03-01',           desc: 'Desde el 1 de marzo de 2024' },
        { q: '>last week',             desc: 'La semana pasada' }
      ]
    },
    integer: {
      label: 'N\u00famero entero',
      notes: 'ES: b\u00fasqueda parcial no soportada en enteros \u2014 use = o >=.',
      notesWarn: true,
      examples: [
        { q: '>=1000000',              desc: '\u2265 1\u00a0MB' },
        { q: '<200000',                desc: '< 200\u00a0KB' }
      ]
    },
    uuid: {
      label: 'UUID',
      notes: 'ES: guiones eliminados. ORM/Whoosh: guiones reemplazados por _.',
      notesWarn: false,
      examples: [
        { q: '550e8400',               desc: 'Inicio del UUID' }
      ]
    },
    boolean: {
      label: 'Booleano',
      notes: 'Solo = (exacto) es soportado. Valores: true o false.',
      notesWarn: false,
      examples: [
        { q: '=true',                  desc: 'Valor verdadero' },
        { q: '=false',                 desc: 'Valor falso' }
      ]
    }
  },

  regexExamples: [
    { pattern: '%factura_2024_\\d{3}',   desc: 'factura-2024-001.pdf (guiones \u2192 _)' },
    { pattern: '%^[A-Z]{2,5}_\\d{4}',    desc: 'C\u00f3digos: ABC_1234, FACT_2024' },
    { pattern: '%informe.*(2023|2024)',   desc: 'Informes de 2023 o 2024' },
    { pattern: '%\\d{4}_\\d{2}_\\d{2}',  desc: 'Fecha en nombre: 2024_01_15' },
    { pattern: '%^(contrato|factura)',    desc: 'Empieza por contrato o factura' },
    { pattern: '%mao\\.zedong',           desc: 'Nombre con punto (. escapado)' }
  ],

  wildcardExamples: [
    { pattern: 'informe*',       desc: 'Empieza por "informe"' },
    { pattern: '*2024*',         desc: 'Contiene "2024"' },
    { pattern: 'contrato*2024*', desc: 'Empieza por "contrato" y contiene "2024"' },
    { pattern: 'factura_2024_*', desc: 'factura-2024-XXX (guiones \u2192 _ en \u00edndice)' }
  ],

  dateExamples: [
    { q: '[]2024-01-01..2024-12-31', desc: 'Todo el a\u00f1o 2024' },
    { q: '>=2024-03-01',             desc: 'Desde el 1 de marzo de 2024' },
    { q: '>last week',               desc: 'La semana pasada' },
    { q: '<yesterday',               desc: 'Antes de ayer' },
    { q: '>3 days ago',              desc: 'En los \u00faltimos 3 d\u00edas' },
    { q: '[]Jan 2024..Mar 2024',     desc: 'De enero a marzo de 2024' }
  ]
};
