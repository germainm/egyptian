/**
 * search_help.en.js — English translations + contextual examples per field
 * Mayan EDMS — Advanced search form contextual help
 */
window.SEARCH_HELP_I18N = {

  ui: {
    helpButtonTitle:  'Help for this field',
    helpButtonText:   '?',
    closePanel:       '\u00d7',
    panelTitlePrefix: 'Help \u2014 ',
    opsTitle:         'Available operators',
    examplesTitle:    'Examples',
    toggleShow:       'Search help',
    toggleHide:       'Hide help',
    globalTitle:      'Advanced search help',
    backendLabel:     'Backend: ',
    prefixesTitle:    'OPERATOR PREFIXES',
    regexTitle:       'EXAMPLES \u2014 REGULAR EXPRESSIONS (PREFIX %)',
    regexWarning:     '\u26a0 Hyphens (-) are converted to _ in the index. Use _ in your regex patterns.',
    wildcardsTitle:   'EXAMPLES \u2014 WILDCARDS * AND ?',
    wildcardsNote:    '* = zero or more characters \u00b7 ? = exactly one character',
    datesTitle:       'ACCEPTED DATE FORMATS'
  },

  operators: {
    partial:    { alias: '(default)', label: 'Partial search',          example: 'report' },
    exact:      { alias: '=',         label: 'Exact match',             example: '=Invoice' },
    phrase:     { alias: '"..."',     label: 'Exact phrase',            example: '"annual report"' },
    fuzzy:      { alias: '~',         label: 'Fuzzy (approximate)',     example: '~raport' },
    regex:      { alias: '%',         label: 'Regular expression',      example: '%contract_\\d{4}' },
    gt:         { alias: '>',         label: 'Greater than',            example: '>2024-01-01' },
    gte:        { alias: '>=',        label: 'Greater than or equal',   example: '>=1000000' },
    lt:         { alias: '<',         label: 'Less than',               example: '<2024-06-01' },
    lte:        { alias: '<=',        label: 'Less than or equal',      example: '<=200000' },
    range:      { alias: '[]',        label: 'Inclusive range',         example: '[]2024-01-01..2024-12-31' },
    range_excl: { alias: '{}',        label: 'Exclusive range',         example: '{}100000..5000000' }
  },

  fieldExamples: {

    'label': [
      { q: 'contract',               desc: 'Documents with "contract" in label' },
      { q: '=invoice-2024-001.pdf',  desc: 'Exact label (case insensitive)' },
      { q: '"annual report"',        desc: 'Both words adjacent in this order' },
      { q: '%invoice_2024_\\d+',     desc: 'Regex \u2014 invoice-2024-001.pdf, etc.' },
      { q: '%^invoice_\\d{4}_',      desc: 'Starts with invoice-XXXX-' },
      { q: '~raport',                desc: 'Fuzzy \u2014 finds "report"' }
    ],

    'document__label': [
      { q: 'contract',               desc: 'Document label contains "contract"' },
      { q: '%^invoice_2024',         desc: 'Label starts with invoice-2024' },
      { q: '"annual report"',        desc: 'Exact phrase in label' }
    ],

    'filename': [
      { q: 'ikea',                   desc: 'Filename contains "ikea"' },
      { q: '=ikea_1989.pdf',         desc: 'Exact filename (with extension)' },
      { q: '%^invoice_\\d{4}_\\d{3}\\.pdf', desc: 'invoice-2024-001.pdf (hyphens \u2192 _)' },
      { q: 'mao*',                   desc: 'Starts with "mao" (wildcard)' },
      { q: '*2024*',                 desc: 'Contains "2024" anywhere' },
      { q: '~zedong',                desc: 'Fuzzy \u2014 tolerates variations' }
    ],

    'document_type__label': [
      { q: 'contract',               desc: 'Type contains "contract"' },
      { q: '=Invoice',               desc: 'Type exactly "Invoice"' },
      { q: '=Contract',              desc: 'Type exactly "Contract"' },
      { q: '%^(Contract|Invoice)',    desc: 'Type = Contract or Invoice (regex)' }
    ],

    'document__document_type__label': [
      { q: '=Invoice',               desc: 'Type exactly "Invoice"' },
      { q: '=Report',                desc: 'Type exactly "Report"' },
      { q: 'contract',               desc: 'Type contains "contract"' }
    ],

    'description': [
      { q: 'urgent',                 desc: 'Description contains "urgent"' },
      { q: '"to be signed"',         desc: 'Exact phrase in description' },
      { q: '%delivery.*2024',         desc: 'Regex \u2014 delivery something 2024' }
    ],

    'datetime_created': [
      { q: '[]2024-01-01..2024-12-31', desc: 'All of 2024' },
      { q: '>=2024-03-01',           desc: 'From March 1st 2024' },
      { q: '>last week',             desc: 'Created last week' },
      { q: '<2024-06-01',            desc: 'Before June 1st 2024' },
      { q: '[]2024-01-15..2024-01-15', desc: 'ES: exact day (same bound both sides)' }
    ],

    'mimetype': [
      { q: 'application/pdf',        desc: 'All PDF files' },
      { q: '=application/pdf',       desc: 'PDF only (exact)' },
      { q: 'image/',                 desc: 'All images (jpeg, png, etc.)' },
      { q: '%^image/',               desc: 'Regex \u2014 any image type' },
      { q: '=image/jpeg',            desc: 'JPEG only' }
    ],

    'files__mimetype': [
      { q: 'application/pdf',        desc: 'PDF files' },
      { q: 'image/jpeg',             desc: 'JPEG images' },
      { q: '%^image/',               desc: 'All image types' },
      { q: 'application/vnd.openxmlformats', desc: 'Office files (docx, xlsx...)' }
    ],

    'files__size': [
      { q: '>=1000000',              desc: 'Files \u2265 1\u00a0MB' },
      { q: '<200000',                desc: 'Files < 200\u00a0KB' },
      { q: '[]100000..5000000',      desc: 'Between 100\u00a0KB and 5\u00a0MB' },
      { q: '=0',                     desc: 'Empty files (0 bytes)' }
    ],

    'size': [
      { q: '>=1000000',              desc: 'Size \u2265 1\u00a0MB' },
      { q: '<200000',                desc: 'Size < 200\u00a0KB' },
      { q: '[]100000..5000000',      desc: 'Between 100\u00a0KB and 5\u00a0MB' }
    ],

    'checksum': [
      { q: 'a1b2c3',                 desc: 'Start of hash (partial search)' },
      { q: '=a1b2c3d4e5f6...',       desc: 'Complete exact checksum' }
    ],

    'comment': [
      { q: 'approved',               desc: 'Comment contains "approved"' },
      { q: '"final version"',        desc: 'Exact phrase in comment' }
    ],

    'metadata__value': [
      { q: 'ABC Corp',               desc: 'Metadata value contains "ABC Corp"' },
      { q: '=2024-001',              desc: 'Exact number value' },
      { q: '[]2024-01-01..2024-12-31', desc: 'If the value is a date' }
    ],

    'metadata__metadata_type__name': [
      { q: 'supplier',               desc: 'Metadata type name = "supplier"' },
      { q: '=contract_number',       desc: 'Exact type "contract_number"' },
      { q: 'date',                   desc: 'Types containing "date"' }
    ],

    'metadata__metadata_type__label': [
      { q: 'Supplier',               desc: 'Type label contains "Supplier"' },
      { q: '=Contract Number',       desc: 'Exact label' }
    ],

    'tags__label': [
      { q: 'urgent',                 desc: 'Tag contains "urgent"' },
      { q: '=urgent',                desc: 'Tag exactly "urgent"' },
      { q: '=to-sign',               desc: 'Tag exactly "to-sign"' }
    ],

    'cabinets__label': [
      { q: 'HR',                     desc: 'Cabinet contains "HR"' },
      { q: '=Human Resources',       desc: 'Exact cabinet name' },
      { q: 'finance',                desc: 'Cabinets containing "finance"' }
    ],

    'groups__name': [
      { q: 'admin',                  desc: 'Group contains "admin"' },
      { q: '=Administrators',        desc: 'Group exactly "Administrators"' },
      { q: 'accounting',             desc: 'Groups containing "accounting"' },
      { q: '~admins',                desc: 'Fuzzy \u2014 finds "admin"' }
    ],

    'name': [
      { q: 'admin',                  desc: 'Name contains "admin"' },
      { q: '=Accounting',            desc: 'Exact name' },
      { q: '%^[A-Z]',                desc: 'Regex \u2014 names starting with uppercase' }
    ],

    'value': [
      { q: 'Invoice',                desc: 'Index node contains "Invoice"' },
      { q: '=2024',                  desc: 'Exact value "2024"' },
      { q: '%^2024',                 desc: 'Value starts with 2024' }
    ],

    'versions__pages__ocr_content__content': [
      { q: 'non-conformance',        desc: 'OCR content contains this term' },
      { q: '"delivery date"',        desc: 'Exact phrase in OCR text' },
      { q: '~conformance',           desc: 'Fuzzy \u2014 tolerates variants' }
    ],

    'file_pages__content__content': [
      { q: 'invoice',                desc: 'Page content contains "invoice"' },
      { q: '"total amount"',         desc: 'Exact phrase in page' }
    ],

    'file_metadata_drivers__entries__key': [
      { q: 'Author',                 desc: 'Metadata key = "Author"' },
      { q: 'Creator',                desc: 'Key = "Creator"' },
      { q: '=PDF:Producer',          desc: 'Exact key "PDF:Producer"' }
    ],

    'file_metadata_drivers__entries__value': [
      { q: 'Adobe',                  desc: 'Value contains "Adobe"' },
      { q: 'Microsoft Word',         desc: 'Value contains "Microsoft Word"' }
    ],

    'uuid': [
      { q: '550e8400',               desc: 'Start of UUID (partial search)' },
      { q: '=550e8400-e29b-41d4-a716-446655440000', desc: 'Full UUID with hyphens (ORM)' },
      { q: '=550e8400e29b41d4a716446655440000', desc: 'UUID without hyphens (ES)' }
    ],

    'versions__active': [
      { q: '=true',                  desc: 'Active versions only' },
      { q: '=false',                 desc: 'Inactive versions' }
    ]
  },

  fieldTypes: {
    text: {
      label: 'Text',
      notes: 'Hyphens (-) are converted to _ at indexing time. Use _ in regex and wildcards.',
      notesWarn: false,
      examples: [
        { q: 'contract',             desc: 'Contains "contract"' },
        { q: '=Exact value',         desc: 'Exact match' },
        { q: '"two words"',          desc: 'Exact phrase' },
        { q: '~aproxim',             desc: 'Fuzzy (approximate)' },
        { q: '%^[A-Z]{2,5}_\\d+',    desc: 'Regex \u2014 structured codes' }
      ]
    },
    datetime: {
      label: 'Date',
      notes: 'ES: = (exact) not supported \u2014 use [] with the same value on both sides.',
      notesWarn: true,
      examples: [
        { q: '[]2024-01-01..2024-12-31', desc: 'All of 2024' },
        { q: '>=2024-03-01',           desc: 'From March 1st 2024' },
        { q: '>last week',             desc: 'Last week' },
        { q: '[]2024-01-15..2024-01-15', desc: 'ES: exact day' }
      ]
    },
    integer: {
      label: 'Integer',
      notes: 'ES: partial search not supported on integers \u2014 use = or >=.',
      notesWarn: true,
      examples: [
        { q: '>=1000000',              desc: '\u2265 1\u00a0MB' },
        { q: '<200000',                desc: '< 200\u00a0KB' },
        { q: '[]100000..5000000',      desc: 'Between 100\u00a0KB and 5\u00a0MB' }
      ]
    },
    uuid: {
      label: 'UUID',
      notes: 'ES: hyphens stripped. ORM/Whoosh: hyphens replaced by _.',
      notesWarn: false,
      examples: [
        { q: '550e8400',               desc: 'Start of UUID' },
        { q: '=550e8400e29b41d4a716446655440000', desc: 'Full UUID (ES, no hyphens)' }
      ]
    },
    boolean: {
      label: 'Boolean',
      notes: 'Only = (exact) is supported. Values: true or false.',
      notesWarn: false,
      examples: [
        { q: '=true',                  desc: 'True value' },
        { q: '=false',                 desc: 'False value' }
      ]
    }
  },

  regexExamples: [
    { pattern: '%invoice_2024_\\d{3}',   desc: 'invoice-2024-001.pdf (hyphens \u2192 _)' },
    { pattern: '%^[A-Z]{2,5}_\\d{4}',    desc: 'Codes: ABC_1234, INV_2024' },
    { pattern: '%report.*(2023|2024)',    desc: 'Reports from 2023 or 2024' },
    { pattern: '%\\d{4}_\\d{2}_\\d{2}',  desc: 'Date in filename: 2024_01_15' },
    { pattern: '%^(contract|invoice)',    desc: 'Starts with contract or invoice' },
    { pattern: '%mao\\.zedong',           desc: 'Name with dot: Mao.Zedong (. escaped)' }
  ],

  wildcardExamples: [
    { pattern: 'report*',        desc: 'Starts with "report"' },
    { pattern: '*2024*',         desc: 'Contains "2024"' },
    { pattern: 'contract*2024*', desc: 'Starts with "contract" and contains "2024"' },
    { pattern: 'invoice_2024_*', desc: 'invoice-2024-XXX (hyphens \u2192 _ in index)' }
  ],

  dateExamples: [
    { q: '[]2024-01-01..2024-12-31', desc: 'All of 2024' },
    { q: '>=2024-03-01',             desc: 'From March 1st 2024' },
    { q: '>last week',               desc: 'Last week' },
    { q: '<yesterday',               desc: 'Before yesterday' },
    { q: '>3 days ago',              desc: 'Within the last 3 days' },
    { q: '[]Jan 2024..Mar 2024',     desc: 'From January to March 2024' }
  ]
};
