/* Pile de pochettes = téléchargements du CV.
   Chaque pochette porte un logo sur sa face supérieure et un sigle sur sa tranche.
   Survol (PC), focus clavier ou premier toucher (mobile) : la pochette sort de la
   pile puis pivote à plat pour faire face à l'écran ; clic, Entrée ou second
   toucher : téléchargement. Projection isométrique recalculée à chaque image.
   Sans JavaScript, chaque pochette reste un simple lien de téléchargement.
   L'animation n'est déclenchée que par le visiteur : elle est jouée même si le
   système demande de réduire les animations. */
(function () {
  var svg = document.querySelector('svg.pile');
  if (!svg) return;
  var NS = 'http://www.w3.org/2000/svg';
  var canHover = matchMedia('(hover: hover)').matches;
  var OUT = [2.3, 2.3, 2.3, 2.0, 1.75]; // distance de sortie par pochette, du bas vers le haut (évite le bandeau du titre)
  var TURN = Math.PI / 4;   // virage à plat : 45° pour faire face à l'écran
  var DUR = 1300;           // ms pour un aller complet
  var INTENT = 140;         // ms de survol avant de déclencher
  var H = 16;               // épaisseur d'une pochette (px SVG)
  var VIEW = [1, -1];       // direction de vue dans le plan (faces visibles)
  var DISPLAY = "font-family:Unbounded,'Arial Black',Arial,sans-serif;font-weight:800";

  /* Logos dessinés dans un repère local 200 × 100 (face supérieure). */
  function doc(x, ink, inside) {
    return '<path d="M' + x + ',14h34l14,14v58h-48z" fill="none" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>' +
      '<path d="M' + (x + 34) + ',14v14h14" fill="none" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>' + (inside || '');
  }
  function word(x, y, s, ink, size) {
    return '<text x="' + x + '" y="' + y + '" fill="' + ink + '" style="' + DISPLAY + ';font-size:' + size + 'px;letter-spacing:-.02em">' + s + '</text>';
  }
  var LOGOS = {
    ats: function (ink) {
      return doc(22, ink, '<path d="M32,46h28M32,58h28M32,70h20" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/>') +
        word(84, 58, 'ATS', ink, 40) + word(86, 82, 'PDF', ink, 18);
    },
    vcf: function (ink) {
      return '<rect x="18" y="22" width="64" height="56" rx="8" fill="none" stroke="' + ink + '" stroke-width="5"/>' +
        '<circle cx="40" cy="44" r="8" fill="' + ink + '"/><path d="M27,68c2-10 24-10 26,0z" fill="' + ink + '"/>' +
        '<path d="M60,42h14M60,54h14" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/>' +
        word(90, 59, 'vCard', ink, 25);
    },
    docx: function (ink) {
      return doc(22, ink, word(31, 72, 'W', ink, 30)) + word(84, 60, 'Word', ink, 34) + word(86, 82, 'DOCX', ink, 15);
    },
    md: function (ink) {
      return '<rect x="14" y="26" width="84" height="50" rx="7" fill="none" stroke="' + ink + '" stroke-width="5"/>' +
        '<path d="M26,66v-30l12,14 12-14v30" fill="none" stroke="' + ink + '" stroke-width="6" stroke-linejoin="round"/>' +
        '<path d="M76,36v24M66,52l10,12 10-12" fill="none" stroke="' + ink + '" stroke-width="6" stroke-linejoin="round"/>' +
        word(108, 62, 'MD', ink, 34);
    },
    json: function (ink) {
      return word(16, 70, '{ }', ink, 48) + word(96, 58, 'JSON', ink, 28) + word(98, 78, 'RESUME', ink, 13);
    }
  };

  function hex(c) { c = c.replace('#', ''); return [0, 2, 4].map(function (i) { return parseInt(c.substr(i, 2), 16); }); }
  function mix(a, b, t) { return 'rgb(' + a.map(function (v, i) { return Math.round(v + (b[i] - v) * t); }).join(',') + ')'; }
  function ease(t) { t = Math.max(0, Math.min(1, t)); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function el(name, attrs) { var e = document.createElementNS(NS, name); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function lum(rgb) { return (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000; }

  var cds = [].slice.call(svg.querySelectorAll('a.dl')).map(function (a, i, arr) {
    var g = a.querySelector('.cd'), slab = g.querySelector('.slab');
    var polys = slab.querySelectorAll('polygon');
    var y0 = parseFloat(g.querySelector('.hit').getAttribute('points').split(' ')[0].split(',')[1]);
    var topRGB = hex(polys[2].getAttribute('fill')), leftRGB = hex(polys[0].getAttribute('fill'));
    var ink = lum(topRGB) < 150 ? '#FFFFFF' : '#52565F';
    var edgeInk = lum(leftRGB) < 150 ? '#FFFFFF' : '#5A2A62';
    var deco = el('g', { 'class': 'deco' });
    var logo = el('g', {}); logo.innerHTML = (LOGOS[a.dataset.fmt] || function () { return ''; })(ink);
    var edge = el('g', {});
    edge.innerHTML = '<text x="100" y="11.5" text-anchor="middle" fill="' + edgeInk + '" style="' + DISPLAY +
      ';font-size:8.5px;letter-spacing:.06em">' + (a.dataset.edge || '') + '</text>';
    deco.appendChild(edge); deco.appendChild(logo); slab.appendChild(deco);
    return {
      a: a, g: g, slab: slab, y0: y0, logo: logo, edge: edge, out: OUT[i] || 2, isTop: i === arr.length - 1,
      left: leftRGB, right: hex(polys[1].getAttribute('fill')),
      top: polys[2], sides: [polys[0], polys[1]],
      p: 0, target: 0, last: 0, raf: 0
    };
  });

  function render(c) {
    var d = c.out * ease(c.p / .6), a = TURN * ease((c.p - .4) / .6);
    var co = Math.cos(a), si = Math.sin(a), cx = 135, cy = c.y0 + 60;
    var base = [[1, 1], [1, -1], [-1, -1], [-1, 1]];
    var normals = [[1, 0], [0, -1], [-1, 0], [0, 1]];
    function proj(x, y, z) {
      var X = x * co - y * si, Y = x * si + y * co - d;
      return [cx + 60 * (X + Y), cy + 30 * (X - Y) + z];
    }
    var top = base.map(function (p) { return proj(p[0], p[1], 0); });
    var bot = base.map(function (p) { return proj(p[0], p[1], H); });
    function pts(arr) { return arr.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' '); }
    function mat(o, ex, ey, w, h) {
      return 'matrix(' + [(ex[0] - o[0]) / w, (ex[1] - o[1]) / w, (ey[0] - o[0]) / h, (ey[1] - o[1]) / h, o[0], o[1]]
        .map(function (v) { return v.toFixed(4); }).join(',') + ')';
    }
    c.top.setAttribute('points', pts(top));
    var used = 0;
    for (var k = 0; k < 4 && used < 2; k++) {
      var n = normals[k], nx = n[0] * co - n[1] * si, ny = n[0] * si + n[1] * co;
      if (nx * VIEW[0] + ny * VIEW[1] <= 1e-6) continue;
      var phi = Math.atan2(ny, nx);
      var t = Math.max(0, Math.min(1, (phi + Math.PI / 2) / (Math.PI / 2)));
      var k1 = (k + 1) % 4, side = c.sides[used++];
      side.setAttribute('points', pts([top[k], top[k1], bot[k1], bot[k]]));
      side.setAttribute('fill', mix(c.left, c.right, t));
    }
    for (; used < 2; used++) c.sides[used].setAttribute('points', '');
    // Logo : repère 200 × 100 plaqué sur la face supérieure ; sigle : 200 × 16 sur la tranche claire
    c.logo.setAttribute('transform', mat(top[3], top[0], top[2], 200, 100));
    c.edge.setAttribute('transform', mat(top[2], top[1], bot[2], 200, H));
    // Logo des pochettes recouvertes : masqué au repos (seuls des morceaux dépasseraient), apparaît en sortant
    if (!c.isTop) c.logo.setAttribute('opacity', Math.min(1, c.p * 3).toFixed(2));
    c.slab.style.filter = c.p > .02 ? 'drop-shadow(6px -3px 6px rgba(0,0,0,' + (.25 * Math.min(1, c.p * 2)).toFixed(2) + '))' : '';
  }

  function tick(c) {
    return function (now) {
      var dt = Math.min(64, now - (c.last || now)); c.last = now;
      var step = dt / DUR * (c.target > c.p ? 1 : -1);
      c.p = c.target > c.p ? Math.min(c.target, c.p + step) : Math.max(c.target, c.p + step);
      render(c);
      if (c.p !== c.target) c.raf = requestAnimationFrame(tick(c)); else { c.raf = 0; c.last = 0; }
    };
  }
  function go(c, target) {
    c.target = target;
    if (!c.raf) { c.last = 0; c.raf = requestAnimationFrame(tick(c)); }
  }
  // Distance de sortie limitée pour que la pochette ne recouvre pas le bandeau du titre.
  var badge = document.querySelector('.hero .role strong');
  function fitOut(c) {
    var d = OUT[cds.indexOf(c)] || 2;
    if (!badge) return d;
    var s = svg.getBoundingClientRect(), b = badge.getBoundingClientRect(), k = s.width / 270;
    if (!k) return d;
    var bl = (b.left - s.left) / k, br = (b.right - s.left) / k, bt = (b.top - s.top) / k, bb = (b.bottom - s.top) / k;
    for (; d > .9; d -= .05) {
      var L = 50 - 60 * d, R = 220 - 60 * d, T = c.y0 + 60 + 30 * d - 43, B = c.y0 + 60 + 30 * d + 43 + H;
      if (L > br + 6 || R < bl || B < bt || T > bb) break;
    }
    return d;
  }
  function only(c) {
    cds.forEach(function (o) { if (o !== c && o.target) go(o, 0); });
    if (c) { if (!c.p) c.out = fitOut(c); go(c, 1); }
  }

  // Téléchargement : un lien HTML temporaire garantit l'attribut download (même origine).
  function download(c) {
    var h = document.createElement('a');
    h.href = c.a.getAttribute('href'); h.download = c.a.getAttribute('download') || '';
    document.body.appendChild(h); h.click(); h.remove();
  }

  var timer = 0, active = null;
  function arm(c) {
    clearTimeout(timer);
    timer = setTimeout(function () { if (active !== c) { active = c; only(c); } }, INTENT);
  }

  cds.forEach(function (c) {
    render(c);
    // Focus clavier uniquement (un toucher donne aussi le focus : ne pas l'interpréter comme une sortie)
    c.a.addEventListener('focus', function () {
      var kb = true; try { kb = c.a.matches(':focus-visible'); } catch (e) {}
      if (kb) { active = c; only(c); }
    });
    c.a.addEventListener('blur', function () { if (active === c) { active = null; go(c, 0); } });
    if (canHover) {
      // Seule la zone de repos (.hit) réagit à la souris : pas de réaction en chaîne.
      c.g.addEventListener('mouseenter', function () { arm(c); });
      c.a.addEventListener('click', function (e) { e.preventDefault(); download(c); });
    } else {
      c.a.addEventListener('click', function (e) {
        e.preventDefault(); e.stopPropagation();
        if (c.target === 1) download(c); else { active = c; only(c); }
      });
    }
  });
  if (canHover) svg.addEventListener('mouseleave', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { active = null; only(null); }, 250);
  });
  else document.addEventListener('click', function () { active = null; only(null); });
})();
