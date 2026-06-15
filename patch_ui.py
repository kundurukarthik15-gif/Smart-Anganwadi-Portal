import os

def patch_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR reading {filepath}: {e}")
        return

    for old_str, new_str in replacements:
        if old_str in content:
            content = content.replace(old_str, new_str)
        else:
            print(f"ERROR: Could not find string in {filepath}:\n{old_str[:60]}...")
            
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully patched {filepath}")
    except Exception as e:
        print(f"ERROR writing {filepath}: {e}")

# index.html patches
index_replacements = [
    (
        '    <button class="btn-nav-login" onclick="showLogin()"><i class="bi bi-box-arrow-in-right"></i> Login</button>\n  </nav>',
        '    <div style="display:flex; gap: 12px; align-items:center;">\n      <button class="btn-dark-toggle" onclick="toggleDarkMode()"><i class="bi bi-moon-fill" id="dm-icon"></i></button>\n      <button class="btn-nav-login" onclick="showLogin()"><i class="bi bi-box-arrow-in-right"></i> Login</button>\n    </div>\n  </nav>'
    ),
    (
        '      <div class="topbar-right">\n        <div class="tb-date"><i class="bi bi-calendar3"></i> <span id="today-date"></span></div>',
        '      <div class="topbar-right">\n        <button class="btn-dark-toggle" onclick="toggleDarkMode()"><i class="bi bi-moon-fill" id="dm-icon-app"></i></button>\n        <div class="tb-date"><i class="bi bi-calendar3"></i> <span id="today-date"></span></div>'
    )
]
patch_file('index.html', index_replacements)

# script.js patches
script_replacements = [
    (
        "  setTimeout(() => {\n    el.style.opacity    = '0';\n    el.style.transform  = 'translateX(50px)';\n    el.style.transition = 'all 0.3s';\n    setTimeout(() => el.remove(), 300);\n  }, 3200);\n}",
        "  setTimeout(() => {\n    el.style.opacity    = '0';\n    el.style.transform  = 'translateX(50px)';\n    el.style.transition = 'all 0.3s';\n    setTimeout(() => el.remove(), 300);\n  }, 3200);\n}\n\n// ================================================================\n//  DARK MODE\n// ================================================================\n\nif (localStorage.getItem('darkMode') === 'yes') {\n  document.body.classList.add('dark-mode');\n}\n\nfunction toggleDarkMode() {\n  document.body.classList.toggle('dark-mode');\n  const isDark = document.body.classList.contains('dark-mode');\n  localStorage.setItem('darkMode', isDark ? 'yes' : 'no');\n  updateDarkModeIcons(isDark);\n}\n\nfunction updateDarkModeIcons(isDark) {\n  const icon1 = document.getElementById('dm-icon');\n  const icon2 = document.getElementById('dm-icon-app');\n  const cls = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-fill';\n  if (icon1) icon1.className = cls;\n  if (icon2) icon2.className = cls;\n}\n\nwindow.addEventListener('DOMContentLoaded', () => {\n  const isDark = document.body.classList.contains('dark-mode');\n  updateDarkModeIcons(isDark);\n});"
    )
]
patch_file('script.js', script_replacements)

