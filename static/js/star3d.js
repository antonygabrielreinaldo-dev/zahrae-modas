// Estrela facetada + nome "ZAHRAE" extrudado em 3D (decorativos) — Three.js r128
(() => {
  const art = document.querySelector(".hero-art");
  const canvas = document.getElementById("star3d");
  if (!art || !canvas) return;

  // Se existir uma foto em static/img/hero.jpg, ela substitui a cena
  if (art.dataset.photo) {
    const probe = new Image();
    probe.onload = () => art.classList.add("has-photo");
    probe.src = art.dataset.photo;
  }
  if (!window.THREE) return;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  let renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true }); }
  catch (e) { return; }                       // sem WebGL: ficam estrela e nome planos com brilho
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 50);
  camera.position.set(0, 0, 9);

  /* ---- estrela de bússola com facetas ---- */
  function starGeometry(longR, shortR, innerR, height) {
    const ring = [];
    for (let k = 0; k < 8; k++) {
      const a = Math.PI / 2 - k * Math.PI / 4;
      const R = k % 2 === 0 ? longR : shortR;
      ring.push([Math.cos(a) * R, Math.sin(a) * R]);
      const b = a - Math.PI / 8;
      ring.push([Math.cos(b) * innerR, Math.sin(b) * innerR]);
    }
    const v = [];
    for (let i = 0; i < ring.length; i++) {
      const [x1, y1] = ring[i], [x2, y2] = ring[(i + 1) % ring.length];
      v.push(0, 0, height, x2, y2, 0, x1, y1, 0);
      v.push(0, 0, -height, x1, y1, 0, x2, y2, 0);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(v, 3));
    g.computeVertexNormals();
    return g;
  }
  const gold = (color) => new THREE.MeshPhongMaterial({ color, specular: 0xfff2c2, shininess: 120, flatShading: true, side: THREE.DoubleSide });

  const rig = new THREE.Group();               // gira com o ponteiro
  const starGroup = new THREE.Group();         // estrela: gira mais (profundidade em camadas)
  const wordGroup = new THREE.Group();         // nome: gira menos
  const big = new THREE.Mesh(starGeometry(1.9, 1.14, 0.38, 0.32), gold(0xc7932a));
  const small = new THREE.Mesh(starGeometry(0.74, 0.46, 0.16, 0.18), gold(0xefce73));
  small.rotation.z = Math.PI / 8; small.position.z = 0.24;
  starGroup.add(big, small);
  starGroup.scale.setScalar(0.6);
  starGroup.position.y = 0.68;
  wordGroup.position.y = -1.32;
  rig.add(starGroup, wordGroup);
  scene.add(rig);

  /* ---- nome em 3D: camadas empilhadas do logo (extrusão) ---- */
  const WORD_W = 3.7, WORD_H = WORD_W / 4;     // textura 2048x512
  new THREE.TextureLoader().load(canvas.dataset.word, (tex) => {
    tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
    const geo = new THREE.PlaneGeometry(WORD_W, WORD_H);
    const LAYERS = 9, STEP = 0.02;
    for (let i = LAYERS; i >= 1; i--) {         // lateral escura (espessura)
      const shade = new THREE.Color(0xb98a2e).lerp(new THREE.Color(0x5a3d10), i / LAYERS);
      const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: tex, color: shade, alphaTest: 0.4 }));
      m.position.z = -i * STEP;
      wordGroup.add(m);
    }
    const front = new THREE.Mesh(geo, new THREE.MeshPhongMaterial({
      map: tex, color: 0xe3b95f, specular: 0xffffff, shininess: 55, alphaTest: 0.4,
    }));
    wordGroup.add(front);
    render(performance.now());
  });

  scene.add(new THREE.AmbientLight(0xffe9c0, 0.6));
  const key = new THREE.DirectionalLight(0xffffff, 1.0);  key.position.set(-3, 4, 6);  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffb35c, 0.6); fill.position.set(4, -3, 3); scene.add(fill);
  const glint = new THREE.PointLight(0xfff4d0, 1.5, 16);  glint.position.set(0, 0, 4.5); scene.add(glint);

  let tx = 0, ty = 0, px = 0, py = 0, running = false, raf = 0;

  function render(now) {
    const t = reduce ? 0 : now / 1000;
    px += (tx - px) * 0.06; py += (ty - py) * 0.06;
    const swayY = reduce ? 0.3 : Math.sin(t * 0.6) * 0.3;
    const swayX = reduce ? -0.08 : Math.sin(t * 0.45) * 0.1;
    rig.rotation.y = swayY * 0.6 + px * 0.4;
    rig.rotation.x = swayX * 0.6 + py * 0.25;
    starGroup.rotation.y = swayY * 0.5 + px * 0.25;       // a estrela gira um pouco mais
    starGroup.position.y = 0.68 + (reduce ? 0 : Math.sin(t * 0.9) * 0.07);
    wordGroup.position.z = reduce ? 0 : Math.sin(t * 0.9 + 1) * 0.04;
    glint.position.set(px * 4, -py * 4, 4.5);              // brilho que segue o ponteiro
    renderer.render(scene, camera);
  }
  function loop(now) { render(now); if (running) raf = requestAnimationFrame(loop); }
  function start() { if (!running && !reduce) { running = true; raf = requestAnimationFrame(loop); } }
  function stop()  { running = false; cancelAnimationFrame(raf); }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    render(performance.now());
  }
  new ResizeObserver(resize).observe(canvas);

  window.addEventListener("pointermove", (e) => {
    tx = (e.clientX / innerWidth - 0.5) * 2;
    ty = (e.clientY / innerHeight - 0.5) * 2;
  }, { passive: true });

  new IntersectionObserver(([e]) => (e.isIntersecting ? start() : stop())).observe(art);
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));

  resize();
  art.classList.add("star-3d");
})();
