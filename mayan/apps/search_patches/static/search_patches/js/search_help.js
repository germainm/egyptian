/**
 * search_help.js — Moteur principal d'aide contextuelle pour Mayan EDMS
 *
 * Architecture i18n :
 *   - Ce fichier contient toute la logique UI, CSS et le moteur de détection
 *   - Les traductions sont dans des fichiers séparés : search_help.{lang}.js
 *   - La langue est détectée depuis html[lang] (ex: fr, fr-ca, en, es, pt-br)
 *   - Fallback : anglais si la langue n'est pas supportée
 *
 * Fichiers de langue requis dans le même répertoire :
 *   search_help.fr.js  search_help.en.js  search_help.es.js  search_help.pt.js
 */

(function () {
  'use strict';

  // ── 1. DÉTECTION DE LA LANGUE ────────────────────────────────────────────────

  var SUPPORTED_LANGS = ['fr', 'en', 'es', 'pt'];
  var DEFAULT_LANG = 'en';

  function detectLang() {
    var htmlLang = document.documentElement.lang || '';
    var lang = htmlLang.toLowerCase().split('-')[0].split('_')[0];
    return SUPPORTED_LANGS.indexOf(lang) >= 0 ? lang : DEFAULT_LANG;
  }

  // ── 2. CHARGEMENT DYNAMIQUE DU FICHIER DE LANGUE ────────────────────────────

  function getScriptBaseUrl() {
    var scripts = document.querySelectorAll('script[src*="search_help"]');
    for (var i = 0; i < scripts.length; i++) {
      var src = scripts[i].src;
      if (src && src.indexOf('search_help') >= 0) {
        return src.replace(/search_help[^/]*\.js(\?.*)?$/, '');
      }
    }
    return '/static/search_patches/js/';
  }

  function loadI18n(lang, callback) {
    if (window.SEARCH_HELP_I18N) {
      callback(window.SEARCH_HELP_I18N);
      return;
    }

    var baseUrl = getScriptBaseUrl();
    var url = baseUrl + 'search_help.' + lang + '.js';

    var script = document.createElement('script');
    script.src = url;
    script.onload = function() {
      if (window.SEARCH_HELP_I18N) {
        callback(window.SEARCH_HELP_I18N);
      } else if (lang !== DEFAULT_LANG) {
        window.SEARCH_HELP_I18N = null;
        loadI18n(DEFAULT_LANG, callback);
      }
    };
    script.onerror = function() {
      if (lang !== DEFAULT_LANG) {
        loadI18n(DEFAULT_LANG, callback);
      }
    };
    document.head.appendChild(script);
  }

  // ── 3. MATRICE DES OPÉRATEURS PAR TYPE DE CHAMP ──────────────────────────────

  var FIELD_OPERATORS = {
    text:     { es: ['partial','exact','phrase','fuzzy','regex','gt','lt','gte','lte'],
                orm: ['partial','exact','phrase','fuzzy','regex','gt','lt','gte','lte'],
                wh:  ['partial','exact','phrase','fuzzy','regex','gt','lt','gte','lte'] },
    datetime: { es:  ['range','range_excl','gt','lt','gte','lte'],
                orm: ['exact','range','range_excl','gt','lt','gte','lte'],
                wh:  ['exact','range','range_excl','gt','lt','gte','lte'] },
    integer:  { es:  ['exact','range','range_excl','gt','lt','gte','lte'],
                orm: ['partial','exact','range','range_excl','gt','lt','gte','lte'],
                wh:  ['exact','range','range_excl','gt','lt','gte','lte'] },
    uuid:     { es: ['exact','partial','regex'], orm: ['exact','partial','regex'], wh: ['exact','partial','regex'] },
    boolean:  { es: ['exact'], orm: ['exact'], wh: ['exact'] }
  };

  var FIELD_TYPE_MAP = {
    'datetime_created': 'datetime', 'datetime_published': 'datetime',
    'files__size': 'integer', 'file__size': 'integer', 'size': 'integer',
    'id': 'integer', 'document__id': 'integer', 'page_number': 'integer',
    'uuid': 'uuid', 'document__uuid': 'uuid',
    'versions__active': 'boolean'
  };

  function getFieldType(n) { return FIELD_TYPE_MAP[n] || 'text'; }
  function getBackendKey(b) {
    if (b === 'elasticsearch') return 'es';
    if (b === 'django') return 'orm';
    return 'wh';
  }
  function detectBackend() {
    var m = document.querySelector('meta[name="search-backend"]');
    if (m) return m.getAttribute('content');
    return window.MAYAN_SEARCH_BACKEND || 'elasticsearch';
  }

  // ── 4. CSS BOOTSTRAP 3 CLAIR ─────────────────────────────────────────────────

  var CSS = [
    '.sh-tooltip-btn{display:inline-flex;align-items:center;justify-content:center;',
    'width:16px;height:16px;background:#5b9bd5;border:1px solid #2e6da4;border-radius:50%;',
    'color:#fff;font-size:10px;font-weight:700;cursor:pointer;margin-left:5px;',
    'vertical-align:middle;flex-shrink:0;line-height:1;font-family:monospace;}',
    '.sh-tooltip-btn:hover{background:#2e6da4;}',
    '.sh-panel{display:none;position:absolute;z-index:9999;background:#fff;',
    'border:1px solid #ddd;border-radius:4px;min-width:360px;max-width:480px;',
    'box-shadow:0 6px 18px rgba(0,0,0,.15);',
    'font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:13px;color:#333;}',
    '.sh-panel.sh-visible{display:block;}',
    '.sh-panel-header{background:#f5f5f5;border-bottom:1px solid #ddd;padding:8px 12px;',
    'border-radius:4px 4px 0 0;display:flex;align-items:center;justify-content:space-between;}',
    '.sh-panel-title{font-size:12px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:.04em;}',
    '.sh-panel-close{cursor:pointer;color:#999;font-size:16px;line-height:1;}',
    '.sh-panel-close:hover{color:#333;}',
    '.sh-panel-body{padding:10px 12px;}',
    '.sh-field-type{font-size:11px;background:#e8f4f8;border:1px solid #b8dce8;border-radius:3px;',
    'padding:1px 6px;color:#31708f;font-family:monospace;margin-bottom:8px;display:inline-block;}',
    '.sh-note{font-size:11px;color:#666;margin-bottom:8px;line-height:1.5;}',
    '.sh-note.sh-warn{color:#8a6d3b;background:#fcf8e3;border:1px solid #faebcc;border-radius:3px;padding:4px 8px;}',
    '.sh-ops-title{font-size:10px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;}',
    '.sh-op-row{display:flex;align-items:flex-start;gap:6px;padding:3px 0;border-bottom:1px solid #f0f0f0;font-size:12px;}',
    '.sh-op-row:last-child{border-bottom:none;}',
    '.sh-op-alias{font-family:monospace;color:#c7254e;background:#f9f2f4;padding:0 3px;border-radius:2px;min-width:52px;font-weight:700;flex-shrink:0;}',
    '.sh-op-label{color:#333;flex:1;}',
    '.sh-op-example{font-family:monospace;font-size:10px;color:#3c763d;background:#dff0d8;padding:1px 4px;border-radius:3px;border:1px solid #d6e9c6;}',
    '.sh-examples-title{font-size:10px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:.08em;margin:8px 0 4px;}',
    '.sh-example-row{display:flex;gap:8px;padding:2px 0;font-size:11px;align-items:flex-start;}',
    '.sh-example-q{font-family:monospace;color:#8b008b;min-width:160px;flex-shrink:0;background:#f9f2f4;padding:0 3px;border-radius:2px;}',
    '.sh-example-desc{color:#666;}',
    '.sh-backend-badge{font-size:10px;font-weight:700;padding:1px 6px;border-radius:3px;font-family:monospace;margin-left:4px;}',
    '.sh-be-es{background:#d9edf7;color:#31708f;border:1px solid #bce8f1;}',
    '.sh-be-orm{background:#dff0d8;color:#3c763d;border:1px solid #d6e9c6;}',
    '.sh-be-wh{background:#fcf8e3;color:#8a6d3b;border:1px solid #faebcc;}'
  ].join('');

  function injectCSS() {
    if (document.getElementById('sh-styles')) return;
    var s = document.createElement('style');
    s.id = 'sh-styles';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  // ── 5. CONSTRUCTION DES PANNEAUX ─────────────────────────────────────────────

  function buildPanel(fieldName, backend, i18n) {
    var ft = getFieldType(fieldName);
    var fi = i18n.fieldTypes[ft] || i18n.fieldTypes['text'];
    var bk = getBackendKey(backend);
    var ops = (FIELD_OPERATORS[ft] || FIELD_OPERATORS['text'])[bk];

    var blabels = { elasticsearch: 'ES', django: 'ORM', whoosh: 'WH' };
    var bclass  = { elasticsearch: 'sh-be-es', django: 'sh-be-orm', whoosh: 'sh-be-wh' };

    var html = '<div class="sh-panel-header">'
      + '<span class="sh-panel-title">' + i18n.ui.panelTitlePrefix + fieldName + '</span>'
      + '<span class="sh-backend-badge ' + (bclass[backend] || 'sh-be-es') + '">' + (blabels[backend] || 'ES') + '</span>'
      + '<span class="sh-panel-close" data-sh-close>' + i18n.ui.closePanel + '</span>'
      + '</div><div class="sh-panel-body">'
      + '<span class="sh-field-type">' + fi.label + '</span>';

    if (fi.notes) {
      html += '<div class="sh-note' + (fi.notesWarn ? ' sh-warn' : '') + '">' + fi.notes + '</div>';
    }

    html += '<div class="sh-ops-title">' + i18n.ui.opsTitle + '</div>';
    ops.forEach(function(k) {
      var op = i18n.operators[k];
      if (!op) return;
      html += '<div class="sh-op-row">'
        + '<span class="sh-op-alias">' + op.alias + '</span>'
        + '<span class="sh-op-label">' + op.label + '</span>'
        + '<span class="sh-op-example">' + op.example + '</span>'
        + '</div>';
    });

    // Exemples contextuels : priorité aux exemples par champ, fallback sur le type
    var examples = (i18n.fieldExamples && i18n.fieldExamples[fieldName])
      ? i18n.fieldExamples[fieldName]
      : (fi.examples || []);

    if (examples.length) {
      html += '<div class="sh-examples-title">' + i18n.ui.examplesTitle + '</div>';
      examples.forEach(function(ex) {
        html += '<div class="sh-example-row">'
          + '<span class="sh-example-q">' + ex.q + '</span>'
          + '<span class="sh-example-desc">' + ex.desc + '</span>'
          + '</div>';
      });
    }
    html += '</div>';
    return html;
  }

  function buildGlobalPanel(backend, i18n) {
    var blabels = { elasticsearch: 'Elasticsearch', django: 'Django ORM', whoosh: 'Whoosh' };
    var bcolors = { elasticsearch: '#31708f', django: '#3c763d', whoosh: '#8a6d3b' };
    var bbg     = { elasticsearch: '#d9edf7', django: '#dff0d8', whoosh: '#fcf8e3' };
    var bl = blabels[backend] || 'Elasticsearch';
    var bc = bcolors[backend] || '#31708f';
    var bb = bbg[backend]     || '#d9edf7';

    var ss = 'font-size:10px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;';
    var cs = 'color:#c7254e;background:#f9f2f4;padding:1px 4px;border-radius:2px;display:inline-block;';

    var html = '<div class="panel panel-default" style="margin-top:16px;">'
      + '<div class="panel-heading" style="display:flex;align-items:center;justify-content:space-between;">'
      + '<strong>' + i18n.ui.globalTitle + '</strong>'
      + '<span style="font-size:11px;padding:2px 8px;border-radius:3px;background:' + bb + ';color:' + bc + ';border:1px solid ' + bc + ';">'
      + i18n.ui.backendLabel + '<strong>' + bl + '</strong></span>'
      + '</div><div class="panel-body">';

    html += '<p style="' + ss + '">' + i18n.ui.prefixesTitle + '</p>'
      + '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:4px;margin-bottom:14px;">';
    ['exact','phrase','fuzzy','regex','gt','gte','lt','lte','range','range_excl'].forEach(function(k) {
      var op = i18n.operators[k];
      if (!op) return;
      html += '<div style="display:flex;align-items:center;gap:6px;padding:3px 8px;background:#f9f9f9;border:1px solid #eee;border-radius:3px;">'
        + '<code style="' + cs + 'min-width:36px;text-align:center;font-size:11px;">' + op.alias + '</code>'
        + '<span style="font-size:11px;color:#555;">' + op.label + '</span>'
        + '</div>';
    });
    html += '</div>';

    html += '<p style="' + ss + '">' + i18n.ui.regexTitle + '</p>'
      + '<div class="well well-sm" style="margin-bottom:10px;">'
      + '<div class="alert alert-warning" style="padding:4px 8px;margin-bottom:6px;font-size:11px;">' + i18n.ui.regexWarning + '</div>';
    (i18n.regexExamples || []).forEach(function(ex) {
      html += '<div style="display:flex;gap:10px;padding:2px 0;font-size:12px;">'
        + '<code style="' + cs + 'min-width:200px;flex-shrink:0;">' + ex.pattern + '</code>'
        + '<span class="text-muted">' + ex.desc + '</span></div>';
    });
    html += '</div>';

    html += '<p style="' + ss + '">' + i18n.ui.wildcardsTitle + '</p>'
      + '<div class="well well-sm" style="margin-bottom:10px;">'
      + '<p class="text-muted" style="font-size:11px;margin-bottom:4px;">' + i18n.ui.wildcardsNote + '</p>';
    (i18n.wildcardExamples || []).forEach(function(ex) {
      html += '<div style="display:flex;gap:10px;padding:2px 0;font-size:12px;">'
        + '<code style="' + cs + 'min-width:180px;flex-shrink:0;">' + ex.pattern + '</code>'
        + '<span class="text-muted">' + ex.desc + '</span></div>';
    });
    html += '</div>';

    html += '<p style="' + ss + '">' + i18n.ui.datesTitle + '</p>'
      + '<div class="well well-sm">';
    (i18n.dateExamples || []).forEach(function(ex) {
      html += '<div style="display:flex;gap:10px;padding:2px 0;font-size:12px;">'
        + '<code style="' + cs + 'min-width:200px;flex-shrink:0;">' + ex.q + '</code>'
        + '<span class="text-muted">' + ex.desc + '</span></div>';
    });
    html += '</div></div></div>';
    return html;
  }

  // ── 6. INITIALISATION DU FORMULAIRE ─────────────────────────────────────────

  function initWithI18n(i18n) {
    var isAdvanced = window.location.href.indexOf('search/advanced') >= 0 ||
                     window.location.href.indexOf('search/results') >= 0;
    if (!isAdvanced) return;

    var form = null;
    var allForms = document.querySelectorAll('form[method="get"]');
    for (var i = 0; i < allForms.length; i++) {
      if (allForms[i].querySelector('fieldset')) { form = allForms[i]; break; }
    }
    if (!form) return;

    if (form.dataset.shInit === '1') return;
    form.dataset.shInit = '1';

    injectCSS();
    var backend = detectBackend();

    var floatingPanel = document.getElementById('sh-floating-panel');
    if (!floatingPanel) {
      floatingPanel = document.createElement('div');
      floatingPanel.className = 'sh-panel';
      floatingPanel.id = 'sh-floating-panel';
      document.body.appendChild(floatingPanel);

      document.addEventListener('mousedown', function(e) {
        if (e.target.hasAttribute('data-sh-field')) return;
        if (floatingPanel.contains(e.target)) return;
        floatingPanel.classList.remove('sh-visible');
      });
    }

    form.querySelectorAll('fieldset input[type="search"], fieldset input[type="text"]').forEach(function(input) {
      var fn = input.name;
      if (!fn || fn.charAt(0) === '_') return;

      var fg = input.closest('.form-group');
      if (!fg) return;
      var lbl = fg.querySelector('label');

      var btn = document.createElement('span');
      btn.className = 'sh-tooltip-btn';
      btn.textContent = i18n.ui.helpButtonText;
      btn.setAttribute('data-sh-field', fn);
      btn.title = i18n.ui.helpButtonTitle;

      if (lbl) { lbl.appendChild(btn); }
      else { input.insertAdjacentElement('afterend', btn); }

      btn.addEventListener('mousedown', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var isVis = floatingPanel.classList.contains('sh-visible') && floatingPanel.dataset.field === fn;
        if (isVis) { floatingPanel.classList.remove('sh-visible'); return; }

        floatingPanel.innerHTML = buildPanel(fn, backend, i18n);
        floatingPanel.dataset.field = fn;
        floatingPanel.classList.add('sh-visible');

        var rect = btn.getBoundingClientRect();
        var st = window.pageYOffset || document.documentElement.scrollTop;
        floatingPanel.style.top  = (rect.bottom + st + 4) + 'px';
        floatingPanel.style.left = Math.max(4, rect.left - 100) + 'px';

        var cb = floatingPanel.querySelector('[data-sh-close]');
        if (cb) cb.addEventListener('mousedown', function(ev) {
          ev.stopPropagation();
          floatingPanel.classList.remove('sh-visible');
        });
      });
    });

    if (form.querySelector('.sh-toggle-btn')) return;

    var gc = document.createElement('div');
    gc.innerHTML = buildGlobalPanel(backend, i18n);
    var hd = gc.querySelector('div');
    if (hd) hd.style.display = 'none';

    var tb = document.createElement('button');
    tb.type = 'button';
    tb.className = 'sh-toggle-btn btn btn-default btn-sm';
    tb.textContent = i18n.ui.toggleShow;
    tb.style.marginTop = '12px';

    tb.addEventListener('click', function() {
      if (!hd) return;
      if (hd.style.display === 'none') {
        hd.style.display = 'block';
        tb.textContent = i18n.ui.toggleHide;
      } else {
        hd.style.display = 'none';
        tb.textContent = i18n.ui.toggleShow;
      }
    });

    var fss = form.querySelectorAll('fieldset');
    var lfs = fss[fss.length - 1];
    if (lfs && lfs.parentNode) {
      lfs.parentNode.insertBefore(tb, lfs.nextSibling);
      lfs.parentNode.insertBefore(gc, tb.nextSibling);
    } else {
      form.appendChild(tb);
      form.appendChild(gc);
    }
  }

  // ── 7. POINT D'ENTRÉE ────────────────────────────────────────────────────────

  function init() {
    var isAdvanced = window.location.href.indexOf('search/advanced') >= 0 ||
                     window.location.href.indexOf('search/results') >= 0;
    if (!isAdvanced) return;

    var hasForm = false;
    document.querySelectorAll('form[method="get"]').forEach(function(f) {
      if (f.querySelector('fieldset')) hasForm = true;
    });
    if (!hasForm) return;

    var lang = detectLang();
    if (window.SEARCH_HELP_LANG && window.SEARCH_HELP_LANG !== lang) {
      window.SEARCH_HELP_I18N = null;
    }
    window.SEARCH_HELP_LANG = lang;

    loadI18n(lang, function(i18n) { initWithI18n(i18n); });
  }

  function waitForForm() {
    var attempts = 0;
    var timer = setInterval(function() {
      attempts++;
      if (window.location.href.indexOf('search') < 0) { clearInterval(timer); return; }
      var hasForm = false;
      document.querySelectorAll('form[method="get"]').forEach(function(f) {
        if (f.querySelector('fieldset')) hasForm = true;
      });
      if (hasForm) { clearInterval(timer); init(); }
      if (attempts > 50) clearInterval(timer);
    }, 100);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForForm);
  } else {
    waitForForm();
  }

  document.addEventListener('mayan:content-loaded', function() {
    setTimeout(init, 200);
  });

  if (window.MutationObserver) {
    var observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(m) {
        if (m.addedNodes.length) {
          var hf = Array.from(m.addedNodes).some(function(n) {
            return n.nodeType === 1 && n.querySelector && n.querySelector('fieldset input');
          });
          if (hf) setTimeout(init, 100);
        }
      });
    });
    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    } else {
      document.addEventListener('DOMContentLoaded', function() {
        if (document.body) observer.observe(document.body, { childList: true, subtree: true });
      });
    }
  }

}());
