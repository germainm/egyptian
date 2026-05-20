/**
 * search_help.pt.js — Traduções em português + exemplos contextuais por campo
 * Mayan EDMS — Ajuda contextual para formulários de pesquisa avançada
 */
window.SEARCH_HELP_I18N = {

  ui: {
    helpButtonTitle:  'Ajuda para este campo',
    helpButtonText:   '?',
    closePanel:       '\u00d7',
    panelTitlePrefix: 'Ajuda \u2014 ',
    opsTitle:         'Operadores dispon\u00edveis',
    examplesTitle:    'Exemplos',
    toggleShow:       'Ajuda de pesquisa',
    toggleHide:       'Ocultar ajuda',
    globalTitle:      'Ajuda de pesquisa avan\u00e7ada',
    backendLabel:     'Backend: ',
    prefixesTitle:    'PREFIXOS DE OPERADOR',
    regexTitle:       'EXEMPLOS \u2014 EXPRESS\u00d5ES REGULARES (PREFIXO %)',
    regexWarning:     '\u26a0 H\u00edfens (-) s\u00e3o convertidos em _ no \u00edndice. Use _ nos seus padr\u00f5es regex.',
    wildcardsTitle:   'EXEMPLOS \u2014 CURINGAS * E ?',
    wildcardsNote:    '* = zero ou mais caracteres \u00b7 ? = exatamente um caractere',
    datesTitle:       'FORMATOS DE DATA ACEITOS'
  },

  operators: {
    partial:    { alias: '(padr\u00e3o)', label: 'Pesquisa parcial',           example: 'relat\u00f3rio' },
    exact:      { alias: '=',             label: 'Correspond\u00eancia exata', example: '=Fatura' },
    phrase:     { alias: '"..."',         label: 'Frase exata',               example: '"relat\u00f3rio anual"' },
    fuzzy:      { alias: '~',             label: 'Aproximado (fuzzy)',         example: '~relatorio' },
    regex:      { alias: '%',             label: 'Express\u00e3o regular',     example: '%contrato_\\d{4}' },
    gt:         { alias: '>',             label: 'Maior que',                 example: '>2024-01-01' },
    gte:        { alias: '>=',            label: 'Maior ou igual a',          example: '>=1000000' },
    lt:         { alias: '<',             label: 'Menor que',                 example: '<2024-06-01' },
    lte:        { alias: '<=',            label: 'Menor ou igual a',          example: '<=200000' },
    range:      { alias: '[]',            label: 'Intervalo inclusivo',       example: '[]2024-01-01..2024-12-31' },
    range_excl: { alias: '{}',            label: 'Intervalo exclusivo',       example: '{}100000..5000000' }
  },

  fieldExamples: {

    'label': [
      { q: 'contrato',               desc: 'Documentos com "contrato" no r\u00f3tulo' },
      { q: '=fatura-2024-001.pdf',   desc: 'R\u00f3tulo exato (sem distin\u00e7\u00e3o mai\u00fasculas)' },
      { q: '"relat\u00f3rio anual"', desc: 'As duas palavras adjacentes nesta ordem' },
      { q: '%fatura_2024_\\d+',      desc: 'Regex \u2014 fatura-2024-001.pdf, etc.' },
      { q: '%^fatura_\\d{4}_',       desc: 'Come\u00e7a com fatura-XXXX-' },
      { q: '~relatorio',             desc: 'Aproximado \u2014 encontra "relat\u00f3rio"' }
    ],

    'filename': [
      { q: 'ikea',                   desc: 'Nome do arquivo cont\u00e9m "ikea"' },
      { q: '=ikea_1989.pdf',         desc: 'Nome exato (com extens\u00e3o)' },
      { q: '%^fatura_\\d{4}_\\d{3}\\.pdf', desc: 'fatura-2024-001.pdf (h\u00edfens \u2192 _)' },
      { q: 'mao*',                   desc: 'Come\u00e7a com "mao" (curinga)' },
      { q: '*2024*',                 desc: 'Cont\u00e9m "2024" em qualquer posi\u00e7\u00e3o' }
    ],

    'document_type__label': [
      { q: 'contrato',               desc: 'Tipo cont\u00e9m "contrato"' },
      { q: '=Fatura',                desc: 'Tipo exatamente "Fatura"' },
      { q: '=Contrato',              desc: 'Tipo exatamente "Contrato"' },
      { q: '%^(Contrato|Fatura)',     desc: 'Tipo = Contrato ou Fatura (regex)' }
    ],

    'document__document_type__label': [
      { q: '=Fatura',                desc: 'Tipo exatamente "Fatura"' },
      { q: '=Relat\u00f3rio',        desc: 'Tipo exatamente "Relat\u00f3rio"' },
      { q: 'contrato',               desc: 'Tipo cont\u00e9m "contrato"' }
    ],

    'description': [
      { q: 'urgente',                desc: 'Descri\u00e7\u00e3o cont\u00e9m "urgente"' },
      { q: '"para assinar"',         desc: 'Frase exata na descri\u00e7\u00e3o' }
    ],

    'datetime_created': [
      { q: '[]2024-01-01..2024-12-31', desc: 'Todo o ano de 2024' },
      { q: '>=2024-03-01',           desc: 'A partir de 1\u00ba de mar\u00e7o de 2024' },
      { q: '>last week',             desc: 'Criado na semana passada' },
      { q: '<2024-06-01',            desc: 'Antes de 1\u00ba de junho de 2024' },
      { q: '[]2024-01-15..2024-01-15', desc: 'ES: dia exato (mesmo limite dos dois lados)' }
    ],

    'mimetype': [
      { q: 'application/pdf',        desc: 'Todos os arquivos PDF' },
      { q: '=application/pdf',       desc: 'Somente PDF (exato)' },
      { q: 'image/',                 desc: 'Todas as imagens' },
      { q: '=image/jpeg',            desc: 'Somente JPEG' }
    ],

    'files__size': [
      { q: '>=1000000',              desc: 'Arquivos \u2265 1\u00a0MB' },
      { q: '<200000',                desc: 'Arquivos < 200\u00a0KB' },
      { q: '[]100000..5000000',      desc: 'Entre 100\u00a0KB e 5\u00a0MB' }
    ],

    'metadata__value': [
      { q: 'ABC Corp',               desc: 'Valor de metadado cont\u00e9m "ABC Corp"' },
      { q: '=2024-001',              desc: 'Valor exato do n\u00famero' }
    ],

    'metadata__metadata_type__name': [
      { q: 'fornecedor',             desc: 'Nome do tipo = "fornecedor"' },
      { q: '=numero_contrato',       desc: 'Tipo exato "numero_contrato"' }
    ],

    'tags__label': [
      { q: 'urgente',                desc: 'Etiqueta cont\u00e9m "urgente"' },
      { q: '=urgente',               desc: 'Etiqueta exatamente "urgente"' }
    ],

    'cabinets__label': [
      { q: 'RH',                     desc: 'Armário cont\u00e9m "RH"' },
      { q: '=Recursos Humanos',      desc: 'Nome exato do arm\u00e1rio' }
    ],

    'groups__name': [
      { q: 'admin',                  desc: 'Grupo cont\u00e9m "admin"' },
      { q: '=Administradores',       desc: 'Grupo exatamente "Administradores"' },
      { q: 'contabilidade',          desc: 'Grupos contendo "contabilidade"' },
      { q: '~admins',                desc: 'Aproximado \u2014 encontra "admin"' }
    ],

    'name': [
      { q: 'admin',                  desc: 'Nome cont\u00e9m "admin"' },
      { q: '=Contabilidade',         desc: 'Nome exato' }
    ],

    'value': [
      { q: 'Fatura',                 desc: 'N\u00f3 de \u00edndice cont\u00e9m "Fatura"' },
      { q: '=2024',                  desc: 'Valor exato "2024"' }
    ],

    'versions__pages__ocr_content__content': [
      { q: 'n\u00e3o conformidade',  desc: 'Conte\u00fado OCR cont\u00e9m este termo' },
      { q: '"data de entrega"',      desc: 'Frase exata no texto OCR' }
    ],

    'uuid': [
      { q: '550e8400',               desc: 'In\u00edcio do UUID (pesquisa parcial)' },
      { q: '=550e8400e29b41d4a716446655440000', desc: 'UUID completo sem h\u00edfens (ES)' }
    ],

    'versions__active': [
      { q: '=true',                  desc: 'Somente vers\u00f5es ativas' },
      { q: '=false',                 desc: 'Vers\u00f5es inativas' }
    ]
  },

  fieldTypes: {
    text: {
      label: 'Texto',
      notes: 'H\u00edfens (-) s\u00e3o convertidos em _ na indexa\u00e7\u00e3o. Use _ em regex e curingas.',
      notesWarn: false,
      examples: [
        { q: 'contrato',             desc: 'Cont\u00e9m "contrato"' },
        { q: '=Valor exato',         desc: 'Correspond\u00eancia exata' },
        { q: '"duas palavras"',      desc: 'Frase exata' },
        { q: '~aproxim',             desc: 'Aproximado (fuzzy)' },
        { q: '%^[A-Z]{2,5}_\\d+',    desc: 'Regex \u2014 c\u00f3digos estruturados' }
      ]
    },
    datetime: {
      label: 'Data',
      notes: 'ES: = (exato) n\u00e3o suportado \u2014 use [] com o mesmo valor nos dois lados.',
      notesWarn: true,
      examples: [
        { q: '[]2024-01-01..2024-12-31', desc: 'Todo o ano de 2024' },
        { q: '>=2024-03-01',           desc: 'A partir de 1\u00ba de mar\u00e7o de 2024' },
        { q: '>last week',             desc: 'Semana passada' }
      ]
    },
    integer: {
      label: 'N\u00famero inteiro',
      notes: 'ES: pesquisa parcial n\u00e3o suportada em inteiros \u2014 use = ou >=.',
      notesWarn: true,
      examples: [
        { q: '>=1000000',              desc: '\u2265 1\u00a0MB' },
        { q: '<200000',                desc: '< 200\u00a0KB' }
      ]
    },
    uuid: {
      label: 'UUID',
      notes: 'ES: h\u00edfens removidos. ORM/Whoosh: h\u00edfens substitu\u00eddos por _.',
      notesWarn: false,
      examples: [
        { q: '550e8400',               desc: 'In\u00edcio do UUID' }
      ]
    },
    boolean: {
      label: 'Booleano',
      notes: 'Apenas = (exato) \u00e9 suportado. Valores: true ou false.',
      notesWarn: false,
      examples: [
        { q: '=true',                  desc: 'Valor verdadeiro' },
        { q: '=false',                 desc: 'Valor falso' }
      ]
    }
  },

  regexExamples: [
    { pattern: '%fatura_2024_\\d{3}',    desc: 'fatura-2024-001.pdf (h\u00edfens \u2192 _)' },
    { pattern: '%^[A-Z]{2,5}_\\d{4}',    desc: 'C\u00f3digos: ABC_1234, FAT_2024' },
    { pattern: '%relatorio.*(2023|2024)', desc: 'Relat\u00f3rios de 2023 ou 2024' },
    { pattern: '%\\d{4}_\\d{2}_\\d{2}',  desc: 'Data no nome: 2024_01_15' },
    { pattern: '%^(contrato|fatura)',     desc: 'Come\u00e7a com contrato ou fatura' },
    { pattern: '%mao\\.zedong',           desc: 'Nome com ponto (. escapado)' }
  ],

  wildcardExamples: [
    { pattern: 'relatorio*',     desc: 'Come\u00e7a com "relatorio"' },
    { pattern: '*2024*',         desc: 'Cont\u00e9m "2024"' },
    { pattern: 'contrato*2024*', desc: 'Come\u00e7a com "contrato" e cont\u00e9m "2024"' },
    { pattern: 'fatura_2024_*',  desc: 'fatura-2024-XXX (h\u00edfens \u2192 _ no \u00edndice)' }
  ],

  dateExamples: [
    { q: '[]2024-01-01..2024-12-31', desc: 'Todo o ano de 2024' },
    { q: '>=2024-03-01',             desc: 'A partir de 1\u00ba de mar\u00e7o de 2024' },
    { q: '>last week',               desc: 'Semana passada' },
    { q: '<yesterday',               desc: 'Antes de ontem' },
    { q: '>3 days ago',              desc: 'Nos \u00faltimos 3 dias' },
    { q: '[]Jan 2024..Mar 2024',     desc: 'De janeiro a mar\u00e7o de 2024' }
  ]
};
