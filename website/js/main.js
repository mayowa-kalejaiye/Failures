/* ============================================================
   FAILURES MCP — Exact Better Auth UI Replicate JS
   ============================================================ */

const THEME_KEY = 'failures-theme';

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getStoredTheme() {
  return localStorage.getItem(THEME_KEY) || 'system';
}

function applyTheme(theme) {
  const resolved = theme === 'system' ? getSystemTheme() : theme;
  document.documentElement.classList.toggle('dark', resolved === 'dark');
  document.querySelectorAll('[data-theme-icon]').forEach(el => {
    if (el.dataset.themeIcon === resolved) {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  });
}

function toggleTheme() {
  const cur = getStoredTheme();
  const next = cur === 'dark' ? 'light' : cur === 'light' ? 'system' : 'dark';
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

// Apply immediately before DOM render
(function() {
  const t = localStorage.getItem(THEME_KEY) || 'system';
  const resolved = t === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : t;
  if (resolved === 'dark') document.documentElement.classList.add('dark');
})();

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function highlightPythonSource(source) {
  const slots = [];
  const withSlots = source
    .replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, match => `@@S${slots.push({ type: 'str', value: match }) - 1}@@`)
    .replace(/(#.*)$/gm, match => `@@S${slots.push({ type: 'comment', value: match }) - 1}@@`);

  let html = escapeHtml(withSlots);

  html = html.replace(
    /\b(async|await|def|class|return|raise|try|except|finally|if|elif|else|for|while|with|as|from|import|pass|break|continue|yield|lambda|in|is|not|and|or)\b/g,
    '<span class="py-control">$1</span>'
  );
  html = html.replace(/\b(True|False|None)\b/g, '<span class="py-builtin">$1</span>');
  html = html.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g, '<span class="py-fn">$1</span>');
  html = html.replace(/\b\d+(?:\.\d+)?\b/g, '<span class="py-num">$&</span>');
  // Restore in a loop: a comment slot can itself contain a string slot
  // (e.g. # ... as 'pending' ...), and a single pass leaves the inner
  // token visible as literal @@S0@@. Bounded at 5 — nesting is finite.
  for (let i = 0; i < 5 && /@@S\d+@@/.test(html); i++) {
    html = html.replace(/@@S(\d+)@@/g, (_, idx) => {
      const slot = slots[Number(idx)];
      if (!slot) return '';
      const cls = slot.type === 'comment' ? 'py-comment' : 'py-str';
      return `<span class="${cls}">${escapeHtml(slot.value)}</span>`;
    });
  }

  return html;
}

function applyLandingPythonHighlighting() {
  if (!document.body.classList.contains('ba-landing')) return;
  document.querySelectorAll('.ba-fw-pane pre code').forEach(codeEl => {
    const raw = codeEl.textContent || '';
    if (!raw.trim()) return;
    codeEl.classList.add('ba-python-code');
    codeEl.innerHTML = highlightPythonSource(raw);
  });
}

function applyDocsHighlighting() {
  if (document.body.classList.contains('ba-landing')) return;
  document.querySelectorAll('.ba-prose pre code, .ba-docs-content pre code').forEach(codeEl => {
    const raw = codeEl.textContent || '';
    if (!raw.trim()) return;
    const isJson = raw.trim().startsWith('{') && raw.includes('":');
    if (isJson) {
      codeEl.classList.add('ba-json-code');
      let html = escapeHtml(raw);
      html = html.replace(/"([^"]+)":/g, '<span class="py-str">"$1"</span>:');
      html = html.replace(/:\s*"([^"]*)"/g, ': <span class="py-str">"$1"</span>');
      codeEl.innerHTML = html;
      return;
    }
    const looksCode = /\b(def|class|async|await|import|from|return|raise|try|except|with|if|for|while|function|const|let|await)\b/.test(raw);
    if (!looksCode) return;
    codeEl.classList.add('ba-python-code');
    codeEl.innerHTML = highlightPythonSource(raw);
  });
}

