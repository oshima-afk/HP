import { works, categories } from './works-data.js';

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}

var groups = categories
  .map(function (c) {
    return {
      id: c.id,
      label: c.label,
      kicker: c.kicker,
      items: works
        .filter(function (w) { return w.category === c.id; })
        .map(function (w) {
          return {
            id: w.id,
            image: w.image || '',
            title: w.title,
            detail: w.detail,
            categoryLabel: c.label,
            meta: w.place + '　／　' + w.year,
          };
        }),
    };
  })
  .filter(function (g) { return g.items.length > 0; });

var tabs = groups.map(function (g) {
  return { href: '#' + g.id, label: g.label, count: g.items.length };
});

var tabsEl = document.getElementById('works-tabs');
if (tabsEl) {
  tabsEl.innerHTML = tabs
    .map(function (tab) {
      return (
        '<a href="' + tab.href + '" style="position: relative; display: grid; place-items: center; text-align: center; text-decoration: none; color: var(--color-text); border: 1px solid var(--color-accent-600); border-radius: var(--radius-md); padding: 20px 18px; min-height: 84px; font-size: clamp(15px, 1.7vw, 18px); letter-spacing: 0.1em; line-height: 1.6; background: var(--color-bg);" style-hover="background: var(--color-accent-100);">' +
        escapeHtml(tab.label) +
        '<span style="position: absolute; left: 24px; bottom: -16px; width: 1px; height: 16px; background: var(--color-accent-600); transform: rotate(-28deg); transform-origin: top;"></span>' +
        '<span style="position: absolute; right: 14px; top: 10px; font-family: var(--font-heading); font-size: 12px; color: var(--color-accent-600); font-feature-settings: \'tnum\';">' + tab.count + '</span>' +
        '</a>'
      );
    })
    .join('');
}

var groupsEl = document.getElementById('works-groups');
if (groupsEl) {
  groupsEl.innerHTML = groups
    .map(function (group) {
      var items = group.items
        .map(function (item) {
          var media = item.image
            ? '<img src="' + escapeHtml(item.image) + '" alt="' + escapeHtml(item.title) + '" style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover;">'
            : '<div class="ph-slot" role="img" aria-label="施工写真" data-slot="' + escapeHtml(item.id) + '"><span>施工写真</span></div>';
          return (
            '<figure style="margin: 0; display: grid; gap: 14px;">' +
            '<div class="plate" style="aspect-ratio: 3 / 2; border-radius: var(--radius-md); position:relative; overflow:hidden">' + media + '</div>' +
            '<figcaption style="display: grid; gap: 8px;">' +
            '<span class="tag tag-outline" style="justify-self: start;">' + escapeHtml(item.categoryLabel) + '</span>' +
            '<h3 style="font-size: 17px; letter-spacing: 0.05em; line-height: 1.6; margin: 0; color: var(--color-text);">' + escapeHtml(item.title) + '</h3>' +
            '<p style="margin: 0; font-size: 12.5px; line-height: 1.95; color: var(--color-neutral-800); font-feature-settings: \'tnum\';">' + escapeHtml(item.meta) + '</p>' +
            '<p style="margin: 0; font-size: 12.5px; line-height: 1.95; color: var(--color-neutral-800);">' + escapeHtml(item.detail) + '</p>' +
            '</figcaption></figure>'
          );
        })
        .join('');
      return (
        '<section id="' + group.id + '" style="padding: clamp(36px, 5vw, 72px) clamp(20px, 5vw, 64px); border-top: 1px solid var(--color-divider);">' +
        '<div style="display: grid; justify-items: center; gap: 10px; text-align: center; margin-bottom: clamp(32px, 5vw, 56px);">' +
        '<p style="margin: 0; font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: var(--color-neutral-600);">' + escapeHtml(group.kicker) + '</p>' +
        '<h2 style="font-size: clamp(24px, 3vw, 36px); margin: 0; letter-spacing: 0.1em;">' + escapeHtml(group.label) + '</h2>' +
        '<span style="width: 56px; height: 1px; background: var(--color-accent); margin-top: 6px;"></span>' +
        '</div>' +
        '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 290px), 1fr)); gap: clamp(22px, 3vw, 40px); max-width: 1120px; margin: 0 auto;">' + items + '</div>' +
        '</section>'
      );
    })
    .join('');

  // the hover-state script in site.js already ran by the time this module
  // finishes fetching works-data.js, so wire up any style-hover tabs here too
  groupsEl.parentElement.querySelectorAll('[style-hover]').forEach(function (el) {
    var base = el.getAttribute('style') || '';
    var hover = el.getAttribute('style-hover');
    el.addEventListener('mouseenter', function () { el.style.cssText = base + ';' + hover; });
    el.addEventListener('mouseleave', function () { el.style.cssText = base; });
  });
}

document.querySelectorAll('#works-tabs [style-hover]').forEach(function (el) {
  var base = el.getAttribute('style') || '';
  var hover = el.getAttribute('style-hover');
  el.addEventListener('mouseenter', function () { el.style.cssText = base + ';' + hover; });
  el.addEventListener('mouseleave', function () { el.style.cssText = base; });
});
