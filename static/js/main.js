// ─── Автозакриття повідомлень ──────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const messages = document.querySelectorAll('.message');
  messages.forEach(function (msg) {
    setTimeout(function () {
      msg.style.opacity = '0';
      msg.style.transition = 'opacity 0.4s';
      setTimeout(function () { msg.remove(); }, 400);
    }, 4000);
  });
});
