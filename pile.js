/* Pile de pochettes : au survol (ou au toucher), une pochette sort de la pile
   puis pivote à plat pour se présenter face à l'écran. Projection isométrique
   recalculée à chaque image ; sans JavaScript, la pile reste statique. */
(function () {
  var svg = document.querySelector('svg.pile');
  if (!svg) return;
  var NS = 'http://www.w3.org/2000/svg';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var canHover = matchMedia('(hover: hover)').matches;
  var OUT = 2.3;            // distance de sortie (unités « monde », 1 = demi-côté)
  var TURN = Math.PI / 4;   // virage à plat : 45° pour faire face à l'écran
  var DUR = 850;            // ms pour un aller complet
  var H = 16;               // épaisseur d'une pochette (px SVG)
  var VIEW = [1, -1];       // direction de vue dans le plan (faces visibles)

  function hex(c) { c = c.replace('#', ''); return [0, 2, 4].map(function (i) { return parseInt(c.substr(i, 2), 16); }); }
  function mix(a, b, t) { return 'rgb(' + a.map(function (v, i) { return Math.round(v + (b[i] - v) * t); }).join(',') + ')'; }
  function ease(t) { t = Math.max(0, Math.min(1, t)); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

  var cds = [].slice.call(svg.querySelectorAll('.cd')).map(function (g) {
    var slab = g.querySelector('.slab');
    var polys = slab.querySelectorAll('polygon');
    var y0 = parseFloat(g.querySelector('.hit').getAttribute('points').split(' ')[0].split(',')[1]);
    var c = {
      g: g, slab: slab, y0: y0,
      left: hex(polys[0].getAttribute('fill')), right: hex(polys[1].getAttribute('fill')),
      top: polys[2], sides: [polys[0], polys[1]],
      p: 0, target: 0, last: 0, raf: 0
    };
    return c;
  });

  function render(c) {
    var d = OUT * ease(c.p / .6), a = TURN * ease((c.p - .4) / .6);
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
    c.top.setAttribute('points', pts(top));
    var used = 0;
    for (var k = 0; k < 4 && used < 2; k++) {
      var n = normals[k], nx = n[0] * co - n[1] * si, ny = n[0] * si + n[1] * co;
      if (nx * VIEW[0] + ny * VIEW[1] <= 1e-6) continue;
      var phi = Math.atan2(ny, nx);                       // -90° = face claire, 0° = face sombre
      var t = Math.max(0, Math.min(1, (phi + Math.PI / 2) / (Math.PI / 2)));
      var k1 = (k + 1) % 4, el = c.sides[used++];
      el.setAttribute('points', pts([top[k], top[k1], bot[k1], bot[k]]));
      el.setAttribute('fill', mix(c.left, c.right, t));
    }
    for (; used < 2; used++) c.sides[used].setAttribute('points', '');
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
    if (reduce) { c.p = target; render(c); return; }
    if (!c.raf) { c.last = 0; c.raf = requestAnimationFrame(tick(c)); }
  }

  cds.forEach(function (c) {
    render(c);
    if (canHover) {
      c.g.addEventListener('mouseenter', function () { go(c, 1); });
      c.g.addEventListener('mouseleave', function () { go(c, 0); });
    } else {
      c.g.addEventListener('click', function (e) {
        e.stopPropagation();
        var open = c.target === 1;
        cds.forEach(function (o) { if (o.target) go(o, 0); });
        if (!open) go(c, 1);
      });
    }
  });
  if (!canHover) document.addEventListener('click', function () { cds.forEach(function (o) { if (o.target) go(o, 0); }); });
})();
