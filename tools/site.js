(function () {
  // close the Sections menu after a choice
  var menu = document.getElementById('sections-menu');
  if (menu) menu.addEventListener('click', function (e) { if (e.target.closest('a')) menu.open = false; });

  // hint that wide tables scroll sideways on phones
  document.querySelectorAll('.tbl.wide').forEach(function (t) {
    var p = document.createElement('p'); p.className = 'scroll-hint'; p.textContent = 'Swipe the table sideways to see every column.';
    t.after(p);
  });

  // copy buttons
  document.querySelectorAll('.copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var text = b.getAttribute('data-copy'), label = b.textContent;
      var done = function () { b.textContent = 'Copied'; b.classList.add('done'); setTimeout(function () { b.textContent = label; b.classList.remove('done'); }, 1600); };
      try {
        navigator.clipboard.writeText(text).then(done, function () { select(b); });
      } catch (e) { select(b); }
    });
  });
  function select(b) {
    var addr = b.parentElement.querySelector('.addr') || b.previousElementSibling;
    if (!addr) return;
    var r = document.createRange(); r.selectNodeContents(addr);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }

  // highlight the current section in the contents rail
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  var byId = {}; links.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
  var heads = Array.prototype.slice.call(document.querySelectorAll('.report h2, .report h3')).filter(function (h) { return byId[h.id]; });
  if ('IntersectionObserver' in window && heads.length) {
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          if (current) current.classList.remove('active');
          current = byId[en.target.id]; if (current) current.classList.add('active');
        }
      });
    }, { rootMargin: '-15% 0px -75% 0px' });
    heads.forEach(function (h) { io.observe(h); });
  }
})();