window.switchLang = function(btn, lang) {
  const scope = btn.closest('main') || document;
  scope.querySelectorAll('.lang-tab').forEach(b => {
    const active = b.dataset.lang === lang;
    b.classList.toggle('active', active);
    if (active) {
      b.classList.add('bg-foreground','text-background','border-foreground/15');
      b.classList.remove('bg-background','text-foreground/60','border-foreground/10');
    } else {
      b.classList.remove('bg-foreground','text-background','border-foreground/15');
      b.classList.add('bg-background','text-foreground/60','border-foreground/10');
    }
  });
  document.querySelectorAll('.lang-block').forEach(el => {
    const isTarget = el.classList.contains('lang-' + lang);
    el.classList.toggle('hidden', !isTarget);
  });
};

function getHugeIconMarkup(name) {
  const icons = {
    book: '<svg viewBox="0 0 24 24" fill="none"><path d="M8 3.5H6.6c-2.168 0-3.252 0-3.926.674C2 4.847 2 5.93 2 8.1v5.3c0 2.168 0 3.253.674 3.926C3.347 18 4.43 18 6.6 18h2.35A3.11 3.11 0 0 1 12 20.5v-15c-.944-1.259-2-2-4-2m8 0h1.4c2.168 0 3.252 0 3.926.674C22 4.847 22 5.93 22 8.1v5.3c0 2.168 0 3.253-.674 3.926C20.653 18 19.568 18 17.4 18h-2.35A3.11 3.11 0 0 0 12 20.5v-15c.944-1.259 2-2 4-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    lock: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 16v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M5 15a7 7 0 1 1 14 0a7 7 0 0 1-14 0Z" stroke="currentColor" stroke-width="1.5"/><path d="M16.5 9.5v-3a4.5 4.5 0 1 0-9 0v3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
    package: '<svg viewBox="0 0 24 24" fill="none"><g stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M11 22c-.818 0-1.6-.33-3.163-.99C3.946 19.366 2 18.543 2 17.16V7m9 15V11.355M20 7v4.5M7.326 9.691L4.405 8.278C2.802 7.502 2 7.114 2 6.5s.802-1.002 2.405-1.778l2.92-1.413C9.13 2.436 10.03 2 11 2s1.871.436 3.674 1.309l2.921 1.413C19.198 5.498 20 5.886 20 6.5s-.802 1.002-2.405 1.778l-2.92 1.413C12.87 10.564 11.97 11 11 11s-1.871-.436-3.674-1.309M5 12l2 1m9-9L6 9" stroke-linejoin="round"/><path d="M20.132 20.159L22 22m-.793-4.404a3.6 3.6 0 0 1-3.603 3.597A3.6 3.6 0 0 1 14 17.596A3.6 3.6 0 0 1 17.604 14a3.6 3.6 0 0 1 3.603 3.596Z"/></g></svg>',
    chart: '<svg viewBox="0 0 24 24" fill="none"><g stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M21 21H10c-3.3 0-4.95 0-5.975-1.025S3 17.3 3 14V3"/><path d="M5 20c.44-3.156 2.676-11.236 5.428-11.236c1.902 0 2.395 3.871 4.258 3.871C17.893 12.635 17.428 4 21 4" stroke-linejoin="round"/></g></svg>',
    code: '<svg viewBox="0 0 24 24" fill="none"><g stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9.5 9.5l-1.533 1.322C7.322 11.377 7 11.655 7 12s.322.623.967 1.178L9.5 14.5m5-5l1.533 1.322c.645.555.967.833.967 1.178s-.322.623-.967 1.178L14.5 14.5"/></g></svg>'
  };
  return icons[name] || '';
}