# styles.css patches
styles_replacements = [
    (
        ".brand-name { font-family: 'Baloo 2', cursive; font-size: 18px; font-weight: 800; color: var(--text-d); display: block; line-height: 1.2; }\n.brand-sub  { font-size: 11px; color: var(--text-s); font-weight: 500; display: block; }",
        ".brand-name { font-family: 'Baloo 2', cursive; font-size: 24px; font-weight: 800; color: var(--text-d); display: block; line-height: 1.2; }\n.brand-sub  { font-size: 13px; color: var(--text-s); font-weight: 600; display: block; }"
    ),
    (
        ".hero-h1 {\n  font-family: 'Baloo 2', cursive;\n  font-size: clamp(36px, 5.5vw, 62px);\n  font-weight: 800; line-height: 1.1;\n  color: var(--text-d); margin-bottom: 18px;\n}\n\n.grad-text {\n  background: linear-gradient(135deg, var(--primary), #EC4899);\n  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;\n}\n\n.hero-p {\n  font-size: 17px; color: var(--text-m); line-height: 1.8;\n  margin-bottom: 32px; max-width: 560px; margin-inline: auto;\n}",
        ".hero-h1 {\n  font-family: 'Baloo 2', cursive;\n  font-size: clamp(48px, 8vw, 84px);\n  font-weight: 800; line-height: 1.1;\n  color: var(--text-d); margin-bottom: 24px;\n}\n\n.grad-text {\n  background: linear-gradient(135deg, var(--primary), #EC4899);\n  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;\n}\n\n.hero-p {\n  font-size: 22px; color: var(--text-d); line-height: 1.6;\n  font-weight: 600;\n  margin-bottom: 36px; max-width: 640px; margin-inline: auto;\n}"
    ),
    (
        ".hm {\n  display: inline-flex; align-items: center; gap: 7px;\n  background: #fff; border: 1.5px solid var(--border);\n  border-radius: 99px; padding: 8px 18px;\n  font-size: 13px; font-weight: 700; color: var(--text-m); transition: all 0.2s;\n}",
        ".hm {\n  display: inline-flex; align-items: center; gap: 7px;\n  background: #fff; border: 1.5px solid var(--border);\n  border-radius: 99px; padding: 12px 24px;\n  font-size: 16px; font-weight: 700; color: var(--text-d); transition: all 0.2s;\n}"
    ),
    (
        ".btn-hero-cta {\n  padding: 15px 38px;\n  background: linear-gradient(135deg, var(--primary), var(--primary-d));\n  color: #fff; border: none; border-radius: 14px;\n  font-family: 'Plus Jakarta Sans', sans-serif;\n  font-size: 16px; font-weight: 800; cursor: pointer;\n  box-shadow: 0 8px 28px rgba(108,99,255,0.38); transition: all 0.22s;\n  display: inline-flex; align-items: center; gap: 9px; margin-bottom: 36px;\n}",
        ".btn-hero-cta {\n  padding: 18px 46px;\n  background: linear-gradient(135deg, var(--primary), var(--primary-d));\n  color: #fff; border: none; border-radius: 14px;\n  font-family: 'Plus Jakarta Sans', sans-serif;\n  font-size: 20px; font-weight: 800; cursor: pointer;\n  box-shadow: 0 8px 28px rgba(108,99,255,0.38); transition: all 0.22s;\n  display: inline-flex; align-items: center; gap: 9px; margin-bottom: 36px;\n}"
    ),
    (
        ".lc-input {\n  border: 2px solid var(--border) !important; border-radius: 12px !important;\n  font-family: 'Plus Jakarta Sans', sans-serif !important;\n  font-size: 15px !important; font-weight: 500 !important;\n  background: var(--bg) !important; height: 56px !important;\n  color: var(--text-d) !important; transition: all 0.2s !important;\n}\n.lc-input:focus { border-color: var(--primary) !important; background: #fff !important; box-shadow: 0 0 0 4px rgba(108,99,255,0.1) !important; }\n.form-floating label { color: var(--text-s) !important; font-size: 14px !important; font-weight: 600 !important; }",
        ".lc-input {\n  border: 2px solid var(--border) !important; border-radius: 12px !important;\n  font-family: 'Plus Jakarta Sans', sans-serif !important;\n  font-size: 18px !important; font-weight: 600 !important;\n  background: var(--bg) !important; height: 64px !important;\n  color: var(--text-d) !important; transition: all 0.2s !important;\n}\n.lc-input:focus { border-color: var(--primary) !important; background: #fff !important; box-shadow: 0 0 0 4px rgba(108,99,255,0.1) !important; }\n.form-floating label { color: var(--text-m) !important; font-size: 16px !important; font-weight: 700 !important; }"
    ),
    (
        ".sb-link {\n  display: flex; align-items: center; gap: 12px;\n  padding: 12px 14px; border-radius: 12px;\n  cursor: pointer; color: var(--text-m);\n  font-size: 15px; font-weight: 600;\n  transition: all 0.2s; text-decoration: none;\n  margin-bottom: 3px;\n}",
        ".sb-link {\n  display: flex; align-items: center; gap: 12px;\n  padding: 14px 16px; border-radius: 12px;\n  cursor: pointer; color: var(--text-m);\n  font-size: 17px; font-weight: 700;\n  transition: all 0.2s; text-decoration: none;\n  margin-bottom: 5px;\n}"
    ),
    (
        ".ptable { width: 100%; border-collapse: collapse; font-size: 14px; }\n.ptable thead { background: var(--bg); }\n.ptable th {\n  padding: 14px 18px; text-align: left;\n  font-size: 12px; font-weight: 800; color: var(--text-m);\n  text-transform: uppercase; letter-spacing: 0.6px;\n  border-bottom: 2px solid var(--border);\n}\n.ptable td {\n  padding: 14px 18px; border-bottom: 1px solid var(--border);\n  color: var(--text-d); font-size: 14px; vertical-align: middle;\n}",
        ".ptable { width: 100%; border-collapse: collapse; font-size: 16px; }\n.ptable thead { background: var(--bg); }\n.ptable th {\n  padding: 16px 20px; text-align: left;\n  font-size: 14px; font-weight: 800; color: var(--text-m);\n  text-transform: uppercase; letter-spacing: 0.6px;\n  border-bottom: 2px solid var(--border);\n}\n.ptable td {\n  padding: 16px 20px; border-bottom: 1px solid var(--border);\n  color: var(--text-d); font-size: 16px; vertical-align: middle;\n}"
    ),
    (
        "/* ================================================================\n   RESPONSIVE\n================================================================ */",
        "/* ================================================================\n   DARK MODE\n================================================================ */\nbody.dark-mode {\n  --bg:         #121212;\n  --bg2:        #1E1E1E;\n  --card:       #1E1E1E;\n  --border:     #333333;\n  --border2:    #444444;\n  --text-d:     #F9FAFB;\n  --text-m:     #D1D5DB;\n  --text-s:     #9CA3AF;\n  --text-xs:    #6B7280;\n}\nbody.dark-mode .land-nav,\nbody.dark-mode .topbar {\n  background: rgba(30, 30, 30, 0.95);\n}\nbody.dark-mode .hero-section {\n  background: linear-gradient(145deg, #181818 0%, #121212 50%, #1a1a1a 100%);\n}\nbody.dark-mode .land-footer {\n  background: #1e1e1e;\n}\nbody.dark-mode .pmodal-foot {\n  background: var(--bg);\n}\nbody.dark-mode .hm {\n  background: #1e1e1e;\n}\nbody.dark-mode .btn-nav-login,\nbody.dark-mode .btn-hero-cta {\n  color: #fff;\n}\nbody.dark-mode .login-card, body.dark-mode .sidebar {\n  background: var(--card);\n}\nbody.dark-mode .lc-input {\n  color: #fff !important;\n}\n\n.btn-dark-toggle {\n  background: var(--bg); border: 1.5px solid var(--border);\n  width: 42px; height: 42px; border-radius: 10px;\n  display: flex; align-items: center; justify-content: center;\n  font-size: 18px; cursor: pointer; color: var(--text-m);\n  transition: all 0.2s;\n}\n.btn-dark-toggle:hover { background: var(--primary-l); color: var(--primary); }\n\n/* ================================================================\n   RESPONSIVE\n================================================================ */"
    )
]
patch_file('styles.css', styles_replacements)

print("Patching process completed.")