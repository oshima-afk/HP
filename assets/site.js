document.addEventListener('DOMContentLoaded', function () {
  // Hover states for elements carrying a style-hover attribute (ported from
  // the design-canvas export, which relied on its own editor runtime for this).
  document.querySelectorAll('[style-hover]').forEach(function (el) {
    var base = el.getAttribute('style') || '';
    var hover = el.getAttribute('style-hover');
    el.addEventListener('mouseenter', function () { el.style.cssText = base + ';' + hover; });
    el.addEventListener('mouseleave', function () { el.style.cssText = base; });
  });

  // Founding-year counter (creation, {{years}} anniversary in the original).
  document.querySelectorAll('.js-years').forEach(function (el) {
    var founded = Number(el.dataset.founded);
    if (founded) el.textContent = String(new Date().getFullYear() - founded);
  });

  // Contact page: keep submit disabled until the privacy checkbox is agreed.
  var agree = document.getElementById('cf-agree');
  var submitBtn = document.getElementById('cf-submit');
  var cfNote = document.getElementById('cf-note');
  if (agree && submitBtn) {
    var syncAgree = function () {
      submitBtn.disabled = !agree.checked;
      if (cfNote) cfNote.textContent = agree.checked ? '' : '送信には個人情報の取り扱いへの同意が必要です。';
    };
    agree.addEventListener('change', syncAgree);
    syncAgree();
  }

  // Forms marked data-mailto have no server behind them yet: submitting
  // opens the visitor's mail client with the fields filled in. Replace this
  // with a real form backend (e.g. a Cloudflare Pages Function) later.
  document.querySelectorAll('form[data-mailto]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var to = form.getAttribute('data-mailto');
      var lines = [];
      new FormData(form).forEach(function (value, key) {
        if (String(value).trim() === '') return;
        lines.push(key + '： ' + value);
      });
      var subject = encodeURIComponent('ウェブサイトからのお問い合わせ');
      var body = encodeURIComponent(lines.join('\n'));
      window.location.href = 'mailto:' + to + '?subject=' + subject + '&body=' + body;
      var note = form.querySelector('.js-form-note');
      if (note) note.textContent = 'メールソフトが開きます。内容をご確認のうえ送信してください。';
    });
  });
});
