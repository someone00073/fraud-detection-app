// ===== PARTICLE CANVAS =====
(function() {
  const canvas = document.getElementById('particleCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [], animId;
  const colors = ['rgba(139,92,246,', 'rgba(79,70,229,', 'rgba(167,139,250,', 'rgba(99,102,241,'];

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  for (let i = 0; i < 55; i++) {
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      size: Math.random() * 2.2 + 0.5,
      opacity: Math.random() * 0.45 + 0.1,
      color: colors[Math.floor(Math.random() * colors.length)],
      pulse: Math.random() * Math.PI * 2,
    });
  }

  let mx = W/2, my = H/2;
  window.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach((p, i) => {
      p.pulse += 0.018;
      const op = p.opacity * (0.7 + 0.3 * Math.sin(p.pulse));
      const dx = mx - p.x, dy = my - p.y;
      const d = Math.sqrt(dx*dx + dy*dy);
      if (d < 140) { p.vx += dx * 0.00004; p.vy += dy * 0.00004; }
      p.x += p.vx; p.y += p.vy;
      p.vx *= 0.99; p.vy *= 0.99;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI*2);
      ctx.fillStyle = p.color + op + ')';
      ctx.fill();
      for (let j = i+1; j < particles.length; j++) {
        const q = particles[j];
        const dx2 = p.x - q.x, dy2 = p.y - q.y;
        const d2 = Math.sqrt(dx2*dx2 + dy2*dy2);
        if (d2 < 110) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = 'rgba(139,92,246,' + (0.09 * (1 - d2/110)) + ')';
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    });
    animId = requestAnimationFrame(draw);
  }
  draw();
})();

// ===== MATRIX RAIN =====
(function() {
  const canvas = document.getElementById('matrixCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const fs = 13;
  const cols = Math.floor(canvas.width / fs);
  const drops = Array(cols).fill(1);
  const chars = '01₿$€£FRAUD DETECT SHIELD SECURE'.split('');

  setInterval(() => {
    ctx.fillStyle = 'rgba(10,8,30,0.045)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < drops.length; i++) {
      const ch = chars[Math.floor(Math.random() * chars.length)];
      const g = ctx.createLinearGradient(i*fs, drops[i]*fs - fs, i*fs, drops[i]*fs);
      g.addColorStop(0, 'rgba(139,92,246,0.75)');
      g.addColorStop(1, 'rgba(79,70,229,0.1)');
      ctx.fillStyle = g;
      ctx.font = fs + 'px monospace';
      ctx.fillText(ch, i*fs, drops[i]*fs);
      if (drops[i]*fs > canvas.height && Math.random() > 0.975) drops[i] = 0;
      drops[i]++;
    }
  }, 45);
})();

// ===== MUSIC CONTROL (AUTO PLAY FIX) =====
(function() {
  const audio = document.getElementById('bgMusic');
  const btn = document.getElementById('musicBtn');
  const ring1 = document.getElementById('mRing1');
  const ring2 = document.getElementById('mRing2');
  if (!audio || !btn) return;

  let playing = false;

  function setPlaying(state) {
    playing = state;
    btn.childNodes[0].textContent = state ? '🔊' : '🔇';
    if (ring1) ring1.style.display = state ? 'block' : 'none';
    if (ring2) ring2.style.display = state ? 'block' : 'none';
  }

  // 🔥 AUTO PLAY START (muted first)
  window.addEventListener('load', () => {
    audio.muted = true;

    audio.play().then(() => {
      setPlaying(true);

      // 🔥 Try to unmute after delay
      setTimeout(() => {
        audio.muted = false;

        audio.play().catch(() => {
          // If still blocked, keep muted but playing
          audio.muted = true;
        });

      }, 1500); // delay helps bypass restrictions

    }).catch(() => {
      setPlaying(false);
    });
  });

  // Manual toggle button (works always)
  btn.addEventListener('click', () => {
    if (!playing) {
      audio.muted = false;
      audio.play().then(() => setPlaying(true)).catch(() => {});
    } else {
      audio.muted = !audio.muted;
      setPlaying(!audio.muted);
    }
  });

})();

// ===== PASSWORD TOGGLE =====
function togglePass(id, btn) {
  const input = document.getElementById(id);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁️';
  }
}

// ===== HASH TOGGLE (ADMIN) =====
document.querySelectorAll('.password').forEach(el => {
  el.addEventListener('click', () => {
    const hash = el.getAttribute('data-hash');
    if (el.textContent.includes('•')) {
      el.textContent = hash.slice(0,22) + '... 👁️';
    } else {
      el.textContent = '•••••••••••••• 👁️';
    }
  });
});
