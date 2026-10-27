// Streetak: the style meter. Tap a skill, the meter fills; four skills open a fire shot.
(function () {
  var pad = document.querySelector('.skill-pad');
  var meter = document.querySelector('.meter');
  if (!pad || !meter) return;
  var arcs = meter.querySelectorAll('.m-arc');
  var flash = meter.querySelector('.m-flash');
  var hint = document.querySelector('.m-hint');
  var t = {};
  try { t = JSON.parse(meter.getAttribute('data-t')) || {}; } catch (e) {}
  var level = 0;

  function replay(el, cls) {
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  }

  pad.addEventListener('click', function (e) {
    var b = e.target.closest('.skill');
    if (!b) return;
    level = level >= arcs.length ? 1 : level + 1;
    for (var i = 0; i < arcs.length; i++) arcs[i].classList.toggle('on', i < level);
    var full = level === arcs.length;
    meter.classList.toggle('is-full', full);
    meter.setAttribute('data-level', String(level));
    flash.textContent = b.getAttribute('data-name');
    replay(flash, 'go');
    var prev = pad.querySelector('.skill.hit');
    if (prev && prev !== b) prev.classList.remove('hit');
    replay(b, 'hit');
    if (hint) hint.textContent = full ? (t.full || '') : (t.level || '').replace('{n}', level);
  });
})();
