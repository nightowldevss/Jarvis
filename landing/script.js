/* ── TRANSLATIONS ── */
const i18n = {
  it: {
    nav_features: "Funzionalità", nav_commands: "Comandi", nav_download: "Download",
    badge: "v1.0.0 — Ora disponibile",
    hero_sub: "Il tuo assistente vocale intelligente per Windows.<br>Parla. Lui ascolta. Tutto il resto è automatico.",
    download_btn: "Scarica per Windows",
    hero_note: "Windows 10/11 · Python 3.9+ · Gratuito e open source",
    feat_title: "Cosa può fare",
    feat_sub: "Tutto quello che ti aspetti da un assistente moderno, e qualcosa in più.",
    f1_title: "Riconoscimento vocale", f1_desc: "Ascolta in tempo reale con Vosk offline o Google Speech. Nessun cloud obbligatorio.",
    f2_title: "AI con OpenAI", f2_desc: "Collega la tua chiave API per risposte intelligenti e conversazioni naturali.",
    f3_title: "Hotkey istantanea", f3_desc: "Ctrl+Shift+J per attivarlo ovunque, senza toccare il mouse.",
    f4_title: "Smart Home", f4_desc: "Integrazione con Philips Hue per controllare le luci di casa con la voce.",
    f5_title: "Email vocali", f5_desc: "Leggi e invia email Gmail senza aprire il browser, solo con la voce.",
    f6_title: "Privacy first", f6_desc: "Funziona anche offline. I tuoi dati restano sul tuo PC.",
    cmd_title: "Comandi vocali", cmd_sub: 'Dì solo "Jarvis" e poi uno di questi comandi.',
    c1: "Dice l'orario attuale", c2: "Apre Google Chrome", c3: "Cerca su YouTube",
    c4: "Traduce il testo", c5: "Legge le notizie", c6: "Avvia un timer",
    c7: "Calcola", c8: "Apre la cartella",
    dl_title: "Pronto a iniziare?", dl_sub: "Un solo file. Nessuna configurazione obbligatoria. Funziona subito.",
    dl_free: "Gratuito", dl_note: "Se Windows blocca il file: tasto destro → Proprietà → Sblocca",
    footer_made: 'Fatto con ❤️ da <a href="https://github.com/nightowldevss" target="_blank">nightowldevss</a>',
    footer_releases: "Releases", footer_issues: "Segnala un bug",
  },
  en: {
    nav_features: "Features", nav_commands: "Commands", nav_download: "Download",
    badge: "v1.0.0 — Now available",
    hero_sub: "Your intelligent voice assistant for Windows.<br>Speak. It listens. Everything else is automatic.",
    download_btn: "Download for Windows",
    hero_note: "Windows 10/11 · Python 3.9+ · Free and open source",
    feat_title: "What it can do",
    feat_sub: "Everything you expect from a modern assistant, and a little more.",
    f1_title: "Voice recognition", f1_desc: "Listens in real time with offline Vosk or Google Speech. No cloud required.",
    f2_title: "AI with OpenAI", f2_desc: "Connect your API key for smart responses and natural conversations.",
    f3_title: "Instant hotkey", f3_desc: "Ctrl+Shift+J to activate it anywhere, without touching the mouse.",
    f4_title: "Smart Home", f4_desc: "Philips Hue integration to control your home lights with your voice.",
    f5_title: "Voice emails", f5_desc: "Read and send Gmail emails without opening the browser, just with your voice.",
    f6_title: "Privacy first", f6_desc: "Works offline too. Your data stays on your PC.",
    cmd_title: "Voice commands", cmd_sub: 'Just say "Jarvis" followed by one of these commands.',
    c1: "Tells the current time", c2: "Opens Google Chrome", c3: "Searches on YouTube",
    c4: "Translates the text", c5: "Reads the news", c6: "Starts a timer",
    c7: "Calculates", c8: "Opens the folder",
    dl_title: "Ready to start?", dl_sub: "One file. No mandatory setup. Works right away.",
    dl_free: "Free", dl_note: "If Windows blocks the file: right-click → Properties → Unblock",
    footer_made: 'Made with ❤️ by <a href="https://github.com/nightowldevss" target="_blank">nightowldevss</a>',
    footer_releases: "Releases", footer_issues: "Report a bug",
  }
};

let currentLang = 'it';

function applyLang(lang) {
  currentLang = lang;
  const t = i18n[lang];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (t[key] !== undefined) el.innerHTML = t[key];
  });
  document.getElementById('langToggle').textContent = lang === 'it' ? '🌐 EN' : '🌐 IT';
  document.documentElement.lang = lang;
}

document.getElementById('langToggle').addEventListener('click', () => {
  applyLang(currentLang === 'it' ? 'en' : 'it');
});

/* ── NAVBAR SCROLL ── */
window.addEventListener('scroll', () => {
  document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 20);
});

/* ── SCROLL REVEAL ── */
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      const delay = entry.target.dataset.delay || 0;
      setTimeout(() => entry.target.classList.add('visible'), +delay);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll('.feat-card, .cmd-item').forEach(el => observer.observe(el));

/* ── THREE.JS 3D BACKGROUND ── */
(function () {
  const canvas = document.getElementById('bg-canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.z = 5;

  /* Particles */
  const count = 1800;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const c1 = new THREE.Color('#7c6af7');
  const c2 = new THREE.Color('#e879f9');

  for (let i = 0; i < count; i++) {
    positions[i * 3]     = (Math.random() - 0.5) * 20;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    const mix = Math.random();
    const col = c1.clone().lerp(c2, mix);
    colors[i * 3] = col.r; colors[i * 3 + 1] = col.g; colors[i * 3 + 2] = col.b;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const mat = new THREE.PointsMaterial({ size: 0.035, vertexColors: true, transparent: true, opacity: 0.7 });
  const points = new THREE.Points(geo, mat);
  scene.add(points);

  /* Floating wireframe torus */
  const torusGeo = new THREE.TorusGeometry(2.2, 0.008, 8, 120);
  const torusMat = new THREE.MeshBasicMaterial({ color: 0x7c6af7, transparent: true, opacity: 0.12, wireframe: true });
  const torus = new THREE.Mesh(torusGeo, torusMat);
  torus.rotation.x = Math.PI / 3;
  scene.add(torus);

  const torus2 = new THREE.Mesh(
    new THREE.TorusGeometry(3.2, 0.005, 6, 100),
    new THREE.MeshBasicMaterial({ color: 0xe879f9, transparent: true, opacity: 0.07, wireframe: true })
  );
  torus2.rotation.x = -Math.PI / 4;
  torus2.rotation.y = Math.PI / 6;
  scene.add(torus2);

  /* Mouse parallax */
  let mx = 0, my = 0;
  window.addEventListener('mousemove', e => {
    mx = (e.clientX / window.innerWidth - 0.5) * 0.4;
    my = (e.clientY / window.innerHeight - 0.5) * 0.4;
  });

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  let t = 0;
  function animate() {
    requestAnimationFrame(animate);
    t += 0.004;
    points.rotation.y = t * 0.06 + mx * 0.3;
    points.rotation.x = my * 0.2;
    torus.rotation.z = t * 0.15;
    torus2.rotation.z = -t * 0.08;
    torus2.rotation.x = -Math.PI / 4 + my * 0.1;
    camera.position.x += (mx * 0.5 - camera.position.x) * 0.05;
    camera.position.y += (-my * 0.5 - camera.position.y) * 0.05;
    renderer.render(scene, camera);
  }
  animate();
})();
