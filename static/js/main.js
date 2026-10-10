// Zahrae — interações e movimento. Tudo respeita prefers-reduced-motion.
(() => {
  "use strict";
  const root = document.documentElement;
  root.classList.add("ready");
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canHover = matchMedia("(hover: hover)").matches;

  /* ---------- Toast ---------- */
  const region = $("#toasts");
  function toast(msg, type) {
    if (!region) return;
    const el = document.createElement("div");
    el.className = "toast" + (type === "erro" ? " erro" : "");
    const icon = type === "erro" ? "M6 6l12 12M18 6L6 18" : "M5 12.5l4.5 4.5L19 7.5";
    el.innerHTML = '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="' + icon + '"/></svg><span></span>';
    el.lastChild.textContent = msg;
    region.appendChild(el);
    setTimeout(() => { el.classList.add("is-leaving"); el.addEventListener("animationend", () => el.remove(), { once: true }); }, 2600);
  }

  /* ---------- Menu mobile ---------- */
  const toggle = $(".menu-toggle"), nav = $("#menu");
  function setMenu(open) {
    nav.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", open);
    toggle.setAttribute("aria-label", open ? "Fechar menu" : "Abrir menu");
  }
  if (toggle && nav) {
    toggle.addEventListener("click", () => setMenu(!nav.classList.contains("open")));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && nav.classList.contains("open")) { setMenu(false); toggle.focus(); } });
  }

  /* ---------- Cabeçalho e "voltar ao topo" ---------- */
  const header = $(".header"), toTop = $(".to-top");
  let ticking = false;
  function onScroll() {
    header && header.classList.toggle("is-scrolled", scrollY > 8);
    toTop && toTop.classList.toggle("is-visible", scrollY > 700);
    ticking = false;
  }
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();
  toTop && toTop.addEventListener("click", () => scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" }));

  /* ---------- Revelação ao rolar, com stagger por lote ---------- */
  const autoTag = ".section-head, .benefits li, .banner, .empty, .table-wrap, .perks li, .prose > *, .related";
  $$(autoTag).forEach((el) => {
    if (!el.classList.contains("reveal") && el.getBoundingClientRect().top > innerHeight * 0.92) el.classList.add("reveal");
  });
  const items = $$(".reveal");
  if ("IntersectionObserver" in window && !reduce) {
    const io = new IntersectionObserver((entries) => {
      entries.filter((e) => e.isIntersecting).forEach((e, i) => {
        const el = e.target;
        el.style.transitionDelay = Math.min(i, 5) * 70 + "ms";
        el.classList.add("in");
        io.unobserve(el);
        const clean = () => { el.classList.remove("reveal", "in"); el.style.transitionDelay = ""; };
        el.addEventListener("transitionend", (ev) => { if (ev.target === el) clean(); });
        setTimeout(clean, 1400);                 // garante a limpeza (devolve hover/transições próprias)
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    items.forEach((el) => io.observe(el));
  } else {
    items.forEach((el) => el.classList.remove("reveal"));
  }

  /* ---------- Imagens: esqueleto -> fade ---------- */
  $$(".card-media, .product-media").forEach((box) => {
    const img = $("img", box);
    if (!img) return;
    const done = () => box.classList.add("is-loaded");
    if (img.complete && img.naturalWidth) done();
    else { img.addEventListener("load", done, { once: true }); img.addEventListener("error", () => setTimeout(done, 50), { once: true }); }
  });
  setTimeout(() => $$(".card-media:not(.is-loaded), .product-media:not(.is-loaded)").forEach((b) => b.classList.add("is-loaded")), 5000);

  /* ---------- Ondulação no clique dos botões ---------- */
  document.addEventListener("pointerdown", (e) => {
    if (reduce) return;
    const b = e.target.closest(".btn");
    if (!b || b.matches("[disabled], [aria-disabled='true'], .is-loading")) return;
    const r = b.getBoundingClientRect(), size = Math.max(r.width, r.height) * 2;
    const s = document.createElement("span");
    s.className = "ripple";
    s.style.cssText = "width:" + size + "px;height:" + size + "px;left:" + (e.clientX - r.left - size / 2) + "px;top:" + (e.clientY - r.top - size / 2) + "px";
    b.appendChild(s);
    s.addEventListener("animationend", () => s.remove(), { once: true });
  });

  /* ---------- Barra de progresso ao navegar ---------- */
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || a.target === "_blank" || a.hasAttribute("download")) return;
    const u = new URL(a.href, location.href);
    if (u.origin !== location.origin || (u.pathname === location.pathname && u.search === location.search)) return;
    root.classList.add("is-navigating");
  });
  addEventListener("pageshow", () => {
    root.classList.remove("is-navigating");
    $$(".btn.is-loading").forEach((b) => { b.classList.remove("is-loading"); b.removeAttribute("aria-busy"); });
  });

  /* ---------- Avisos (fechar + sumir sozinho) ---------- */
  $$(".flash").forEach((f) => {
    const dismiss = () => { f.classList.add("is-leaving"); f.addEventListener("animationend", () => f.remove(), { once: true }); };
    const x = $(".flash-close", f);
    x && x.addEventListener("click", dismiss);
    if (f.classList.contains("sucesso")) setTimeout(dismiss, 5000);
  });

  /* ---------- Campos: preenchido, erro, validação ---------- */
  const fieldSel = ".field input, .field select, .field textarea";
  const fieldOf = (el) => el.closest(".field");
  function syncFilled(el) { const f = fieldOf(el); f && f.classList.toggle("is-filled", !!el.value && el.type !== "file"); }
  function clearError(el) {
    const f = fieldOf(el); if (!f) return;
    f.classList.remove("has-error"); el.removeAttribute("aria-invalid");
  }
  function showError(el, msg) {
    const f = fieldOf(el); if (!f) return;
    f.classList.add("has-error"); el.setAttribute("aria-invalid", "true");
    let m = $(".field-error", f);
    if (!m) {
      m = document.createElement("span");
      m.className = "field-error"; m.id = (el.id || el.name) + "-erro"; m.setAttribute("role", "alert");
      f.appendChild(m);
      el.setAttribute("aria-describedby", [el.getAttribute("aria-describedby"), m.id].filter(Boolean).join(" "));
    }
    m.textContent = msg;
  }
  function validate(el) {
    if (el.checkValidity()) { clearError(el); return true; }
    showError(el, el.validity.typeMismatch ? "Informe um e-mail válido." : el.validity.valueMissing ? "Preencha este campo." : el.validationMessage);
    return false;
  }
  $$(fieldSel).forEach(syncFilled);
  document.addEventListener("input", (e) => {
    if (!e.target.matches(fieldSel)) return;
    syncFilled(e.target);
    if (fieldOf(e.target)?.classList.contains("has-error")) validate(e.target);
  });
  document.addEventListener("change", (e) => { if (e.target.matches(fieldSel)) syncFilled(e.target); });
  document.addEventListener("focusout", (e) => { if (e.target.matches?.(".field [required]")) validate(e.target); });

  /* ---------- Mostrar/ocultar senha ---------- */
  $$(".reveal-pass").forEach((b) => {
    const input = $("input", b.parentElement);
    b.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      b.setAttribute("aria-pressed", show);
      b.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
      input.focus();
    });
  });

  /* ---------- Prévia da foto ---------- */
  const foto = $("#foto");
  foto && foto.addEventListener("change", () => {
    const file = foto.files[0], img = $("#foto-preview"), box = $("#foto-field");
    if (!file || !img) return;
    img.src = URL.createObjectURL(file);
    img.classList.remove("pop"); void img.offsetWidth; img.classList.add("pop");
    box && (box.hidden = false);
    const l = $("#foto-label"); l && (l.textContent = "Prévia da nova foto");
  });

  /* ---------- Limpar busca ---------- */
  const sInput = $("#q"), sClear = $(".search-clear");
  sClear && sInput && sClear.addEventListener("click", () => {
    sInput.value = ""; sInput.dispatchEvent(new Event("input", { bubbles: true })); sInput.focus();
  });

  /* ---------- Diálogo de confirmação ---------- */
  const dlg = $("#confirm");
  let pending = null;
  function closeDlg(val) {
    const finish = () => { dlg.classList.remove("closing"); dlg.close(val); };
    if (reduce) return finish();
    dlg.classList.add("closing");
    setTimeout(finish, 180);
  }
  function askConfirm(form) {
    pending = form;
    $("#confirm-text").textContent = form.dataset.confirm;
    $("#confirm-ok").textContent = form.dataset.confirmLabel || "Excluir";
    dlg.returnValue = "";
    dlg.showModal();
  }
  if (dlg) {
    dlg.addEventListener("click", (e) => { if (e.target === dlg) closeDlg("cancel"); });
    dlg.addEventListener("cancel", (e) => { e.preventDefault(); closeDlg("cancel"); });
    $$("[data-dlg]", dlg).forEach((b) => b.addEventListener("click", () => closeDlg(b.dataset.dlg)));
    dlg.addEventListener("close", () => {
      const f = pending; pending = null;
      if (dlg.returnValue === "ok" && f) { f._ok = true; f.requestSubmit(); }
    });
  }

  /* ---------- Envio de formulários: validação + loading ---------- */
  document.addEventListener("submit", (e) => {
    const f = e.target;
    if (f.matches("[data-confirm]") && !f._ok) { e.preventDefault(); askConfirm(f); return; }
    const bad = $$("[required]", f).filter((i) => !validate(i));
    if (bad.length) { e.preventDefault(); bad[0].focus(); return; }
    const btn = $("button[type='submit'].btn", f);
    if (btn) { btn.classList.add("is-loading"); btn.setAttribute("aria-busy", "true"); }
  });

  /* ---------- Copiar link da peça ---------- */
  $$("[data-copy]").forEach((b) => b.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      b.classList.add("is-done");
      toast("Link da peça copiado");
      setTimeout(() => b.classList.remove("is-done"), 1800);
    } catch (_) { toast("Não foi possível copiar o link", "erro"); }
  }));

  /* ---------- Zoom na foto do produto (só com mouse) ---------- */
  const pm = $(".product-media");
  if (pm && canHover && !reduce) {
    pm.addEventListener("pointerenter", () => pm.classList.add("is-zoom"));
    pm.addEventListener("pointerleave", () => pm.classList.remove("is-zoom"));
    pm.addEventListener("pointermove", (e) => {
      const r = pm.getBoundingClientRect();
      pm.style.setProperty("--zx", ((e.clientX - r.left) / r.width) * 100 + "%");
      pm.style.setProperty("--zy", ((e.clientY - r.top) / r.height) * 100 + "%");
    });
  }

  /* ---------- Brilho que segue o mouse no banner ---------- */
  const banner = $(".banner");
  if (banner && canHover && !reduce) {
    banner.addEventListener("pointermove", (e) => {
      const r = banner.getBoundingClientRect();
      banner.style.setProperty("--mx", e.clientX - r.left + "px");
      banner.style.setProperty("--my", e.clientY - r.top + "px");
    });
  }

  /* ---------- Botão Voltar ---------- */
  $$("[data-back]").forEach((a) => a.addEventListener("click", (e) => {
    try {
      if (document.referrer && new URL(document.referrer).origin === location.origin && history.length > 1) { e.preventDefault(); history.back(); }
    } catch (_) { /* segue para a home */ }
  }));
})();