function prependHugeIcon(element, iconName, wrapperClass) {
  if (!element || element.querySelector(`.${wrapperClass}`)) return;
  const iconMarkup = getHugeIconMarkup(iconName);
  if (!iconMarkup) return;
  const wrapper = document.createElement('span');
  wrapper.className = wrapperClass;
  wrapper.setAttribute('aria-hidden', 'true');
  wrapper.innerHTML = iconMarkup;
  element.prepend(wrapper);
}

function applyDocsHugeIcons() {
  if (!document.querySelector('.ba-docs-layout')) return;

  document.querySelectorAll('.ba-sidebar-label').forEach(label => {
    const text = (label.textContent || '').toLowerCase();
    if (text.includes('getting')) prependHugeIcon(label, 'book', 'ba-sidebar-label-icon');
    else if (text.includes('principles')) prependHugeIcon(label, 'lock', 'ba-sidebar-label-icon');
    else if (text.includes('reference')) prependHugeIcon(label, 'package', 'ba-sidebar-label-icon');
  });

  const tocTitle = document.querySelector('.ba-toc-title');
  if (tocTitle) prependHugeIcon(tocTitle, 'chart', 'ba-toc-title-icon');

  document.querySelectorAll('.ba-code-title').forEach(title => {
    prependHugeIcon(title, 'code', 'ba-code-title-icon');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  // 1. Theme initialization
  applyTheme(getStoredTheme());

  document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
    btn.addEventListener('click', toggleTheme);
  });

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (getStoredTheme() === 'system') applyTheme('system');
  });

  // 2. Command Box Multi-Tab (Scoped per box)
  document.querySelectorAll('.ba-cmd-box').forEach(box => {
    const tabs = box.querySelectorAll('.ba-cmd-tab');
    const snippets = box.querySelectorAll('.ba-cmd-snippet');
    const copyBtn = box.querySelector('.copy-btn');

    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        snippets.forEach(s => s.classList.remove('active'));

        tab.classList.add('active');
        const targetId = `tab-${tab.dataset.tab}`;
        const targetSnippet = document.getElementById(targetId);
        if (targetSnippet) {
          targetSnippet.classList.add('active');
          if (copyBtn) copyBtn.dataset.copy = targetId;
        }
      });
    });
  });

  // 3. Mobile Navigation & Sidebar Toggle
  const mobileToggleBtn = document.querySelector('[data-mobile-toggle]');
  const mobileDrawer = document.getElementById('mobile-nav-drawer');
  const mobileCloseBtn = document.querySelector('[data-mobile-close]');
  const sidebar = document.querySelector('.ba-docs-sidebar');

  if (mobileToggleBtn && mobileDrawer) {
    mobileToggleBtn.addEventListener('click', () => {
      mobileDrawer.classList.toggle('open');
      document.body.classList.toggle('overflow-hidden', mobileDrawer.classList.contains('open'));
    });
  }

  if (mobileCloseBtn && mobileDrawer) {
    mobileCloseBtn.addEventListener('click', () => {
      mobileDrawer.classList.remove('open');
      document.body.classList.remove('overflow-hidden');
    });
  }

  // Close drawer on link click
  mobileDrawer?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      mobileDrawer.classList.remove('open');
      document.body.classList.remove('overflow-hidden');
    });
  });

  document.querySelectorAll('[data-sidebar-toggle]').forEach(btn => {
    btn.addEventListener('click', () => {
      sidebar?.classList.toggle('open');
    });
  });

  // Framework Code Studio Tabs
  const fwTabs = document.querySelectorAll('.ba-fw-tab');
  fwTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      fwTabs.forEach(t => {
        t.classList.remove('active');
        t.classList.remove('text-foreground');
        t.classList.add('text-foreground/50');
      });
      document.querySelectorAll('.ba-fw-pane').forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      tab.classList.remove('text-foreground/50');
      tab.classList.add('text-foreground');
      const targetId = tab.dataset.fwTab;
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  applyLandingPythonHighlighting();
  applyDocsHighlighting();
  applyDocsHugeIcons();

  // Landing page: reveal the right-column product story as it enters view.
  if (document.body.classList.contains('ba-landing') && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const landingRight = document.querySelector('#hero .ba-sticky-left + div');
    const storyItems = landingRight ? Array.from(landingRight.querySelectorAll(
      ':scope > .ba-cmd-box, ' +
      ':scope > .ba-trusted-label, ' +
      ':scope > .ba-marquee-wrap, ' +
      ':scope > [id="framework"], ' +
      ':scope > [id="proof"], ' +
      ':scope > [id="infrastructure"], ' +
      ':scope > [id="benchmark"]'
    )) : [];

    const revealObserver = 'IntersectionObserver' in window
      ? new IntersectionObserver(entries => {
          entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
          });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 })
      : null;

    storyItems.forEach((item, index) => {
      item.classList.add('ba-reveal');
      item.style.transitionDelay = `${Math.min(index * 45, 180)}ms`;
      if (revealObserver) revealObserver.observe(item);
      else item.classList.add('is-visible');
    });
  }

  // FAQ Accordion
  document.querySelectorAll('.ba-faq-trigger').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const item = trigger.closest('.ba-faq-item');
      if (item) item.classList.toggle('open');
    });
  });

  // 4. Copy to Clipboard
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const targetId = btn.dataset.copy;
      let text = '';
      if (targetId) {
        const el = document.getElementById(targetId);
        text = el ? el.textContent : '';
      } else {
        const block = btn.closest('.ba-code-block') || btn.closest('pre');
        text = block ? block.querySelector('code')?.textContent || block.textContent : '';
      }

      if (!text) return;

      try {
        await navigator.clipboard.writeText(text.trim());
        const origHtml = btn.innerHTML;
        btn.innerHTML = `<span style="color:#22c55e;">✓ Copied</span>`;
        setTimeout(() => {
          btn.innerHTML = origHtml;
        }, 2000);
      } catch (err) {
        console.error('Copy failed', err);
      }
    });
  });

  // 5. Search Modal (Ctrl+K)
  const searchOverlay = document.getElementById('search-overlay');
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');

  function openSearch() {
    searchOverlay?.classList.add('open');
    setTimeout(() => searchInput?.focus(), 50);
  }

  function closeSearch() {
    searchOverlay?.classList.remove('open');
    if (searchInput) searchInput.value = '';
    renderSearchResults([]);
  }

  document.querySelectorAll('[data-search-open]').forEach(btn => {
    btn.addEventListener('click', openSearch);
  });

  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchOverlay?.classList.contains('open') ? closeSearch() : openSearch();
    }
    if (e.key === 'Escape' && searchOverlay?.classList.contains('open')) {
      closeSearch();
    }
  });

  searchOverlay?.addEventListener('click', e => {
    if (e.target === searchOverlay) closeSearch();
  });

  const SEARCH_ITEMS = [
    { title: 'Introduction', type: 'Docs', url: 'docs/index.html' },
    { title: 'Tools Reference', type: 'Tools', url: 'docs/tools.html' },
    { title: 'Patterns Catalog', type: 'Patterns', url: 'docs/patterns.html' },
    { title: 'Benchmark & Examples', type: 'Benchmark', url: 'docs/examples.html' },
    { title: 'Atomicity Principle', type: 'CRITICAL', url: 'docs/principles/atomicity.html' },
    { title: 'Idempotency Principle', type: 'CRITICAL', url: 'docs/principles/idempotency.html' },
    { title: 'Timeout & Ambiguous Outcome', type: 'CRITICAL', url: 'docs/principles/timeout.html' },
    { title: 'Concurrency & Locking', type: 'HIGH', url: 'docs/principles/concurrency.html' },
    { title: 'Retry Safety', type: 'HIGH', url: 'docs/principles/retry-safety.html' },
    { title: 'Availability & Circuit Breaker', type: 'HIGH', url: 'docs/principles/availability.html' },
    { title: 'Ordering & Streams', type: 'HIGH', url: 'docs/principles/ordering.html' },
    { title: 'Consistency & Cache', type: 'MEDIUM', url: 'docs/principles/consistency.html' },
    { title: 'Resource Exhaustion', type: 'HIGH', url: 'docs/principles/resource-exhaustion.html' },
    { title: 'Recovery & DLQ', type: 'MEDIUM', url: 'docs/principles/recovery.html' },
    { title: 'Observability & Traceability', type: 'MEDIUM', url: 'docs/principles/observability.html' }
  ];

  function renderSearchResults(items) {
    if (!searchResults) return;
    if (!items.length) {
      searchResults.innerHTML = searchInput?.value
        ? `<div style="padding: 24px; text-align: center; color: var(--fg-muted); font-size: 13px;">No matching results</div>`
        : '';
      return;
    }

    let relRoot = '';
    const path = window.location.pathname;
    if (path.includes('/principles/')) relRoot = '../../';
    else if (path.includes('/docs/')) relRoot = '../';

    searchResults.innerHTML = items.map(item => `
      <a href="${relRoot + item.url}" class="ba-search-item">
        <span style="font-family:var(--font-geist-mono); font-size:10px; font-weight:600; text-transform:uppercase; color:var(--fg-subtle);">${item.type}</span>
        <span style="font-size:13.5px; font-weight:500;">${item.title}</span>
      </a>
    `).join('');
  }

  searchInput?.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) {
      renderSearchResults([]);
      return;
    }
    const matches = SEARCH_ITEMS.filter(it => it.title.toLowerCase().includes(q) || it.type.toLowerCase().includes(q));
    renderSearchResults(matches.slice(0, 8));
  });

  // 6. Scrollspy Table of Contents
  const tocLinks = document.querySelectorAll('.ba-toc-link');
  if (tocLinks.length > 0) {
    const headings = Array.from(document.querySelectorAll('h2[id], h3[id]'));
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          tocLinks.forEach(l => l.classList.remove('active'));
          const activeLink = document.querySelector(`.ba-toc-link[href="#${entry.target.id}"]`);
          activeLink?.classList.add('active');
        }
      });
    }, { rootMargin: '-60px 0px -70% 0px', threshold: 0 });

    headings.forEach(h => observer.observe(h));
  }

  // 7. WebGL LineField Background on Hero
  const canvas = document.getElementById('hero-linefield');
  if (canvas) {
    const gl = canvas.getContext('webgl', { alpha: false, antialias: false, preserveDrawingBuffer: false });
    if (gl) {
      const vsSource = `
        attribute vec2 a_position;
        void main() {
          gl_Position = vec4(a_position, 0.0, 1.0);
        }
      `;
      const fsSource = `
        precision highp float;
        uniform float u_time;
        uniform vec2 u_resolution;
        uniform vec2 u_center;

        void main() {
          vec2 uv = gl_FragCoord.xy / u_resolution.xy;
          float aspect = u_resolution.x / u_resolution.y;
          vec2 p = vec2((uv.x - u_center.x) * aspect, uv.y - u_center.y);
          float dist = length(p);
          float t = u_time * 0.08;

          float stripeFreq = 120.0;
          float phase = uv.x * stripeFreq + t * 0.6;
          float stripe = abs(fract(phase) - 0.5) * 2.0;

          float stripeIdx = floor(phase + 0.5);
          float thickSeed = fract(sin(stripeIdx * 45.77) * 9823.11);
          float vThickness = 0.22 + step(0.78, thickSeed) * 0.08 + step(0.93, thickSeed) * 0.14;
          float stripeCore = 1.0 - smoothstep(0.06, vThickness, stripe);

          float dashSpacingPx = 32.0;
          float dashFract = fract(gl_FragCoord.y / dashSpacingPx);
          float dashMask = smoothstep(0.06, 0.18, dashFract);
          float lineCore = stripeCore * dashMask;

          float gapIdx = floor(phase);
          float beadCycle = 7.0;
          float beadCycleIndex = floor(u_time / beadCycle);
          float beadProgress = fract(u_time / beadCycle);
          float targetGap = floor(fract(sin(beadCycleIndex * 45.321 + 1.7) * 54321.98) * stripeFreq);
          float onTargetGap = 1.0 - step(0.5, abs(gapIdx - targetGap));
          float travel = beadProgress / 0.8;
          float beadVisible = step(beadProgress, 0.8);
          float beadY = 1.0 - travel;
          float travelFade = sin(clamp(travel, 0.0, 1.0) * 3.14159);
          float gapCore = smoothstep(0.55, 0.95, stripe);
          float bead = exp(-pow((uv.y - beadY) * 22.0, 2.0)) * beadVisible * travelFade;
          float signal = gapCore * bead * onTargetGap;

          float dy = uv.y - u_center.y;
          float sigma = dy > 0.0 ? 0.08 : 0.22;
          float verticalHalo = exp(-pow(dy / sigma, 2.0));
          float centerClear = smoothstep(0.14, 0.28, dist);
          float leftFade = smoothstep(0.25, 0.7, uv.x);
          float envelope = verticalHalo * centerClear * leftFade;

          float ripple = 0.0;
          for (int i = 0; i < 3; i++) {
            float rp = fract(t * 0.3 + float(i) * 0.333);
            float radius = rp * 1.2;
            float bell = (1.0 - rp) * rp * 4.0;
            ripple += exp(-pow((dist - radius) * 10.0, 2.0)) * bell;
          }

          float lines = lineCore * envelope * (0.32 + ripple * 1.1);
          lines += signal * envelope * 0.9;
          vec2 vc = uv - 0.5;
          float vignette = clamp(1.0 - dot(vc, vc) * 0.9, 0.0, 1.0);
          float brightness = lines * 0.75 * vignette * 0.9;
          brightness = clamp(brightness, 0.0, 1.0);

          gl_FragColor = vec4(vec3(brightness), 1.0);
        }
      `;

      function createShader(type, src) {
        const s = gl.createShader(type);
        gl.shaderSource(s, src);
        gl.compileShader(s);
        return s;
      }

      const vs = createShader(gl.VERTEX_SHADER, vsSource);
      const fs = createShader(gl.FRAGMENT_SHADER, fsSource);
      const prog = gl.createProgram();
      gl.attachShader(prog, vs);
      gl.attachShader(prog, fs);
      gl.linkProgram(prog);
      gl.useProgram(prog);

      const buf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]), gl.STATIC_DRAW);

      const posLoc = gl.getAttribLocation(prog, 'a_position');
      gl.enableVertexAttribArray(posLoc);
      gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

      const uTime = gl.getUniformLocation(prog, 'u_time');
      const uRes = gl.getUniformLocation(prog, 'u_resolution');
      const uCenter = gl.getUniformLocation(prog, 'u_center');

      const startTime = performance.now();
      function resize() {
        const dpr = 0.75 * Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = canvas.offsetWidth * dpr;
        canvas.height = canvas.offsetHeight * dpr;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
      resize();
      window.addEventListener('resize', resize);

      function renderFrame() {
        const elapsed = (performance.now() - startTime) / 1000;
        const cy = Math.min(0.5 + 0.15 * (canvas.offsetWidth || canvas.width) / (canvas.offsetHeight || canvas.height), 0.85);
        gl.uniform1f(uTime, elapsed);
        gl.uniform2f(uRes, canvas.width, canvas.height);
        gl.uniform2f(uCenter, 0.5, cy);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
        requestAnimationFrame(renderFrame);
      }
      requestAnimationFrame(renderFrame);
    }
  }
});
