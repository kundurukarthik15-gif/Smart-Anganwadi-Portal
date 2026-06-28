// ================================================================
//  SMART ANGANWADI PORTAL — script.js  (Backend Connected)
// ================================================================

// ── LOCAL DATA STORE — starts empty, filled by the user ─────────
const DB = {
  user:         null,
  attendance:   [],
  stock:        [],
  stockHistory: [],
  children:     [],
  beneficiaries:[],
  stories:      [],
  meetings:     [],
  bmiRecords:   [],
  villageSurveys:[],
  villagers:     [],
  reportsHistory:[],
  attendancePhotos:[],
  nextId:       100,
};

// demo user store (in-memory for registration)
const DEMO_USERS = [
  { email: 'admin@anganwadi.gov.in',   password: 'admin@123',   name: 'Lakshmi Devi',   center: 'Rajiv Nagar Anganwadi Center', village: 'Rajiv Nagar', mandal: 'Secunderabad', district: 'Hyderabad', role: 'Admin'   },
  { email: 'teacher@anganwadi.gov.in', password: 'teach@123',   name: 'Savitri Bai',    center: 'Gandhi Nagar Anganwadi Center', village: 'Gandhi Nagar', mandal: 'Hanamkonda',  district: 'Warangal',  role: 'Teacher' },
  { email: 'staff@anganwadi.gov.in',   password: 'staff@123',   name: 'Radha Kumari',   center: 'Nehru Colony Anganwadi Center', village: 'Nehru Colony',  mandal: 'Choppadandi',  district: 'Karimnagar', role: 'Staff'   },
];

// global variables for charts & survey edit
let trendsChartInstance = null;
let ratioChartInstance = null;
let dashAgeChartInstance = null;
let dashAttendanceChartInstance = null;
let editSurveyId = null;
let editVillagerId = null;

// edit state
let editChildId  = null;
let editBenefId  = null;
let editBmiId    = null;
let audioInterval = null, audioPlaying = false, audioProgress = 0;

// ── UTILS ───────────────────────────────────────────────────────
function uid() { return ++DB.nextId; }

function fmt(date) {
  if (!date) return '—';
  const d = typeof date === 'string' ? date.slice(0, 10) : date;
  const [y, m, day] = d.split('-');
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${parseInt(day, 10)} ${months[parseInt(m, 10) - 1]} ${y}`;
}

function toast(msg, type = 'default') {
  const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', info: 'bi-info-circle-fill', default: 'bi-bell-fill' };
  const wrap = document.getElementById('toast-wrap');
  const el = document.createElement('div');
  el.className = `ptoast ${type}`;
  el.innerHTML = `<i class="bi ${icons[type] || icons.default}"></i> ${msg}`;
  wrap.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(50px)'; el.style.transition = 'all 0.3s'; setTimeout(() => el.remove(), 300); }, 3500);
}

// ================================================================
//  DARK MODE
// ================================================================

if (localStorage.getItem('darkMode') === 'yes') {
  document.body.classList.add('dark-mode');
}

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');
  localStorage.setItem('darkMode', isDark ? 'yes' : 'no');
  updateDarkModeIcons(isDark);
  
  if (window.Chart) {
    Chart.defaults.color = isDark ? '#9CA3AF' : '#64748B';
    Chart.defaults.borderColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.03)';
    if (document.getElementById('page-dashboard')?.classList.contains('active')) {
      renderDashboard();
    }
  }
}

function updateDarkModeIcons(isDark) {
  const icon1 = document.getElementById('dm-icon');
  const icon2 = document.getElementById('dm-icon-app');
  const cls = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  if (icon1) icon1.className = cls;
  if (icon2) icon2.className = cls;
}

window.addEventListener('DOMContentLoaded', () => {
  const isDark = document.body.classList.contains('dark-mode');
  updateDarkModeIcons(isDark);
  if (window.Chart) {
    Chart.defaults.color = isDark ? '#9CA3AF' : '#64748B';
    Chart.defaults.borderColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.03)';
  }
});

// ── API HELPER ──────────────────────────────────────────────────
const API_URL = window.location.protocol === 'file:' 
  ? 'http://localhost:5000/api' 
  : window.location.origin + '/api';

const SUPABASE_URL = 'https://frwtmqkwmtnoibrnytrt.supabase.co';

async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };
  
  try {
    const res = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
    const json = await res.json();
    
    // Auto logout on invalid/expired session (401 Unauthorized)
    if (res.status === 401 && token && endpoint !== '/auth/profile') {
      console.warn("Invalid session detected. Logging out.");
      localStorage.removeItem('token');
      DB.user = null;
      toast("Session expired — please log in again", "error");
      setTimeout(() => { window.location.reload(); }, 800);
    }
    
    return { status: res.status, ok: res.ok, ...json };
  } catch (err) {
    console.error('API Error:', err);
    return { ok: false, success: false, message: 'Network error or server down.' };
  }
}

// ── SUPABASE AUTH CALLBACK & REDIRECTS ───────────────────────────
function loginWithGoogle() {
  let redirectUrl = window.location.origin;
  // Only force redirect to Flask server if opening the file directly (file://)
  if (window.location.protocol === 'file:') {
    redirectUrl = 'http://localhost:5000';
  }
  window.location.href = `${SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(redirectUrl)}`;
}


function showAuthStatus(type, msg) {
  const el = document.getElementById('auth-status-msg');
  if (!el) return;
  el.className = `auth-status-banner ${type}`;
  el.textContent = msg;
  el.style.display = 'block';
  // Scroll to status banner
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function checkAuthHash() {
  const hash = window.location.hash;
  if (!hash) return;
  
  // Remove '#'
  const params = new URLSearchParams(hash.substring(1));
  const accessToken = params.get('access_token');
  const type = params.get('type');
  const errorDescription = params.get('error_description');
  
  if (errorDescription) {
    window.history.replaceState(null, null, window.location.pathname);
    showAuthStatus('error', `❌ Authentication error: ${decodeURIComponent(errorDescription.replace(/\+/g, ' '))}`);
    showLogin();
    return;
  }
  
  if (type === 'signup' || hash.includes('type=signup')) {
    // Email verified successfully
    window.history.replaceState(null, null, window.location.pathname);
    localStorage.removeItem('token');
    showAuthStatus('success', 'Email verified successfully. You can now login.');
    showLogin();
    return;
  }
  
  if (accessToken) {
    // Save token, let the window load handler handle profile retrieval
    localStorage.setItem('token', accessToken);
    window.history.replaceState(null, null, window.location.pathname);
  }
}

// Call hash check immediately on script execution
checkAuthHash();

// ── AUTO LOGIN & VERIFICATION ────────────────────────────────────
window.addEventListener('load', async () => {
  // Check hash again on load (in case of delay)
  checkAuthHash();
  
  const token = localStorage.getItem('token');
  if (token) {
    const res = await apiFetch('/auth/profile');
    if (res.success) {
      DB.user = { 
        id: res.data.id,
        email: res.data.email, 
        name: res.data.full_name, 
        center: res.data.center?.center_name || 'Anganwadi Center', 
        center_id: res.data.center_id,
        village: res.data.center?.village || '', 
        mandal: res.data.center?.mandal || '', 
        district: res.data.center?.district || '', 
        role: res.data.role || 'Staff' 
      };
      openPortal();
    } else {
      console.error("Profile fetch failed:", res);
      localStorage.removeItem('token');
      if (res.status === 403) {
        showLogin();
        showErr('login-err', 'Please verify your email address before accessing the portal.');
      } else {
        showLogin();
        showErr('login-err', `Authentication failed: ${res.message || 'Unknown error'}`);
      }
    }
  } else {
    // If not authenticated, ensure landing is visible
    backToLanding();
  }
});

// ── LANDING / AUTH ──────────────────────────────────────────────
function showLogin() {
  document.getElementById('landing-page').style.display = 'none';
  document.getElementById('login-page').style.display   = 'flex';
  // Ensure correct forms are visible
  document.getElementById('login-form').style.display = 'block';
  document.getElementById('register-form').style.display = 'none';
  document.getElementById('forgot-password-form').style.display = 'none';
  document.getElementById('registration-success-view').style.display = 'none';
}

function backToLanding() {
  document.getElementById('login-page').style.display   = 'none';
  document.getElementById('landing-page').style.display = 'block';
}

function togglePw() {
  const inp = document.getElementById('login-password');
  const eye = document.getElementById('pw-eye');
  if (inp.type === 'password') { inp.type = 'text'; eye.className = 'bi bi-eye-slash'; }
  else { inp.type = 'password'; eye.className = 'bi bi-eye'; }
}

async function doLogin() {
  const email = document.getElementById('login-email').value.trim().toLowerCase();
  const pass  = document.getElementById('login-password').value;
  const err   = document.getElementById('login-err');

  if (!email || !pass) { showErr('login-err', '⚠️ Please enter your email and password.'); return; }

  // Temporarily show loading text
  const btn = document.querySelector('#login-form .btn-login-submit') || document.querySelector('.btn-login');
  const originalText = btn ? btn.innerHTML : 'Signing in...';
  if (btn) {
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';
    btn.disabled = true;
  }

  const res = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password: pass })
  });

  if (btn) {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }

  if (res.success) {
    err.style.display = 'none';
    localStorage.setItem('token', res.data.token);
    
    // Map backend user to local DB user format for compatibility
    DB.user = { 
        id: res.data.user.id,
        email: res.data.user.email, 
        name: res.data.user.full_name, 
        center: res.data.center.center_name || 'Anganwadi Center', 
        center_id: res.data.user.center_id,
        village: res.data.center.village || '', 
        mandal: res.data.center.mandal || '', 
        district: res.data.center.district || '', 
        role: res.data.user.role || 'Staff' 
    };
    
    openPortal();
  } else {
    if (res.status === 403) {
      showErr('login-err', 'Please verify your email address before accessing the portal.');
    } else {
      showErr('login-err', `❌ ${res.message}`);
    }
  }
}

function showRegister() {
  document.getElementById('login-form').style.display    = 'none';
  document.getElementById('register-form').style.display = '';
  document.getElementById('forgot-password-form').style.display = 'none';
  document.getElementById('registration-success-view').style.display = 'none';
  document.getElementById('reg-err').style.display = 'none';
}

function backToLogin() {
  document.getElementById('register-form').style.display = 'none';
  document.getElementById('login-form').style.display    = '';
}

function showForgotPassword() {
  document.getElementById('login-form').style.display = 'none';
  document.getElementById('forgot-password-form').style.display = 'block';
  document.getElementById('forgot-err').style.display = 'none';
}

function backToLoginFromForgot() {
  document.getElementById('forgot-password-form').style.display = 'none';
  document.getElementById('login-form').style.display = 'block';
}

function backToLoginFromSuccess() {
  document.getElementById('registration-success-view').style.display = 'none';
  document.getElementById('login-form').style.display = 'block';
}

async function doForgotPassword() {
  const email = document.getElementById('forgot-email').value.trim();
  const err = document.getElementById('forgot-err');
  
  if (!email) {
    showErr('forgot-err', '⚠️ Please enter your email address.');
    return;
  }
  
  const btn = document.querySelector('#forgot-password-form .btn-login-submit');
  const origText = btn ? btn.innerHTML : 'Send Reset Link';
  if (btn) {
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
    btn.disabled = true;
  }
  
  const res = await apiFetch('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email })
  });
  
  if (btn) {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
  
  if (res.success) {
    toast('✅ Password reset email sent successfully.', 'success');
    backToLoginFromForgot();
  } else {
    showErr('forgot-err', `❌ ${res.message}`);
  }
}

async function doRegister() {
  const name  = document.getElementById('reg-fullname').value.trim();
  const email = document.getElementById('reg-email').value.trim().toLowerCase();
  const pass  = document.getElementById('reg-password').value;
  const pass2 = document.getElementById('reg-password-confirm').value;
  const centerName = document.getElementById('reg-center-name').value.trim();
  const district = document.getElementById('reg-district').value.trim();
  const mandal = document.getElementById('reg-mandal').value.trim();
  const village = document.getElementById('reg-village').value.trim();
  const address = document.getElementById('reg-address').value.trim();
  const mobile = document.getElementById('reg-mobile').value.trim();

  if (!name)  { showErr('reg-err', '⚠️ Enter your full name.'); return; }
  if (!email) { showErr('reg-err', '⚠️ Enter a valid email.'); return; }
  if (!pass)  { showErr('reg-err', '⚠️ Enter a password.'); return; }
  if (pass !== pass2) { showErr('reg-err', '⚠️ Passwords do not match.'); return; }
  if (pass.length < 6) { showErr('reg-err', '⚠️ Password must be at least 6 characters.'); return; }
  if (!centerName) { showErr('reg-err', '⚠️ Enter center name.'); return; }
  if (!district) { showErr('reg-err', '⚠️ Enter district.'); return; }
  if (!mandal) { showErr('reg-err', '⚠️ Enter mandal.'); return; }
  if (!village) { showErr('reg-err', '⚠️ Enter village.'); return; }

  // Temporarily show loading text
  const btn = document.querySelector('#register-form .btn-login-submit') || document.querySelector('#register-form .btn-login');
  const originalText = btn ? btn.innerHTML : 'Creating...';
  if (btn) {
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
    btn.disabled = true;
  }

  const res = await apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ 
      full_name: name,
      email: email,
      password: pass,
      mobile: mobile,
      center_name: centerName,
      district: district,
      mandal: mandal,
      village: village,
      address: address
    })
  });

  if (btn) {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }

  if (res.success) {
    // Display Registration Success verification page
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('registration-success-view').style.display = 'block';
  } else {
    showErr('reg-err', `❌ ${res.message}`);
  }
}

function showErr(id, msg) {
  const el = document.getElementById(id);
  el.textContent    = msg;
  el.style.display  = 'block';
}

async function loadInitialData() {
  // If not authenticated, skip fetching data
  if (!DB.user) return;

  const overlay = document.createElement('div');
  overlay.id = 'initial-loading-overlay';
  overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(255,255,255,0.8);z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column;font-size:24px;font-weight:bold;';
  if (document.body.classList.contains('dark-mode')) overlay.style.background = 'rgba(0,0,0,0.8)';
  overlay.innerHTML = '<div class="spinner-border text-primary" style="width: 2rem; height: 2rem;" role="status"></div>';
  document.body.appendChild(overlay);

  try {
    DB.children = [];
    DB.beneficiaries = [];
    DB.stock = [];
    DB.stockHistory = [];
    DB.stories = [];
    DB.meetings = [];
    DB.bmiRecords = [];
    DB.attendance = [];
    DB.attendancePhotos = [];
    DB.dailyMeals = [];
    DB.villageSurveys = [];
    DB.villagers = [];
    DB.reportsHistory = [];
    DB.vaccinations = [];
    DB.vaccinationNotifications = [];

    if (DB.user.role === 'Parent') {
      const vax = await apiFetch('/vaccinations');
      if (vax.success) DB.vaccinations = vax.data || [];
    } else {
      const [children, benef, stocks, history, stories, meetings, bmi, attPhotos, surveys, villagers, repHistory, attHistory, vax, vaxLogs] = await Promise.all([
        apiFetch('/children'),
        apiFetch('/beneficiaries'),
        apiFetch('/stocks'),
        apiFetch('/stocks/history'),
        apiFetch('/stories'),
        apiFetch('/meetings'),
        apiFetch('/bmi'),
        apiFetch('/attendance/photos'),
        apiFetch('/village-surveys'),
        apiFetch('/villagers'),
        apiFetch('/reports/history'),
        apiFetch('/attendance/history'),
        apiFetch('/vaccinations'),
        apiFetch('/vaccinations/notifications')
      ]);

      if (children.success) DB.children = children.data || [];
      if (benef.success) DB.beneficiaries = benef.data || [];
      if (stocks.success) DB.stock = stocks.data || [];
      if (history.success) DB.stockHistory = history.data || [];
      if (stories.success) DB.stories = stories.data || [];
      if (meetings.success) DB.meetings = meetings.data || [];
      if (bmi.success) DB.bmiRecords = (bmi.data || []).map(normalizeBmi);
      if (attPhotos.success) DB.attendancePhotos = attPhotos.data || [];
      if (surveys.success) DB.villageSurveys = surveys.data || [];
      if (villagers.success) DB.villagers = villagers.data || [];
      if (repHistory.success) DB.reportsHistory = repHistory.data || [];
      if (attHistory.success) DB.attendance = attHistory.data || [];
      if (vax.success) DB.vaccinations = vax.data || [];
      if (vaxLogs.success) DB.vaccinationNotifications = vaxLogs.data || [];
    }
  } catch (err) {
    console.error("Failed to load initial data", err);
    toast("Failed to sync some data from server", "error");
  } finally {
    overlay.remove();
  }
}

async function openPortal() {
  document.getElementById('landing-page').style.display = 'none';
  document.getElementById('login-page').style.display   = 'none';
  document.getElementById('portal-wrap').style.display  = 'block';

  await loadInitialData();

  const u  = DB.user;
  const av = (u.name || 'U').split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();

  if (document.getElementById('sbu-avatar')) {
    document.getElementById('sbu-avatar').innerHTML = `<i class="bi bi-person-fill"></i>`;
  }
  document.getElementById('sbu-name').textContent    = u.name || 'Anganwadi Worker';
  if (document.getElementById('sbu-center'))  document.getElementById('sbu-center').textContent  = u.center || '';
  if (document.getElementById('sbu-village')) document.getElementById('sbu-village').textContent = u.village || '';
  if (document.getElementById('sbu-role')) {
    document.getElementById('sbu-role').textContent    = u.role === 'Admin' ? 'Admin Worker' : u.role === 'Parent' ? 'Parent User' : 'Worker ID: AW12345';
  }
  if (document.getElementById('tb-avatar'))   document.getElementById('tb-avatar').textContent   = av;
  if (document.getElementById('tb-uname')) {
    document.getElementById('tb-uname').textContent    = u.role === 'Admin' ? 'Admin' : u.role === 'Parent' ? 'Parent' : 'Worker';
  }
  if (document.getElementById('tb-ucenter'))  document.getElementById('tb-ucenter').textContent  = u.center;

  // Show/Hide sidebar links dynamically based on user role
  const sidebarLinks = document.querySelectorAll('.sidebar nav.sb-nav a.sb-link');
  sidebarLinks.forEach(link => {
    const actionAttr = link.getAttribute('onclick');
    if (u.role === 'Parent') {
      if (actionAttr && (actionAttr.includes("'vaccinations'") || actionAttr.includes("doLogout"))) {
        link.style.display = 'flex';
      } else {
        link.style.display = 'none';
      }
    } else {
      link.style.display = 'flex';
    }
  });

  const now   = new Date();
  const today = now.toISOString().split('T')[0];
  document.getElementById('today-date').textContent = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

  // Set date fields
  ['s-date', 'd-date'].forEach(id => { const el = document.getElementById(id); if (el) el.value = today; });

  const hour  = now.getHours();
  const greet = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';
  document.getElementById('dash-welcome').textContent = `${greet}, ${u.name.split(' ')[0]}! 👋`;

  // Update dashboard hero info cards
  const staffNameEl = document.getElementById('dash-staff-name');
  const centerEl2   = document.getElementById('dash-center-name');
  const villageEl   = document.getElementById('dash-village');
  const mandalEl    = document.getElementById('dash-mandal');
  const districtEl  = document.getElementById('dash-district');
  const dateEl2     = document.getElementById('today-date2');
  if (staffNameEl) staffNameEl.textContent = u.name || '';
  if (centerEl2)   centerEl2.textContent   = u.center || '';
  if (villageEl)   villageEl.textContent   = u.village || '';
  if (mandalEl)    mandalEl.textContent    = u.mandal || '';
  if (districtEl)  districtEl.textContent  = u.district || '';
  if (dateEl2)     dateEl2.textContent     = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  if (u.role === 'Parent') {
    showPage('vaccinations');
  } else {
    showPage('dashboard');
  }
}

async function doLogout() {
  try {
    await apiFetch('/auth/logout', { method: 'POST' });
  } catch (e) {
    console.error("Logout failed on backend", e);
  }

  // ── Fully wipe all per-user data from the local store ──────────
  DB.user            = null;
  DB.attendance      = [];
  DB.stock           = [];
  DB.stockHistory    = [];
  DB.children        = [];
  DB.beneficiaries   = [];
  DB.stories         = [];
  DB.meetings        = [];
  DB.bmiRecords      = [];
  DB.villageSurveys  = [];
  DB.villagers       = [];
  DB.reportsHistory  = [];
  DB.attendancePhotos= [];
  DB.dailyMeals      = [];

  localStorage.removeItem('token');

  toast('👋 Logged out successfully', 'info');

  // Hard reload so there is zero chance of stale data being shown
  // to the next user who logs in on this browser tab.
  setTimeout(() => { window.location.reload(); }, 800);
}

// ── SIDEBAR ─────────────────────────────────────────────────────
function openSidebar()  { document.getElementById('sidebar').classList.add('open');    document.getElementById('sb-overlay').classList.add('open');    }
function closeSidebar() { document.getElementById('sidebar').classList.remove('open'); document.getElementById('sb-overlay').classList.remove('open'); }

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar.classList.contains('open')) {
    closeSidebar();
  } else {
    openSidebar();
  }
}

// ── PAGE NAVIGATION ──────────────────────────────────────────────
const PAGE_META = {
  dashboard:    { icon: '📊', title: 'Dashboard' },
  stock:        { icon: '📦', title: 'Stock Management' },
  distribution: { icon: '📤', title: 'Stock Distribution' },
  children:     { icon: '👶', title: 'Children Management' },
  attendance:   { icon: '📅', title: 'Student Attendance' },
  beneficiary:  { icon: '🤱', title: 'Beneficiary Management' },
  bmi:          { icon: '🤖', title: 'AI-Powered BMI & Nutrition' },
  survey:       { icon: '🏡', title: 'Village Survey' },
  stories:      { icon: '📚', title: 'Digital Story Library' },
  meetings:     { icon: '📅', title: 'Meeting Management' },
  reports:      { icon: '📊', title: 'Reports & Analytics' },
  settings:     { icon: '⚙️', title: 'Settings' },
  vaccinations: { icon: '🛡️', title: 'Vaccinations & Alerts' }
};

function showPage(page) {
  // If not authenticated, force redirect to login
  if (!DB.user) {
    showLogin();
    return;
  }

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.sb-link').forEach(l => l.classList.remove('active'));

  const el = document.getElementById('page-' + page);
  if (el) el.classList.add('active');

  document.querySelectorAll('.sb-link').forEach(l => {
    if (l.getAttribute('onclick')?.includes(`'${page}'`)) l.classList.add('active');
  });

  const meta = PAGE_META[page] || { icon: '📄', title: page };
  document.getElementById('tt-icon').textContent = meta.icon;
  document.getElementById('tt-text').textContent = meta.title;
  closeSidebar();

  const renders = {
    dashboard:    renderDashboard,
    stock:        () => switchStockTab('inventory'),
    distribution: () => { populateDistItems(); filterDistHistory('all'); },
    children:     renderChildren,
    attendance:   () => {
      initAttendancePage();
    },
    survey:       renderSurveyPage,
    beneficiary:  renderBenef,
    bmi:          renderBmiPage,
    stories:      () => renderStories(DB.stories),
    meetings:     () => renderMeetings('upcoming'),
    reports:      renderReports,
    settings:     renderSettingsPage,
    vaccinations: renderVaccinationsPage
  };
  renders[page]?.();
}

// ── SETTINGS & EDIT PROFILE ─────────────────────────────────────
function renderSettingsPage() {
  const u = DB.user || {};
  document.getElementById('set-fullname').value = u.name || '';
  document.getElementById('set-email').value = u.email || '';
  document.getElementById('set-mobile').value = u.mobile || '';
  document.getElementById('set-role').value = u.role || 'Staff';
  document.getElementById('set-center').value = u.center || '';
  document.getElementById('set-location').value = `${u.village || ''} / ${u.mandal || ''} (${u.district || ''})`;
  
  const banner = document.getElementById('settings-status-banner');
  if (banner) banner.style.display = 'none';
}

async function updateUserProfile() {
  const name = document.getElementById('set-fullname').value.trim();
  const email = document.getElementById('set-email').value.trim().toLowerCase();
  const mobile = document.getElementById('set-mobile').value.trim();

  if (!name) {
    showSettingsStatus('error', '⚠️ Full name is required.');
    return;
  }
  if (!email) {
    showSettingsStatus('error', '⚠️ Email address is required.');
    return;
  }

  const btn = document.querySelector('#page-settings .btn-submit');
  const origText = btn ? btn.innerHTML : 'Save Changes';
  if (btn) {
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    btn.disabled = true;
  }

  try {
    const res = await apiFetch('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify({ full_name: name, email: email, mobile: mobile })
    });

    if (res.success) {
      DB.user.name = res.data.full_name;
      DB.user.email = res.data.email;
      DB.user.mobile = res.data.mobile || '';

      // Refresh sidebar and topbar profile UI
      const av = (DB.user.name || 'U').split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
      document.getElementById('sbu-avatar').textContent  = av;
      document.getElementById('sbu-name').textContent    = DB.user.name;
      document.getElementById('tb-avatar').textContent   = av;
      document.getElementById('tb-uname').textContent    = DB.user.name.split(' ')[0];

      showSettingsStatus('success', '✅ Profile updated successfully!');
      toast('✅ Profile updated successfully!', 'success');
    } else {
      showSettingsStatus('error', `❌ ${res.message || 'Failed to update profile'}`);
    }
  } catch (err) {
    console.error("Failed to update profile:", err);
    showSettingsStatus('error', '❌ Network error or server offline.');
  } finally {
    if (btn) {
      btn.innerHTML = origText;
      btn.disabled = false;
    }
  }
}

function showSettingsStatus(type, msg) {
  const banner = document.getElementById('settings-status-banner');
  if (!banner) return;
  banner.className = `auth-status-banner ${type}`;
  banner.textContent = msg;
  banner.style.display = 'block';
}

// ── LOADING ──────────────────────────────────────────────────────
function showLoading(id, msg = 'Loading…') {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `<div style="padding:40px;text-align:center;color:var(--text-s)">
    <div style="font-size:32px;animation:spin 1s linear infinite;display:inline-block">⏳</div>
    <div style="margin-top:10px;font-weight:700">${msg}</div></div>`;
}

// ── DASHBOARD ────────────────────────────────────────────────────
function renderDashboard() {
  const u            = DB.user || {};
  const totalKids    = DB.children.length;
  const totalBenef   = DB.beneficiaries.length;
  const normalizedStocks = DB.stock.map(normalizeStock);
  const totalStock   = normalizedStocks.reduce((a, s) => a + (s.qty || 0), 0);
  const underweight  = DB.bmiRecords.filter(r => r.category === 'Underweight' || r.category === 'Severe Underweight').length;
  const criticalNutr = DB.bmiRecords.filter(r => r.category === 'Severe Underweight').length;

  // Find latest survey population
  const latestSurvey = DB.villageSurveys && DB.villageSurveys.length > 0 ? DB.villageSurveys[0] : null;
  const totalVillagers = latestSurvey ? (latestSurvey.total_population || 0) : 0;

  // ── Info bar (if elements exist)
  const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val || '—'; };
  setEl('dash-staff-name', u.name);
  setEl('dash-center-name', u.center);
  setEl('dash-village', u.village);
  setEl('dash-mandal', u.mandal);
  setEl('dash-district', u.district);
  
  const now = new Date();
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const fullMonths = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  
  const bannerDateText = `Today is ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}, ${days[now.getDay()]}`;
  setEl('dash-banner-date', bannerDateText);
  setEl('today-date2', now.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }));

  // ── Stat cards matching the reference image layout
  const lowItems = normalizedStocks.filter(s => s.qty <= s.minQty);
  
  // Calculate attendance details for today
  const todayStr = now.toISOString().split('T')[0];
  const todayLog = DB.attendance.find(a => a.date === todayStr);
  let presentCount = 0;
  let totalChildrenMarked = 0;
  let attPercent = 0;
  let attendanceVal = 0;

  if (todayLog && todayLog.records) {
    const recordsKeys = Object.keys(todayLog.records);
    totalChildrenMarked = recordsKeys.length;
    presentCount = Object.values(todayLog.records).filter(v => v === 'Present' || v === 'present').length;
    attPercent = totalChildrenMarked > 0 ? Math.round(presentCount / totalChildrenMarked * 100) : 0;
    attendanceVal = presentCount;
  }

  const statsData = [
    { title: 'Total Children', val: totalKids, lbl: 'Active Children', bg: 'bg-g', col: 'col-g', icon: 'bi-people-fill', link: 'children' },
    { title: "Today's Attendance", val: todayLog ? attendanceVal : '—', lbl: todayLog ? `${attPercent}% Present` : 'Not Marked', bg: 'bg-b', col: 'col-b', icon: 'bi-calendar2-check-fill', link: 'attendance' },
    { title: 'Stock Items', val: DB.stock.length, lbl: 'Items in Stock', bg: 'bg-o', col: 'col-o', icon: 'bi-box-seam-fill', link: 'stock' },
    { title: 'Pending Tasks', val: lowItems.length + underweight, lbl: 'Needs Attention', bg: 'bg-p', col: 'col-p', icon: 'bi-clipboard-check-fill', link: 'settings' }
  ];

  const statsEl = document.getElementById('dash-stats');
  if (statsEl) {
    statsEl.innerHTML = statsData.map(s => `
      <div class="col-xl-3 col-sm-6">
        <div class="scard" onclick="showPage('${s.link}')" style="cursor:pointer" title="Go to ${s.title}">
          <div class="scard-icon ${s.bg}">
            <i class="bi ${s.icon} ${s.col}" style="font-size:22px"></i>
          </div>
          <div class="scard-info">
            <div class="scard-lbl-top">${s.title}</div>
            <div class="scard-val">${s.val}</div>
            <div class="scard-lbl-bottom ${s.col}">${s.lbl}</div>
          </div>
        </div>
      </div>`).join('');
  }

  // ── Alerts Banner
  let alertHtml = '';
  if (lowItems.length) {
    alertHtml += `
      <div class="palert palert-err" style="margin: 0;">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <div>
          <strong>Low Stock Alert:</strong>
          ${lowItems.map(s => `<span class="tag tag-r" style="margin:0 3px">${s.item_name}</span>`).join('')}
          — Please reorder soon!
        </div>
      </div>`;
  }
  if (underweight > 0) {
    alertHtml += `
      <div class="bmi-alert-banner" style="margin: 14px 0 0 0;">
        <div class="bmi-alert-icon">⚠️</div>
        <div style="flex:1">
          <div class="bmi-alert-title">
            ${underweight} Children Require Nutrition Attention
          </div>
        </div>
        <button onclick="showPage('bmi')" class="btn-ph" style="flex-shrink:0;font-size:13px;padding:8px 16px">
          <i class="bi bi-arrow-right"></i> View
        </button>
      </div>`;
  }
  if (!alertHtml) {
    alertHtml = `
      <div class="palert palert-ok" style="margin: 0;">
        <i class="bi bi-check-circle-fill"></i>
        All systems normal. No urgent alerts today.
      </div>`;
  }
  const notifsEl = document.getElementById('dash-notifs');
  if (notifsEl) notifsEl.innerHTML = alertHtml;

  // ── Donut Chart: Age-wise Children Distribution
  const ageCanvas = document.getElementById('dashAgeChart');
  if (ageCanvas) {
    if (dashAgeChartInstance) {
      dashAgeChartInstance.destroy();
    }
    
    // Calculate age groups from DB
    let ageGroups = {
      '0-1': 0,
      '1-2': 0,
      '2-3': 0,
      '3-4': 0,
      '4-6': 0
    };
    
    DB.children.forEach(c => {
      const age = parseFloat(c.age);
      if (age <= 1) ageGroups['0-1']++;
      else if (age <= 2) ageGroups['1-2']++;
      else if (age <= 3) ageGroups['2-3']++;
      else if (age <= 4) ageGroups['3-4']++;
      else ageGroups['4-6']++;
    });
    
    const hasKids = DB.children.length > 0;
    const dataVals = hasKids 
      ? [ageGroups['0-1'], ageGroups['1-2'], ageGroups['2-3'], ageGroups['3-4'], ageGroups['4-6']]
      : [1]; // fallback grey arc
    const chartLabels = hasKids
      ? ['0 - 1 Years', '1 - 2 Years', '2 - 3 Years', '3 - 4 Years', '4 - 6 Years']
      : ['No Registered Children'];
    const chartColors = hasKids
      ? ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899']
      : ['#E5E7EB'];
    const totalKidsCount = DB.children.length;
    
    setEl('dash-chart-total-kids', totalKidsCount);
    
    const ctx = ageCanvas.getContext('2d');
    dashAgeChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: chartLabels,
        datasets: [{
          data: dataVals,
          backgroundColor: chartColors,
          borderWidth: 0
        }]
      },
      options: {
        cutout: '70%',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        }
      }
    });
    
    const legendEl = document.getElementById('dash-age-legend');
    if (legendEl) {
      if (!hasKids) {
        legendEl.innerHTML = `
          <div style="text-align:center; padding: 20px 0; color:var(--text-s); font-size:13px; font-weight:600;">
            No children registered yet.
          </div>`;
      } else {
        const labels = ['0 - 1 Years', '1 - 2 Years', '2 - 3 Years', '3 - 4 Years', '4 - 6 Years'];
        const colors = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899'];
        legendEl.innerHTML = labels.map((lbl, idx) => `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; font-size:12px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="width:10px; height:10px; border-radius:50%; background:${colors[idx]}; display:inline-block;"></span>
              <span style="color:var(--text-s); font-weight:600;">${lbl}</span>
            </div>
            <span style="color:var(--text-d); font-weight:700;">${dataVals[idx]} Children</span>
          </div>
        `).join('');
      }
    }
  }

  // ── Line Chart: Attendance Trend (Last 7 Days)
  const attendanceCanvas = document.getElementById('dashAttendanceChart');
  if (attendanceCanvas) {
    if (dashAttendanceChartInstance) {
      dashAttendanceChartInstance.destroy();
    }
    
    const labels = [];
    const dataVals = [];
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dStr = d.toISOString().split('T')[0];
      
      const dayNum = d.getDate();
      const lbl = `${dayNum} ${monthNames[d.getMonth()]}`;
      labels.push(lbl);
      
      const log = DB.attendance.find(a => a.date === dStr);
      if (log && log.records && Object.keys(log.records).length > 0) {
        const total = Object.keys(log.records).length;
        const present = Object.values(log.records).filter(status => status === 'Present' || status === 'present').length;
        const pct = Math.round((present / total) * 100);
        dataVals.push(pct);
      } else {
        dataVals.push(0);
      }
    }
    
    const ctx = attendanceCanvas.getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 180);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.15)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
    
    dashAttendanceChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Attendance %',
          data: dataVals,
          borderColor: '#10B981',
          borderWidth: 2,
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#10B981',
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            min: 0,
            max: 100,
            ticks: {
              stepSize: 25,
              callback: function(value) { return value + '%'; },
              font: { size: 10, weight: '600' }
            },
            grid: { color: 'rgba(0,0,0,0.03)' }
          },
          x: {
            grid: { display: false },
            ticks: { font: { size: 10, weight: '600' } }
          }
        }
      }
    });
  }

  // ── Recent children
  const recent = DB.children.slice(0, 5);
  const hasKids = recent.length > 0;
  
  const childrenEl = document.getElementById('dash-children');
  if (childrenEl) {
    if (!hasKids) {
      childrenEl.innerHTML = `
        <div style="padding: 40px; text-align: center; color: var(--text-s);">
          <div style="font-size: 32px; margin-bottom: 10px;">👶</div>
          <div style="font-weight: 700;">No children registered yet</div>
          <div style="font-size: 13px; margin-top: 4px;">Go to the <strong>Children Management</strong> section to register children.</div>
        </div>`;
    } else {
      childrenEl.innerHTML = `
        <div class="table-responsive">
          <table class="ptable">
            <thead>
              <tr>
                <th>#</th>
                <th>Child Name</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Mother Name</th>
                <th>Anganwadi Center</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${recent.map((c, i) => `
                <tr>
                  <td>${i + 1}</td>
                  <td><strong>${c.child_name}</strong></td>
                  <td>${c.age} Years</td>
                  <td><span class="tag ${c.gender === 'Male' ? 'tag-s' : 'tag-pk'}">${c.gender}</span></td>
                  <td class="col-soft">${c.parent_name || '—'}</td>
                  <td class="col-soft">${c.center_name || u.center || '—'}</td>
                  <td><span class="tag tag-g">Active</span></td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>`;
    }
  }
}

// ── STOCK ────────────────────────────────────────────────────────

// Normalize backend stock object → unified field names used across the UI
function normalizeStock(s) {
  return {
    id:             s.id,
    item_name:      s.item_name || s.name || '—',
    category:       s.category  || 'Other',
    qty:            parseFloat(s.remaining_quantity ?? s.qty ?? 0),
    received:       parseFloat(s.quantity_received  ?? (s.qty || 0)),
    distributed:    parseFloat(s.quantity_distributed ?? 0),
    unit:           s.unit      || 'units',
    minQty:         parseFloat(s.min_quantity ?? s.minQty ?? 20),
    low_stock:      !!s.low_stock,
    receivedDate:   s.received_date || s.received || '—',
    supplier:       s.supplier  || '—',
  };
}

// Normalize backend distribution/log record → unified fields for history table
function normalizeHistory(h) {
  return {
    date:   h.distribution_date || h.created_at?.slice(0,10) || h.date || '—',
    item:   h.item_name  || h.item  || '—',
    action: h.action     || 'Distributed',
    qty:    parseFloat(h.quantity ?? h.qty ?? 0),
    detail: h.distributed_to
      ? `To: ${h.distributed_to}${h.distributed_by ? ' | By: ' + h.distributed_by : ''}`
      : (h.detail || '—'),
  };
}

// Normalize backend BMI record → unified fields used across the UI
function normalizeBmi(r) {
  if (!r) return null;
  return {
    id:                 r.id,
    child_id:           r.child_id,
    child_name:         r.child_name || '—',
    age:                r.age_at_measurement ?? r.age ?? 0,
    gender:             r.gender || '—',
    height:             r.height_cm ?? r.height ?? 0,
    weight:             r.weight_kg ?? r.weight ?? 0,
    bmi:                r.bmi_value ?? r.bmi ?? 0,
    category:           r.bmi_category ?? r.category ?? 'Normal',
    nutrition_status:   r.nutrition_status,
    ai_recommendation:  r.ai_recommendation,
    date:               r.measurement_date || r.date || '—',
    notes:              r.notes || '',
  };
}

function switchStockTab(tab) {
  ['inventory', 'add', 'history'].forEach(t => {
    const el = document.getElementById('stock-' + t);
    if (el) el.style.display = t === tab ? '' : 'none';
  });
  document.querySelectorAll('#page-stock .ptab').forEach((b, i) =>
    b.classList.toggle('active', ['inventory', 'add', 'history'][i] === tab));

  if (tab === 'inventory') renderStockInventory();
  if (tab === 'history')   renderStockHistory();
}

function renderStockInventory(data) {
  const raw  = data || DB.stock;
  const rows = raw.map(normalizeStock);

  const low  = rows.filter(s => s.qty <= s.minQty || s.low_stock).length;
  const well = rows.filter(s => s.qty > s.minQty * 2).length;
  const run  = rows.filter(s => s.qty > s.minQty && s.qty <= s.minQty * 2).length;

  const statsEl = document.getElementById('stock-stats');
  if (statsEl) statsEl.innerHTML = `
    <div class="scard"><div class="scard-icon bg-o"><i class="bi bi-box-seam-fill col-o" style="font-size:22px"></i></div><div><div class="scard-val col-o">${rows.length}</div><div class="scard-lbl">Total Items</div></div></div>
    <div class="scard"><div class="scard-icon bg-g"><i class="bi bi-check-circle-fill col-g" style="font-size:22px"></i></div><div><div class="scard-val col-g">${well}</div><div class="scard-lbl">Well Stocked</div></div></div>
    <div class="scard"><div class="scard-icon bg-y"><i class="bi bi-lightning-charge-fill col-y" style="font-size:22px"></i></div><div><div class="scard-val col-y">${run}</div><div class="scard-lbl">Running Low</div></div></div>
    <div class="scard"><div class="scard-icon bg-r"><i class="bi bi-exclamation-triangle-fill col-r" style="font-size:22px"></i></div><div><div class="scard-val col-r">${low}</div><div class="scard-lbl">Critical Low</div></div></div>
  `;

  const tbodyEl = document.getElementById('stock-tbody');
  if (!tbodyEl) return;

  if (!rows.length) {
    tbodyEl.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:36px;color:var(--text-s)">
      <div style="font-size:40px">📦</div>
      <div style="margin-top:10px;font-weight:700">No stock items yet.</div>
      <div style="font-size:13px;margin-top:4px">Click <strong>Add Stock</strong> to add your first item.</div>
    </td></tr>`;
    return;
  }

  tbodyEl.innerHTML = rows.map((s, i) => {
    const base  = s.minQty * 5 || 1;
    const pct   = Math.min(100, Math.round((s.qty / base) * 100));
    const isCrit = s.qty <= s.minQty || s.low_stock;
    const isLow  = !isCrit && pct < 40;
    const color  = isCrit ? '#EF4444' : isLow ? '#F59E0B' : '#10B981';
    const tag    = isCrit
      ? '<span class="tag tag-r"><i class="bi bi-exclamation-circle"></i> Critical</span>'
      : isLow
        ? '<span class="tag tag-y"><i class="bi bi-dash-circle"></i> Low</span>'
        : '<span class="tag tag-g"><i class="bi bi-check-circle"></i> Good</span>';

    return `<tr>
      <td>${i + 1}</td>
      <td><strong>${s.item_name}</strong></td>
      <td><span class="tag tag-s">${s.category}</span></td>
      <td>${s.received}</td>
      <td>${s.distributed}</td>
      <td>
        <strong style="font-size:15px;color:${color}">${s.qty}</strong>
        <span style="font-size:11px;color:var(--text-s)"> ${s.unit}</span>
        <div class="pbar mt-2" style="max-width:100px">
          <div class="pbar-fill" style="width:${pct}%;background:${color}"></div>
        </div>
      </td>
      <td>${s.unit}</td>
      <td>${tag}</td>
      <td class="col-soft fs-13">${fmt(s.receivedDate)}</td>
    </tr>`;
  }).join('');
}

function searchStock(q) {
  const filtered = DB.stock.filter(s =>
    (s.item_name || '').toLowerCase().includes(q.toLowerCase())
  );
  renderStockInventory(filtered);
}

async function addStock() {
  const name     = document.getElementById('s-item')?.value?.trim();
  const qty      = parseFloat(document.getElementById('s-qty')?.value);
  const supplier = document.getElementById('s-supplier')?.value?.trim() || 'Unknown';
  const date     = document.getElementById('s-date')?.value || new Date().toISOString().split('T')[0];
  const notes    = document.getElementById('s-notes')?.value?.trim() || '';

  if (!name)           { toast('Please select an item', 'error'); return; }
  if (!qty || qty < 1) { toast('Enter a valid quantity (≥ 1)', 'error'); return; }

  const btn = document.querySelector('#stock-add .btn-submit');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Adding…'; }

  const res = await apiFetch('/stocks/add', {
    method: 'POST',
    body: JSON.stringify({ item_name: name, quantity_received: qty, supplier, received_date: date, notes }),
  });

  if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-plus-circle-fill"></i> Add to Inventory'; }

  if (res.success) {
    // Clear form
    ['s-item','s-qty','s-supplier','s-notes'].forEach(id => {
      const el = document.getElementById(id); if (el) el.value = '';
    });
    const dateEl = document.getElementById('s-date');
    if (dateEl) dateEl.value = new Date().toISOString().split('T')[0];

    toast(`✅ Added ${qty} ${name} to inventory!`, 'success');

    // Refresh from backend
    const [stocksRes, histRes] = await Promise.all([apiFetch('/stocks'), apiFetch('/stocks/history')]);
    if (stocksRes.success) DB.stock        = stocksRes.data || [];
    if (histRes.success)   DB.stockHistory = histRes.data  || [];

    switchStockTab('inventory');
  } else {
    toast(res.message || 'Failed to add stock', 'error');
  }
}

function populateDistItems() {
  const el = document.getElementById('d-item');
  if (!el) return;
  if (!DB.stock.length) {
    el.innerHTML = '<option value="">No stock items available — add stock first</option>';
    return;
  }
  el.innerHTML = DB.stock.map(s => {
    const n = normalizeStock(s);
    return `<option value="${n.id}">${n.item_name} (${n.qty} ${n.unit} available)</option>`;
  }).join('');
}

async function distributeStock() {
  const stockId = document.getElementById('d-item')?.value;
  const qty     = parseFloat(document.getElementById('d-qty')?.value);
  const to      = document.getElementById('d-to')?.value?.trim();
  const date    = document.getElementById('d-date')?.value || new Date().toISOString().split('T')[0];
  const by      = document.getElementById('d-by')?.value?.trim() || (DB.user?.full_name || DB.user?.name || 'Staff');

  if (!stockId)        { toast('Select an item', 'error'); return; }
  if (!qty || qty < 1) { toast('Enter a valid quantity', 'error'); return; }
  if (!to)             { toast('Enter who this is distributed to', 'error'); return; }

  // Client-side check: don't allow distributing more than available
  const item = DB.stock.find(s => s.id === stockId || String(s.id) === String(stockId));
  if (item) {
    const n = normalizeStock(item);
    if (qty > n.qty) { toast(`Only ${n.qty} ${n.unit} available!`, 'error'); return; }
  }

  const btn = document.querySelector('#page-distribution .btn-submit, #stock-distribute .btn-submit');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Recording…'; }

  const res = await apiFetch('/stocks/distribute', {
    method: 'POST',
    body: JSON.stringify({ stock_id: stockId, quantity: qty, distributed_to: to, distribution_date: date, distributed_by: by }),
  });

  if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-arrow-right-circle-fill"></i> Record Distribution'; }

  if (res.success) {
    ['d-qty','d-to','d-by'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    toast(`✅ Distributed ${qty} to ${to}`, 'success');

    // Refresh
    const [stocksRes, histRes] = await Promise.all([apiFetch('/stocks'), apiFetch('/stocks/history')]);
    if (stocksRes.success) DB.stock        = stocksRes.data || [];
    if (histRes.success)   DB.stockHistory = histRes.data  || [];

    populateDistItems();
    filterDistHistory('all');
  } else {
    toast(res.message || 'Failed to distribute stock', 'error');
  }
}

function renderStockHistory() {
  const tbodyEl = document.getElementById('stock-hist-tbody');
  if (!tbodyEl) return;

  if (!DB.stockHistory.length) {
    tbodyEl.innerHTML = `<tr><td colspan="5" class="text-center" style="padding:28px;color:var(--text-s)">No history found.</td></tr>`;
    return;
  }

  tbodyEl.innerHTML = DB.stockHistory
    .map(normalizeHistory)
    .map(h => {
      const tag = h.action === 'Added'
        ? '<span class="tag tag-g"><i class="bi bi-plus-circle-fill"></i> Added</span>'
        : '<span class="tag tag-o"><i class="bi bi-arrow-right-circle-fill"></i> Distributed</span>';
      return `<tr>
        <td class="col-soft">${fmt(h.date)}</td>
        <td><strong>${h.item}</strong></td>
        <td>${tag}</td>
        <td><strong>${h.qty}</strong></td>
        <td class="col-soft fs-13">${h.detail}</td>
      </tr>`;
    }).join('');
}

// ── Distribution page date filter ──────────────────────────────
function filterDistHistory(filter) {
  // Update active tab
  document.querySelectorAll('#dist-filter-row .ptab').forEach((b, i) =>
    b.classList.toggle('active', ['today','yesterday','week','month','all'][i] === filter));

  const now       = new Date();
  const todayStr  = now.toISOString().split('T')[0];
  const yest      = new Date(now - 86400000).toISOString().split('T')[0];
  const weekAgo   = new Date(now - 7*86400000).toISOString().split('T')[0];
  const monthAgo  = new Date(now - 30*86400000).toISOString().split('T')[0];

  // Only show distributions (not additions)
  let items = DB.stockHistory.map(normalizeHistory).filter(h => h.action === 'Distributed');

  if      (filter === 'today')     items = items.filter(h => h.date === todayStr);
  else if (filter === 'yesterday') items = items.filter(h => h.date === yest);
  else if (filter === 'week')      items = items.filter(h => h.date >= weekAgo);
  else if (filter === 'month')     items = items.filter(h => h.date >= monthAgo);

  const tbodyEl = document.getElementById('stock-dist-tbody');
  if (!tbodyEl) return;

  tbodyEl.innerHTML = items.length
    ? items.map(h => `<tr>
        <td class="col-soft">${fmt(h.date)}</td>
        <td><strong>${h.item}</strong></td>
        <td><strong>${h.qty}</strong></td>
        <td>${h.detail}</td>
      </tr>`).join('')
    : `<tr><td colspan="4" class="text-center" style="padding:28px;color:var(--text-s)">No distribution records for this period.</td></tr>`;
}

// ── CHILDREN ────────────────────────────────────────────────────
function renderChildren(data) {
  const rows = data || DB.children;
  const boys = rows.filter(c => c.gender === 'Male').length;
  const girls = rows.filter(c => c.gender === 'Female').length;

  document.getElementById('child-stats').innerHTML = `
    <div class="scard"><div class="scard-icon bg-p"><i class="bi bi-people-fill col-p" style="font-size:24px"></i></div><div><div class="scard-val col-p">${rows.length}</div><div class="scard-lbl">Total Children</div></div></div>
    <div class="scard"><div class="scard-icon bg-s"><i class="bi bi-person-fill col-s" style="font-size:24px"></i></div><div><div class="scard-val col-s">${boys}</div><div class="scard-lbl">Boys</div></div></div>
    <div class="scard"><div class="scard-icon bg-pk"><i class="bi bi-person-fill col-pk" style="font-size:24px"></i></div><div><div class="scard-val col-pk">${girls}</div><div class="scard-lbl">Girls</div></div></div>
    <div class="scard"><div class="scard-icon bg-y"><i class="bi bi-calendar-plus-fill col-y" style="font-size:24px"></i></div><div><div class="scard-val col-y">${rows.filter(c => c.age <= 5).length}</div><div class="scard-lbl">Under 5 Years</div></div></div>
  `;

  document.getElementById('children-tbody').innerHTML = rows.length ? rows.map((c, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${c.child_name}</strong></td>
      <td>${c.age} yrs</td>
      <td><span class="tag ${c.gender === 'Male' ? 'tag-s' : 'tag-pk'}">${c.gender}</span></td>
      <td>${c.parent_name || '—'}</td>
      <td class="fs-13">${c.parent_mobile || '—'}</td>
      <td class="col-soft fs-13">${fmt(c.created_at)}</td>
      <td>
        <button class="tbl-btn tbl-btn-edit" onclick="openChildModal('${c.id}')" title="Edit"><i class="bi bi-pencil-fill"></i></button>
        <button class="tbl-btn tbl-btn-del"  onclick="deleteChild('${c.id}')"      title="Delete"><i class="bi bi-trash-fill"></i></button>
      </td>
    </tr>`).join('')
    : '<tr><td colspan="8" class="text-center" style="padding:28px;color:var(--text-s)">No children found. Add your first child.</td></tr>';
}

function searchChildren(q) {
  renderChildren(DB.children.filter(c => c.child_name.toLowerCase().includes(q.toLowerCase()) || c.parent_name.toLowerCase().includes(q.toLowerCase())));
}

function filterChildren(g) {
  renderChildren(g ? DB.children.filter(c => c.gender === g) : DB.children);
}

function openChildModal(id) {
  editChildId = id || null;
  ['cm-name','cm-age','cm-parent','cm-mobile','cm-addr'].forEach(x => document.getElementById(x).value = '');
  document.getElementById('cm-gender').value = '';

  if (id) {
    const c = DB.children.find(x => String(x.id) === String(id));
    if (c) {
      document.getElementById('cm-name').value   = c.child_name    || '';
      document.getElementById('cm-age').value    = c.age           || '';
      document.getElementById('cm-gender').value = c.gender        || '';
      document.getElementById('cm-parent').value = c.parent_name   || '';
      document.getElementById('cm-mobile').value = c.parent_mobile || '';
      document.getElementById('cm-addr').value   = c.address       || '';
    }
  }
  new bootstrap.Modal(document.getElementById('childModal')).show();
}

async function saveChild() {
  const name   = document.getElementById('cm-name').value.trim();
  const age    = parseInt(document.getElementById('cm-age').value);
  const gender = document.getElementById('cm-gender').value;
  const parent = document.getElementById('cm-parent').value.trim();
  const mobile = document.getElementById('cm-mobile').value.trim();
  const addr   = document.getElementById('cm-addr').value.trim();

  if (!name)   { toast('Enter child name', 'error'); return; }
  if (!gender) { toast('Select gender', 'error'); return; }
  if (isNaN(age) || age < 0) { toast('Enter valid age', 'error'); return; }

  const payload = { child_name: name, age, gender, parent_name: parent, parent_mobile: mobile, address: addr };

  if (editChildId) {
    const res = await apiFetch(`/children/${editChildId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    if (res.success) {
      toast(`✅ Updated ${name}'s record!`, 'success');
    } else {
      toast(res.message || 'Failed to update child', 'error');
      return;
    }
  } else {
    const res = await apiFetch('/children', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res.success) {
      toast(`✅ Added ${name} to children records!`, 'success');
    } else {
      toast(res.message || 'Failed to add child', 'error');
      return;
    }
  }

  bootstrap.Modal.getInstance(document.getElementById('childModal')).hide();
  
  // Refresh children data
  const fetchRes = await apiFetch('/children');
  if (fetchRes.success) {
    DB.children = fetchRes.data;
    renderChildren();
  }
}

async function deleteChild(id) {
  const c = DB.children.find(x => String(x.id) === String(id));
  if (!c) return;
  if (!confirm(`Delete ${c.child_name}'s record? This cannot be undone.`)) return;
  
  const res = await apiFetch(`/children/${id}`, { method: 'DELETE' });
  if (res.success) {
    toast('Child record deleted.', 'info');
    const fetchRes = await apiFetch('/children');
    if (fetchRes.success) {
      DB.children = fetchRes.data;
      renderChildren();
    }
  } else {
    toast(res.message || 'Failed to delete child', 'error');
  }
}

// ── ATTENDANCE ──────────────────────────────────────────────────

// Calendar state
let calYear  = new Date().getFullYear();
let calMonth = new Date().getMonth();
let attSelectedDate = new Date().toISOString().split('T')[0];

function initAttendancePage() {
  const today = new Date().toISOString().split('T')[0];
  attSelectedDate = today;
  calYear  = new Date().getFullYear();
  calMonth = new Date().getMonth();
  if (!DB.attendance.find(a => a.date === today)) {
    DB.attendance.push({ id: uid(), date: today, records: {}, saved: false });
  }
  renderCalendar();
  renderAttendance(today);
  renderAttendanceHistory();
}

function renderCalendar() {
  const today    = new Date().toISOString().split('T')[0];
  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysInM  = new Date(calYear, calMonth + 1, 0).getDate();
  const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const dayNames   = ['Su','Mo','Tu','We','Th','Fr','Sa'];
  document.getElementById('cal-month-label').textContent = `${monthNames[calMonth]} ${calYear}`;
  const savedDates = new Set(DB.attendance.filter(a => a.saved).map(a => a.date));
  let html = dayNames.map(d => `<div class="att-cal-day-name">${d}</div>`).join('');
  for (let i = 0; i < firstDay; i++) html += `<div class="att-cal-cell empty"></div>`;
  for (let d = 1; d <= daysInM; d++) {
    const ds = `${calYear}-${String(calMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    let cls = 'att-cal-cell';
    if (ds === today)   cls += ' today';
    else if (ds > today) cls += ' future';
    if (savedDates.has(ds)) cls += ' saved';
    if (ds === attSelectedDate && ds !== today) cls += ' selected';
    html += `<div class="${cls}" onclick="selectAttDate('${ds}')">${d}</div>`;
  }
  document.getElementById('att-calendar').innerHTML = html;
}

function calNav(dir) {
  calMonth += dir;
  if (calMonth > 11) { calMonth = 0; calYear++; }
  if (calMonth < 0)  { calMonth = 11; calYear--; }
  renderCalendar();
}

function selectAttDate(ds) {
  attSelectedDate = ds;
  renderCalendar();
  renderAttendance(ds);
}

function renderAttendance(dateStr) {
  const today   = new Date().toISOString().split('T')[0];
  const isToday = dateStr === today;
  const days    = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const d       = new Date(dateStr + 'T00:00:00');
  const display = d.toLocaleDateString('en-IN', { day:'numeric', month:'long', year:'numeric' });
  const dayName = days[d.getDay()];
  const banner  = document.getElementById('att-date-display');
  const badge   = document.getElementById('att-mode-badge');
  if (banner) banner.textContent = `${display} (${dayName})`;
  if (badge)  { badge.textContent = isToday ? 'Today — Mark Now' : 'History View'; badge.className = 'att-today-badge' + (isToday ? '' : ' history'); }
  const saveBtn = document.getElementById('save-att-btn');
  if (saveBtn) saveBtn.style.display = isToday ? '' : 'none';
  let rec = DB.attendance.find(a => a.date === dateStr);
  if (!rec) { rec = { id: uid(), date: dateStr, records: {}, saved: false }; DB.attendance.push(rec); }
  const tbody = document.getElementById('attendance-tbody');
  if (!tbody) return;
  if (!DB.children.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:36px;color:var(--text-s)"><div style="font-size:40px">👶</div><div style="margin-top:10px;font-weight:700">No children enrolled yet.</div></td></tr>`;
    updateAttendanceStats(dateStr); renderAttSummary(dateStr); return;
  }
  tbody.innerHTML = DB.children.map((c, i) => {
    const status    = rec.records[c.id] || '';
    const isPresent = status === 'Present';
    const isAbsent  = status === 'Absent';
    const statusBadge = status
      ? `<span class="att-status-badge ${isPresent ? 'att-present' : 'att-absent'}"><i class="bi bi-${isPresent ? 'check-circle-fill' : 'x-circle-fill'}"></i> ${status}</span>`
      : `<span class="att-status-badge att-unmarked"><i class="bi bi-dash"></i> Not Marked</span>`;
    if (!isToday) return `<tr><td>${i+1}</td><td><strong>${c.child_name}</strong></td><td>${c.age} yrs</td><td><span class="tag ${c.gender==='Male'?'tag-s':'tag-pk'}">${c.gender}</span></td><td>${statusBadge}</td><td>${statusBadge}</td></tr>`;
    return `<tr>
      <td>${i+1}</td>
      <td><strong>${c.child_name}</strong></td>
      <td>${c.age} yrs</td>
      <td><span class="tag ${c.gender==='Male'?'tag-s':'tag-pk'}">${c.gender}</span></td>
      <td><div style="display:flex;gap:8px">
        <button class="att-btn ${isPresent?'present':''}" onclick="markAttendance('${dateStr}','${c.id}','Present')"><i class="bi bi-check-circle-fill"></i> Present</button>
        <button class="att-btn ${isAbsent?'absent':''}"  onclick="markAttendance('${dateStr}','${c.id}','Absent')"><i class="bi bi-x-circle-fill"></i> Absent</button>
      </div></td>
      <td>${statusBadge}</td>
    </tr>`;
  }).join('');
  updateAttendanceStats(dateStr);
  renderAttSummary(dateStr);
  renderAttendancePhoto(dateStr);
}

function markAttendance(date, childId, status) {
  let rec = DB.attendance.find(a => a.date === date);
  if (!rec) { rec = { id: uid(), date, records: {}, saved: false }; DB.attendance.push(rec); }
  if (rec.records[childId] === status) delete rec.records[childId];
  else rec.records[childId] = status;
  renderAttendance(date);
}

function updateAttendanceStats(dateStr) {
  const rec     = DB.attendance.find(a => a.date === dateStr);
  const map     = rec ? rec.records : {};
  const total   = DB.children.length;
  const present = Object.values(map).filter(v => v === 'Present').length;
  const absent  = Object.values(map).filter(v => v === 'Absent').length;
  const unmarked= total - present - absent;
  const pct     = total > 0 ? Math.round((present/total)*100) : 0;
  const el = document.getElementById('att-stats');
  if (!el) return;
  el.innerHTML = `
    <div class="scard"><div class="scard-icon bg-p"><i class="bi bi-people-fill col-p" style="font-size:22px"></i></div><div><div class="scard-val col-p">${total}</div><div class="scard-lbl">Total Children</div></div></div>
    <div class="scard" style="cursor:pointer" onclick="filterAttendance('Present')"><div class="scard-icon bg-g"><i class="bi bi-check-circle-fill col-g" style="font-size:22px"></i></div><div><div class="scard-val col-g">${present}</div><div class="scard-lbl">Present</div></div></div>
    <div class="scard" style="cursor:pointer" onclick="filterAttendance('Absent')"><div class="scard-icon bg-r"><i class="bi bi-x-circle-fill col-r" style="font-size:22px"></i></div><div><div class="scard-val col-r">${absent}</div><div class="scard-lbl">Absent</div></div></div>
    <div class="scard"><div class="scard-icon bg-y"><i class="bi bi-dash-circle-fill col-y" style="font-size:22px"></i></div><div><div class="scard-val col-y">${unmarked}</div><div class="scard-lbl">Unmarked</div></div></div>
    <div class="scard"><div class="scard-icon bg-t"><i class="bi bi-percent col-t" style="font-size:22px"></i></div><div><div class="scard-val col-t">${pct}%</div><div class="scard-lbl">Attendance %</div></div></div>
  `;
}

function renderAttSummary(dateStr) {
  const el = document.getElementById('att-summary-body');
  if (!el) return;
  const rec = DB.attendance.find(a => a.date === dateStr);
  if (!rec || !Object.keys(rec.records).length) {
    el.innerHTML = `<div class="palert palert-ok" style="margin:0"><i class="bi bi-info-circle-fill"></i> No attendance marked yet.</div>`;
    return;
  }
  const total   = DB.children.length;
  const present = Object.values(rec.records).filter(v => v === 'Present').length;
  const absent  = Object.values(rec.records).filter(v => v === 'Absent').length;
  const pct     = total > 0 ? Math.round((present/total)*100) : 0;
  const col     = pct >= 80 ? '#10B981' : pct >= 50 ? '#F59E0B' : '#EF4444';
  el.innerHTML = `
    <div class="att-sum-grid mb-3">
      <div class="att-sum-card att-sum-present"><div class="att-sum-num">${present}</div><div class="att-sum-lbl">Present</div></div>
      <div class="att-sum-card att-sum-absent"><div class="att-sum-num">${absent}</div><div class="att-sum-lbl">Absent</div></div>
    </div>
    <div style="text-align:center;margin-bottom:10px"><div style="font-family:'Baloo 2',cursive;font-size:32px;font-weight:800;color:${col}">${pct}%</div><div style="font-size:12px;color:var(--text-s);font-weight:700">Attendance Rate</div></div>
    <div class="pbar"><div class="pbar-fill" style="width:${pct}%;background:${col}"></div></div>
    ${rec.saved ? '<div class="palert palert-ok" style="margin-top:10px;padding:8px 12px;font-size:12px"><i class="bi bi-check-circle-fill"></i> Saved</div>' : ''}
  `;
}

function filterAttendance(status) {
  document.querySelectorAll('#attendance-tbody tr').forEach(row => {
    const badge = row.querySelector('.att-status-badge');
    if (!badge) return;
    row.style.opacity = badge.textContent.trim().toLowerCase().includes(status.toLowerCase()) ? '1' : '0.3';
  });
}

function searchAttendance(q) {
  document.querySelectorAll('#attendance-tbody tr').forEach(row => {
    const name = row.cells[1]?.textContent.toLowerCase() || '';
    row.style.display = name.includes(q.toLowerCase()) ? '' : 'none';
  });
}

async function saveAttendance() {
  const dateStr = attSelectedDate || new Date().toISOString().split('T')[0];
  let rec = DB.attendance.find(a => a.date === dateStr);
  if (!rec) { rec = { id: uid(), date: dateStr, records: {}, saved: false }; DB.attendance.push(rec); }
  const total  = DB.children.length;
  const marked = Object.keys(rec.records).length;
  if (marked < total && !confirm(`${total - marked} child${total-marked>1?'ren are':' is'} still unmarked. Save anyway?`)) return;

  const btn = document.getElementById('save-att-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Saving...'; }

  const res = await apiFetch('/attendance', {
    method: 'POST',
    body: JSON.stringify({ date: dateStr, records: rec.records })
  });

  if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Save Register'; }

  if (res.success) {
    rec.saved = true;
    const present = Object.values(rec.records).filter(v=>v==='Present').length;
    toast(`✅ Attendance saved to server! Present: ${present} / ${total}`, 'success');
    renderCalendar();
    renderAttendanceHistory();
    renderAttSummary(dateStr);
  } else {
    toast(res.message || 'Failed to save attendance', 'error');
  }
}

function renderAttendanceHistory() {
  const tbody = document.getElementById('att-history-tbody');
  if (!tbody) return;
  const saved = DB.attendance.filter(a => a.saved).sort((a,b) => b.date.localeCompare(a.date));
  if (!saved.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:28px;color:var(--text-s)">No saved records yet. Mark and save today's attendance first.</td></tr>`;
    return;
  }
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  tbody.innerHTML = saved.map(rec => {
    const total   = DB.children.length || Object.keys(rec.records).length;
    const present = Object.values(rec.records).filter(v=>v==='Present').length;
    const absent  = Object.values(rec.records).filter(v=>v==='Absent').length;
    const pct     = total > 0 ? Math.round((present/total)*100) : 0;
    const col     = pct >= 80 ? '#10B981' : pct >= 50 ? '#F59E0B' : '#EF4444';
    const d = new Date(rec.date + 'T00:00:00');
    return `<tr>
      <td><strong>${fmt(rec.date)}</strong></td>
      <td><span class="tag tag-s">${days[d.getDay()]}</span></td>
      <td>${total}</td>
      <td class="col-g" style="font-weight:800">${present}</td>
      <td class="col-r" style="font-weight:800">${absent}</td>
      <td><div class="att-pct-bar"><span class="att-pct-num" style="color:${col}">${pct}%</span><div class="att-pct-track"><div class="att-pct-fill" style="width:${pct}%;background:${col}"></div></div></div></td>
      <td><button class="tbl-btn tbl-btn-view" onclick="selectAttDate('${rec.date}')" title="View"><i class="bi bi-eye-fill"></i></button></td>
    </tr>`;
  }).join('');
}

function exportAttendancePdf() {
  if (typeof window.jspdf === 'undefined') { toast('jsPDF not loaded','error'); return; }
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF(); const u = DB.user || {};
  const today = new Date().toISOString().split('T')[0];
  doc.setFillColor(79,70,229); doc.rect(0,0,210,36,'F');
  doc.setTextColor(255,255,255); doc.setFontSize(16); doc.setFont('helvetica','bold');
  doc.text('Smart Anganwadi Portal',14,13);
  doc.setFontSize(10); doc.setFont('helvetica','normal');
  doc.text('Student Attendance Report',14,21);
  doc.text(`Center: ${u.center||''} | ${u.village||''}, ${u.mandal||''}, ${u.district||''}`,14,29);
  doc.setFillColor(245,243,255); doc.rect(0,36,210,18,'F');
  doc.setTextColor(30,27,75); doc.setFontSize(10); doc.setFont('helvetica','bold');
  doc.text(`Staff: ${u.name||''}`,14,45); doc.setFont('helvetica','normal');
  doc.text(`Date: ${new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'})}`,110,45);
  doc.text(`Total Children: ${DB.children.length}`,14,52);
  doc.text(`Saved Days: ${DB.attendance.filter(a=>a.saved).length}`,110,52);
  let y = 62;
  const saved = DB.attendance.filter(a=>a.saved).sort((a,b)=>a.date.localeCompare(b.date));
  if (saved.length) {
    doc.setFontSize(11); doc.setFont('helvetica','bold'); doc.setTextColor(30,27,75);
    doc.text('Attendance Summary',14,y); y+=6;
    const days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    doc.autoTable({ startY:y, head:[['Date','Day','Total','Present','Absent','Rate']],
      body: saved.map(r=>{ const tot=DB.children.length||Object.keys(r.records).length; const pre=Object.values(r.records).filter(v=>v==='Present').length; const abs=Object.values(r.records).filter(v=>v==='Absent').length; const pct=tot>0?Math.round(pre/tot*100):0; const dw=new Date(r.date+'T00:00:00'); return [fmt(r.date),days[dw.getDay()],tot,pre,abs,pct+'%']; }),
      headStyles:{fillColor:[79,70,229],textColor:255,fontStyle:'bold',fontSize:9}, bodyStyles:{fontSize:8}, alternateRowStyles:{fillColor:[245,243,255]}});
    y = doc.lastAutoTable.finalY + 12;
  }
  const todayRec = DB.attendance.find(a=>a.date===today);
  if (todayRec && Object.keys(todayRec.records).length) {
    if (y>230) { doc.addPage(); y=20; }
    doc.setFontSize(11); doc.setFont('helvetica','bold'); doc.setTextColor(30,27,75);
    doc.text(`Today's Register (${fmt(today)})`,14,y); y+=6;
    doc.autoTable({ startY:y, head:[['#','Child Name','Age','Gender','Status']],
      body: DB.children.map((c,i)=>{ const st=todayRec.records[c.id]||'Not Marked'; return [i+1,c.child_name,c.age+'y',c.gender,st]; }),
      headStyles:{fillColor:[16,185,129],textColor:255,fontStyle:'bold',fontSize:9}, bodyStyles:{fontSize:8}, alternateRowStyles:{fillColor:[240,253,244]},
      didDrawCell:(data)=>{ if(data.section==='body'&&data.column.index===4){ const v=data.cell.raw; if(v==='Present')data.cell.styles.textColor=[4,120,87]; else if(v==='Absent')data.cell.styles.textColor=[185,28,28]; else data.cell.styles.textColor=[100,100,100]; data.cell.styles.fontStyle='bold'; } }
    });
  }
  const pg=doc.internal.getNumberOfPages();
  for(let i=1;i<=pg;i++){ doc.setPage(i); doc.setFillColor(79,70,229); doc.rect(0,284,210,13,'F'); doc.setTextColor(255,255,255); doc.setFontSize(9); doc.text('Smart Anganwadi Portal | Government of Telangana',14,291); doc.text(`Page ${i} of ${pg}`,185,291); }
  doc.save(`Attendance_Report_${today}.pdf`);
  toast('📄 Attendance PDF downloaded!','success');
}

function changeAttendanceDate() {
  const d = document.getElementById('att-date')?.value;
  if (d) selectAttDate(d);
}

// ── DAILY MEALS ──────────────────────────────────────────────────
DB.dailyMeals = [];

async function loadMealsForDate(dateStr) {
  const dateEl = document.getElementById('meal-date');
  if (dateEl && dateEl.value !== dateStr) dateEl.value = dateStr;

  const res = await apiFetch('/daily-meals');
  if (res.success) {
    DB.dailyMeals = res.data;
  }
}

function renderMeals(dateStr) {
  const currentRecord = DB.dailyMeals.find(m => m.meal_date === dateStr);
  if (currentRecord) {
    document.getElementById('meal-children').value = currentRecord.children_served || 0;
    document.getElementById('meal-benef').value = currentRecord.beneficiaries_served || 0;
    document.getElementById('meal-menu').value = currentRecord.menu_served || '';
  } else {
    document.getElementById('meal-children').value = '';
    document.getElementById('meal-benef').value = '';
    document.getElementById('meal-menu').value = '';
  }

  const tbody = document.getElementById('meals-tbody');
  if (!tbody) return;

  tbody.innerHTML = DB.dailyMeals.length ? DB.dailyMeals.map(m => `
    <tr>
      <td>${fmt(m.meal_date)}</td>
      <td><strong>${m.children_served}</strong></td>
      <td><strong>${m.beneficiaries_served}</strong></td>
      <td>${m.menu_served}</td>
    </tr>
  `).join('') : '<tr><td colspan="4" class="text-center" style="padding:28px;color:var(--text-s)">No meal records found.</td></tr>';
}

async function changeMealDate() {
  const d = document.getElementById('meal-date').value;
  if (d) {
    renderMeals(d);
  }
}

async function saveDailyMeal() {
  const date = document.getElementById('meal-date').value || new Date().toISOString().split('T')[0];
  const children = parseInt(document.getElementById('meal-children').value) || 0;
  const benef = parseInt(document.getElementById('meal-benef').value) || 0;
  const menu = document.getElementById('meal-menu').value.trim();

  if (!menu) {
    toast('Please enter the menu served', 'error');
    return;
  }

  const btn = document.querySelector('#page-meals .btn-green');
  const oldText = btn ? btn.innerHTML : '';
  if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';

  const res = await apiFetch('/daily-meals', {
    method: 'POST',
    body: JSON.stringify({ meal_date: date, children_served: children, beneficiaries_served: benef, menu_served: menu })
  });

  if (btn) btn.innerHTML = oldText;

  if (res.success) {
    toast('✅ Meal record saved successfully!', 'success');
    await loadMealsForDate(date);
    renderMeals(date);
  } else {
    toast(res.message || 'Failed to save meal record', 'error');
  }
}

// ── BENEFICIARIES ────────────────────────────────────────────────
function renderBenef(data) {
  const rows = data || DB.beneficiaries;
  const pw   = rows.filter(b => b.category === 'Pregnant Woman').length;
  const lm   = rows.filter(b => b.category === 'Lactating Mother').length;

  document.getElementById('benef-stats').innerHTML = `
    <div class="scard"><div class="scard-icon bg-pk"><i class="bi bi-person-heart col-pk" style="font-size:24px"></i></div><div><div class="scard-val col-pk">${rows.length}</div><div class="scard-lbl">Total Beneficiaries</div></div></div>
    <div class="scard"><div class="scard-icon bg-r"><i class="bi bi-heart-pulse-fill col-r" style="font-size:24px"></i></div><div><div class="scard-val col-r">${pw}</div><div class="scard-lbl">Pregnant Women</div></div></div>
    <div class="scard"><div class="scard-icon bg-v"><i class="bi bi-person-fill col-v" style="font-size:24px"></i></div><div><div class="scard-val col-v">${lm}</div><div class="scard-lbl">Lactating Mothers</div></div></div>
    <div class="scard"><div class="scard-icon bg-g"><i class="bi bi-calendar-check-fill col-g" style="font-size:24px"></i></div><div><div class="scard-val col-g">${rows.length}</div><div class="scard-lbl">Active</div></div></div>
  `;

  document.getElementById('benef-tbody').innerHTML = rows.length ? rows.map((b, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${b.name}</strong></td>
      <td><span class="tag ${b.category === 'Pregnant Woman' ? 'tag-r' : 'tag-v'}">${b.category}</span></td>
      <td class="fs-13">${b.mobile || '—'}</td>
      <td class="fs-13">${b.address || '—'}</td>
      <td class="col-soft fs-13">${fmt(b.created_at)}</td>
      <td>
        <button class="tbl-btn tbl-btn-edit" onclick="openBenefModal('${b.id}')" title="Edit"><i class="bi bi-pencil-fill"></i></button>
        <button class="tbl-btn tbl-btn-del"  onclick="deleteBenef('${b.id}')"     title="Delete"><i class="bi bi-trash-fill"></i></button>
      </td>
    </tr>`).join('')
    : '<tr><td colspan="7" class="text-center" style="padding:28px;color:var(--text-s)">No beneficiaries found. Add your first beneficiary.</td></tr>';
}

function filterBenef(cat) {
  document.querySelectorAll('#page-beneficiary .ptab').forEach((b, i) =>
    b.classList.toggle('active', ['all','Pregnant Woman','Lactating Mother'][i] === cat));
  renderBenef(cat === 'all' ? DB.beneficiaries : DB.beneficiaries.filter(b => b.category === cat));
}

function searchBenef(q) {
  renderBenef(DB.beneficiaries.filter(b => b.name.toLowerCase().includes(q.toLowerCase())));
}

function openBenefModal(id) {
  editBenefId = id || null;
  ['bm-name','bm-mobile','bm-husband','bm-addr'].forEach(x => document.getElementById(x).value = '');
  document.getElementById('bm-cat').value = 'Pregnant Woman';

  if (id) {
    const b = DB.beneficiaries.find(x => String(x.id) === String(id));
    if (b) {
      document.getElementById('bm-name').value    = b.name     || '';
      document.getElementById('bm-cat').value     = b.category || 'Pregnant Woman';
      document.getElementById('bm-mobile').value  = b.mobile   || '';
      document.getElementById('bm-husband').value = b.husband  || '';
      document.getElementById('bm-addr').value    = b.address  || '';
    }
  }
  new bootstrap.Modal(document.getElementById('benefModal')).show();
}

async function saveBenef() {
  const name    = document.getElementById('bm-name').value.trim();
  const cat     = document.getElementById('bm-cat').value;
  const mobile  = document.getElementById('bm-mobile').value.trim();
  const husband = document.getElementById('bm-husband').value.trim();
  const address = document.getElementById('bm-addr').value.trim();

  if (!name) { toast('Enter beneficiary name', 'error'); return; }

  const payload = { name, category: cat, mobile, address, husband };

  if (editBenefId) {
    const res = await apiFetch(`/beneficiaries/${editBenefId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    if (res.success) {
      toast(`✅ Updated ${name}'s record!`, 'success');
    } else {
      toast(res.message || 'Failed to update beneficiary', 'error');
      return;
    }
  } else {
    const res = await apiFetch('/beneficiaries', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res.success) {
      toast(`✅ Added ${name} to beneficiaries!`, 'success');
    } else {
      toast(res.message || 'Failed to add beneficiary', 'error');
      return;
    }
  }

  bootstrap.Modal.getInstance(document.getElementById('benefModal')).hide();
  
  // Refresh beneficiaries data
  const fetchRes = await apiFetch('/beneficiaries');
  if (fetchRes.success) {
    DB.beneficiaries = fetchRes.data;
    renderBenef();
  }
}

async function deleteBenef(id) {
  const b = DB.beneficiaries.find(x => String(x.id) === String(id));
  if (!b) return;
  if (!confirm(`Delete ${b.name}'s record? This cannot be undone.`)) return;
  
  const res = await apiFetch(`/beneficiaries/${id}`, { method: 'DELETE' });
  if (res.success) {
    toast('Beneficiary deleted.', 'info');
    const fetchRes = await apiFetch('/beneficiaries');
    if (fetchRes.success) {
      DB.beneficiaries = fetchRes.data;
      renderBenef();
    }
  } else {
    toast(res.message || 'Failed to delete beneficiary', 'error');
  }
}

// ── STORIES ──────────────────────────────────────────────────────

const TYPE_META = {
  url:   { icon: 'bi-link-45deg',             label: 'Link',  cls: 'type-url'   },
  video: { icon: 'bi-play-circle-fill',        label: 'Video', cls: 'type-video' },
  pdf:   { icon: 'bi-file-earmark-pdf-fill',   label: 'PDF',   cls: 'type-pdf'   },
  text:  { icon: 'bi-file-text-fill',          label: 'Text',  cls: 'type-text'  },
};

let _storyLangFilter = 'all';
let _storyCatFilter  = '';
let _storyTypeFilter = 'all';
let _storySearch     = '';

function _applyStoryFilters() {
  let data = DB.stories || [];
  if (_storyLangFilter !== 'all') data = data.filter(s => s.language === _storyLangFilter);
  if (_storyCatFilter)            data = data.filter(s => s.category === _storyCatFilter);
  if (_storyTypeFilter !== 'all') data = data.filter(s => (s.content_type || 'text') === _storyTypeFilter);
  if (_storySearch)               data = data.filter(s => s.title.toLowerCase().includes(_storySearch) || (s.preview||'').toLowerCase().includes(_storySearch));
  renderStories(data);
}

const THUMB_COLORS = ['#FFE4D6','#D6E8FF','#ECD6FF','#D6FFE8','#FFF4D6','#D6F4FF','#FFE8D6','#D6FFD8'];

function renderStories(data) {
  const grid = document.getElementById('story-grid');
  if (!grid) return;

  if (!data || !data.length) {
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:56px;color:var(--text-s)"><div style="font-size:56px">📚</div><div style="margin-top:14px;font-weight:700;font-size:16px">No stories found. Be the first to add one!</div></div>';
    return;
  }

  grid.innerHTML = data.map((s, i) => {
    const ct   = s.content_type || 'text';
    const tm   = TYPE_META[ct] || TYPE_META.text;
    const myCenter = DB.user && s.center_id === DB.user.center_id;

    // Action button label
    const btnLabel = ct === 'url'   ? '🌐 Open Link'
                   : ct === 'video' ? '▶️ Watch'
                   : ct === 'pdf'   ? '📄 View PDF'
                   : '📖 Read';

    return `
    <div class="stcard">
      <div class="stcard-thumb" style="background:${s.color || THUMB_COLORS[i % THUMB_COLORS.length]}">
        ${s.emoji || '📖'}
        <div class="stcard-type-badge ${tm.cls}"><i class="bi ${tm.icon}"></i>${tm.label}</div>
      </div>
      <div class="stcard-body">
        <div class="stcard-title">${s.title}</div>
        <div class="stcard-meta">
          <span class="tag tag-s">${s.category || 'Moral Stories'}</span>
          <span class="tag ${s.language === 'Telugu' ? 'tag-o' : s.language === 'Hindi' ? 'tag-v' : 'tag-t'}">${s.language}</span>
          ${s.is_global ? '<span class="tag" style="background:rgba(99,102,241,.12);color:#6366f1"><i class="bi bi-globe2"></i> Global</span>' : ''}
        </div>
        ${s.preview ? `<div style="font-size:12px;color:var(--text-s);margin-top:8px;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">${s.preview}</div>` : ''}
      </div>
      <div class="stcard-actions" style="display:flex;gap:6px;width:100%;">
        <button style="flex:1;border-radius:8px;font-size:13px;font-weight:700;border:none;padding:8px;cursor:pointer;background:var(--green-l);color:var(--green)" onclick="openStoryViewer('${s.id}')">${btnLabel}</button>
        <button style="width:36px;border-radius:8px;border:none;padding:0;cursor:pointer;background:var(--primary-l);color:var(--primary);font-size:16px;display:flex;align-items:center;justify-content:center;" onclick="downloadStoryFile('${s.id}')" title="Download Story"><i class="bi bi-download"></i></button>
        ${myCenter ? `<button style="width:36px;border-radius:8px;border:none;padding:0;cursor:pointer;background:var(--red-l);color:var(--red);font-size:16px;display:flex;align-items:center;justify-content:center;" onclick="deleteStory('${s.id}')" title="Delete"><i class="bi bi-trash-fill"></i></button>` : ''}
      </div>
    </div>`;
  }).join('');
}

function filterStories(lang) {
  _storyLangFilter = lang;
  document.querySelectorAll('.tab-row .ptab[id^="stab-"]').forEach(b => b.classList.remove('active'));
  const tab = document.getElementById(`stab-${lang === 'all' ? 'all' : lang.toLowerCase()}`);
  if (tab) tab.classList.add('active');
  _applyStoryFilters();
}

function filterStoriesCat(cat) {
  _storyCatFilter = cat;
  _applyStoryFilters();
}

function filterStoryType(type) {
  _storyTypeFilter = type;
  document.querySelectorAll('[id^="ctype-"]').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById(`ctype-${type}`);
  if (btn) btn.classList.add('active');
  _applyStoryFilters();
}

function searchStories(q) {
  _storySearch = q.toLowerCase();
  _applyStoryFilters();
}

// ── Story type radio selection ───────────────────────────────────
function onStoryTypeChange() {
  const val = document.querySelector('input[name="sm-ctype"]:checked')?.value || 'text';
  ['url','video','pdf','text'].forEach(t => {
    const sec   = document.getElementById(`ct-section-${t}`);
    const lbl   = document.getElementById(`ct-label-${t}`);
    const isActive = t === val;
    if (sec) sec.style.display = isActive ? 'block' : 'none';
    if (lbl) {
      lbl.style.borderColor  = isActive ? 'var(--primary)' : 'var(--border)';
      lbl.style.background   = isActive ? 'var(--primary-l)' : '';
      lbl.style.color        = isActive ? 'var(--primary)' : '';
    }
  });
  const saveLabel = document.getElementById('sm-save-label');
  if (saveLabel) {
    saveLabel.textContent = val === 'url' ? 'Save Link Story'
                          : val === 'video' ? 'Save Video Story'
                          : val === 'pdf'   ? 'Save PDF Story'
                          : 'Save Text Story';
  }
}

// ── File upload helpers ──────────────────────────────────────────
async function _uploadStoryFile(file, type) {
  const statusEl = document.getElementById(`${type}-upload-status`);
  const dropZone = document.getElementById(`${type}-drop-zone`);
  if (statusEl) { statusEl.style.display = 'block'; statusEl.innerHTML = `<span style="color:var(--primary)"><i class="bi bi-arrow-repeat spin"></i> Uploading ${file.name}…</span>`; }
  if (dropZone) { dropZone.innerHTML = `<div style="color:var(--primary);font-weight:700"><i class="bi bi-arrow-repeat spin"></i> Uploading…</div>`; }

  const form = new FormData();
  form.append('file', file);

  const token = localStorage.getItem('token');
  try {
    const res = await fetch(`${API_URL}/upload/file`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: form
    });
    const json = await res.json();
    if (json.success) {
      const url = json.data.file_url;
      const hiddenEl = document.getElementById(`sm-${type}-url-hidden`);
      if (hiddenEl) { hiddenEl.textContent = url; hiddenEl.dataset.url = url; }
      if (statusEl) statusEl.innerHTML = `<span style="color:var(--green)"><i class="bi bi-check-circle-fill"></i> Uploaded: ${file.name}</span>`;
      if (dropZone) dropZone.innerHTML = `<i class="bi bi-check-circle-fill" style="font-size:28px;color:var(--green)"></i><div style="font-weight:700;margin-top:8px;color:var(--green)">${file.name}</div><div style="font-size:12px;color:var(--text-s)">File ready</div>`;
      return url;
    } else {
      if (statusEl) statusEl.innerHTML = `<span style="color:var(--red)"><i class="bi bi-x-circle-fill"></i> Upload failed: ${json.message}</span>`;
      if (dropZone) dropZone.innerHTML = `<i class="bi bi-x-circle-fill" style="font-size:28px;color:var(--red)"></i><div style="font-weight:700;margin-top:8px;color:var(--red)">${json.message}</div>`;
      return null;
    }
  } catch(e) {
    if (statusEl) statusEl.innerHTML = `<span style="color:var(--red)"><i class="bi bi-x-circle-fill"></i> Upload error: ${e.message}</span>`;
    return null;
  }
}

function handleFileSelect(event, type) {
  const file = event.target.files[0];
  if (file) _uploadStoryFile(file, type);
}

function handleFileDrop(event, type) {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (file) _uploadStoryFile(file, type);
  const dz = document.getElementById(`${type}-drop-zone`);
  if (dz) dz.classList.remove('drag-over');
}

// ── Open story modal ─────────────────────────────────────────────
function openStoryModal() {
  // Reset form
  ['sm-title','sm-emoji','sm-preview','sm-url-link','sm-youtube-url','sm-pdf-url-direct'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  ['sm-video-url-hidden','sm-pdf-url-hidden','sm-audio-url-hidden'].forEach(id => { const el = document.getElementById(id); if (el) { el.textContent = ''; el.dataset.url = ''; } });
  ['video-upload-status','pdf-upload-status','audio-upload-status'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });
  // Reset drop zones
  ['video','pdf','audio'].forEach(t => {
    const dz = document.getElementById(`${t}-drop-zone`);
    if (dz) dz.innerHTML = t === 'video'
      ? '<i class="bi bi-cloud-arrow-up-fill" style="font-size:32px;color:#ef4444"></i><div style="font-weight:700;margin-top:8px">Click or drag video file here</div><div style="font-size:12px;color:var(--text-s)">MP4 · WebM · AVI · MOV (max 100MB)</div>'
      : t === 'pdf'
      ? '<i class="bi bi-file-earmark-pdf-fill" style="font-size:32px;color:#f97316"></i><div style="font-weight:700;margin-top:8px">Click or drag PDF file here</div><div style="font-size:12px;color:var(--text-s)">PDF (max 10MB)</div>'
      : '<i class="bi bi-mic-fill" style="font-size:24px;color:var(--primary)"></i><div style="font-weight:600;margin-top:4px">Upload Audio File (MP3/WAV)</div><div style="font-size:11px;color:var(--text-s)">Max 20MB</div>';
  });
  // Reset to 'text' type
  const textRadio = document.getElementById('ct-text');
  if (textRadio) { textRadio.checked = true; onStoryTypeChange(); }
  new bootstrap.Modal(document.getElementById('storyModal')).show();
}

// ── Save story ───────────────────────────────────────────────────
async function saveStory() {
  const title    = document.getElementById('sm-title')?.value.trim();
  const lang     = document.getElementById('sm-lang')?.value;
  const cat      = document.getElementById('sm-cat')?.value;
  const emoji    = document.getElementById('sm-emoji')?.value || '📖';
  const preview  = document.getElementById('sm-preview')?.value.trim();
  const isGlobal = document.getElementById('sm-global')?.value !== 'false';
  const ctype    = document.querySelector('input[name="sm-ctype"]:checked')?.value || 'text';

  if (!title) { toast('⚠️ Enter a story title', 'error'); return; }

  const payload = { title, language: lang, category: cat, emoji, preview, content_type: ctype, is_global: isGlobal };

  // Collect content URLs per type
  if (ctype === 'url') {
    payload.url_link = document.getElementById('sm-url-link')?.value.trim();
    if (!payload.url_link) { toast('⚠️ Enter a URL link for this story', 'error'); return; }
  } else if (ctype === 'video') {
    payload.youtube_url = document.getElementById('sm-youtube-url')?.value.trim();
    const uploadedVideo = document.getElementById('sm-video-url-hidden')?.dataset?.url || '';
    if (uploadedVideo) payload.video_url = uploadedVideo;
    if (!payload.youtube_url && !payload.video_url) { toast('⚠️ Add a YouTube URL or upload a video file', 'error'); return; }
  } else if (ctype === 'pdf') {
    const directPdf = document.getElementById('sm-pdf-url-direct')?.value.trim();
    const uploadedPdf = document.getElementById('sm-pdf-url-hidden')?.dataset?.url || '';
    payload.pdf_url = uploadedPdf || directPdf;
    if (!payload.pdf_url) { toast('⚠️ Add a PDF URL or upload a PDF file', 'error'); return; }
  }

  const btn = document.getElementById('sm-save-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving…'; }

  // Extract optional audio URL
  const uploadedAudio = document.getElementById('sm-audio-url-hidden')?.dataset?.url || '';
  if (uploadedAudio) {
    payload.audio_url = uploadedAudio;
  }

  const res = await apiFetch('/stories', { method: 'POST', body: JSON.stringify(payload) });

  if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-upload"></i> <span id="sm-save-label">Add Story</span>'; }

  if (res.success) {
    bootstrap.Modal.getInstance(document.getElementById('storyModal')).hide();
    toast(`✅ "${title}" added to the library!`, 'success');
    const fetchRes = await apiFetch('/stories');
    if (fetchRes.success) { DB.stories = fetchRes.data; _applyStoryFilters(); }
  } else {
    toast(res.message || 'Failed to save story', 'error');
  }
}

// ── Delete story ─────────────────────────────────────────────────
async function deleteStory(id) {
  const s = DB.stories.find(x => String(x.id) === String(id));
  if (!s) return;
  if (!confirm(`Delete "${s.title}"? This cannot be undone.`)) return;
  const res = await apiFetch(`/stories/${id}`, { method: 'DELETE' });
  if (res.success) {
    toast('Story deleted.', 'info');
    const fetchRes = await apiFetch('/stories');
    if (fetchRes.success) { DB.stories = fetchRes.data; _applyStoryFilters(); }
  } else {
    toast(res.message || 'Failed to delete story', 'error');
  }
}

// ── Story Viewer ─────────────────────────────────────────────────
function openStoryViewer(id) {
  const s = DB.stories.find(x => String(x.id) === String(id));
  if (!s) return;

  audioProgress = 0; audioPlaying = false;
  if (audioInterval) { clearInterval(audioInterval); audioInterval = null; }

  const ct = s.content_type || 'text';
  document.getElementById('sv-title').textContent = `${s.emoji || '📖'} ${s.title}`;

  let contentHtml = '';

  if (ct === 'url') {
    const link = s.url_link || s.youtube_url || '';
    // Try YouTube embed
    const ytMatch = link.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})/);
    if (ytMatch) {
      contentHtml = `<div style="position:relative;padding-top:56.25%;background:#000">
        <iframe src="https://www.youtube.com/embed/${ytMatch[1]}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none" allowfullscreen></iframe>
      </div>`;
    } else {
      contentHtml = `
      <div style="padding:32px;text-align:center">
        <div style="font-size:64px;margin-bottom:16px">🌐</div>
        <div style="font-size:18px;font-weight:700;margin-bottom:12px">${s.title}</div>
        <div style="color:var(--text-s);margin-bottom:24px">${s.preview || 'Click below to open the story link'}</div>
        <a href="${link}" target="_blank" rel="noopener" class="btn-submit" style="text-decoration:none;display:inline-flex;align-items:center;gap:8px;padding:14px 32px;border-radius:12px;font-size:16px">
          <i class="bi bi-box-arrow-up-right"></i> Open Story Link
        </a>
      </div>`;
    }

  } else if (ct === 'video') {
    const vurl = s.video_url || '';
    const yurl = s.youtube_url || '';
    const ytMatch = yurl.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})/);
    if (ytMatch) {
      contentHtml = `<div style="position:relative;padding-top:56.25%;background:#000">
        <iframe src="https://www.youtube.com/embed/${ytMatch[1]}?autoplay=0" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none" allowfullscreen></iframe>
      </div>`;
    } else if (vurl) {
      contentHtml = `
      <div style="background:rgba(255,255,255,0.05);backdrop-filter:blur(8px);padding:12px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <span style="font-size:13px;color:var(--text-s);display:flex;align-items:center;gap:6px;"><i class="bi bi-info-circle-fill" style="color:var(--primary)"></i> Want to keep a copy of this video?</span>
        <a href="${vurl}" download target="_blank" style="text-decoration:none;font-size:12px;padding:8px 16px;border-radius:8px;display:inline-flex;align-items:center;gap:6px;background:var(--primary);color:#fff;font-weight:700;box-shadow:0 2px 4px rgba(0,0,0,0.1);transition:transform 0.2s;" onmouseover="this.style.transform='scale(1.03)'" onmouseout="this.style.transform='scale(1)'">
          <i class="bi bi-download"></i> Download Video Story
        </a>
      </div>
      <video controls style="width:100%;max-height:480px;background:#000;display:block;">
        <source src="${vurl}">
        Your browser does not support the video tag.
      </video>`;
    } else {
      contentHtml = `<div style="padding:32px;text-align:center;color:var(--text-s)">No video source available.</div>`;
    }

  } else if (ct === 'pdf') {
    const pdfUrl = s.pdf_url || '';
    if (pdfUrl) {
      // Convert Google Drive share link to embed link
      const gdMatch = pdfUrl.match(/\/file\/d\/([^/]+)/);
      const embedUrl = gdMatch
        ? `https://drive.google.com/file/d/${gdMatch[1]}/preview`
        : pdfUrl;
      contentHtml = `
      <div style="background:rgba(255,255,255,0.05);backdrop-filter:blur(8px);padding:12px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <span style="font-size:13px;color:var(--text-s);display:flex;align-items:center;gap:6px;"><i class="bi bi-info-circle-fill" style="color:var(--primary)"></i> Having trouble viewing the PDF story? Extract it directly:</span>
        <a href="${pdfUrl}" download target="_blank" style="text-decoration:none;font-size:12px;padding:8px 16px;border-radius:8px;display:inline-flex;align-items:center;gap:6px;background:var(--primary);color:#fff;font-weight:700;box-shadow:0 2px 4px rgba(0,0,0,0.1);transition:transform 0.2s;" onmouseover="this.style.transform='scale(1.03)'" onmouseout="this.style.transform='scale(1)'">
          <i class="bi bi-download"></i> Download PDF Story
        </a>
      </div>
      <iframe src="${embedUrl}" style="width:100%;height:70vh;border:none" title="${s.title}"></iframe>`;
    } else {
      contentHtml = `<div style="padding:32px;text-align:center;color:var(--text-s)">PDF not available.</div>`;
    }

  } else {
    // text / fallback
    contentHtml = `
    <div style="padding:28px">
      <div style="font-size:64px;text-align:center;margin-bottom:16px">${s.emoji || '📖'}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-bottom:16px">
        <span class="tag tag-s">${s.category}</span>
        <span class="tag ${s.language === 'Telugu' ? 'tag-o' : s.language === 'Hindi' ? 'tag-v' : 'tag-t'}">${s.language}</span>
      </div>
      <div style="font-size:15px;line-height:1.8;color:var(--text-d)">${s.preview || 'No content available.'}</div>
      ${s.has_audio ? (s.audio_url ? `
      <div style="margin-top:24px;text-align:center">
        <div style="font-weight:600;margin-bottom:8px;color:var(--primary)"><i class="bi bi-volume-up-fill"></i> Audio Narration</div>
        <audio controls src="${s.audio_url}" style="width:100%;max-width:400px"></audio>
      </div>` : `
      <div class="audio-player" style="margin-top:24px">
        <div class="ap-title"><i class="bi bi-volume-up-fill" style="color:var(--primary)"></i> Audio Narration</div>
        <div class="ap-progress">
          <span id="ap-time">0:00</span>
          <div class="ap-track" onclick="scrubAudio(event,this)"><div class="ap-fill" id="ap-fill" style="width:0%"></div></div>
          <span>2:30</span>
        </div>
        <div class="ap-controls">
          <button class="ap-btn ap-btn-side" onclick="prevAudio()"><i class="bi bi-skip-backward-fill"></i></button>
          <button class="ap-btn ap-btn-main" id="ap-play" onclick="toggleAudio(this)"><i class="bi bi-play-fill"></i></button>
          <button class="ap-btn ap-btn-side" onclick="nextAudio()"><i class="bi bi-skip-forward-fill"></i></button>
        </div>
      </div>`) : ''}
    </div>`;
  }

  document.getElementById('sv-body').innerHTML = contentHtml;
  new bootstrap.Modal(document.getElementById('storyViewModal')).show();
}

function downloadTextAsFile(filename, text) {
  const element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);
  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}

function downloadStoryFile(id) {
  const s = DB.stories.find(x => String(x.id) === String(id));
  if (!s) return;

  const ct = s.content_type || 'text';
  if (ct === 'pdf' && s.pdf_url) {
    window.open(s.pdf_url, '_blank');
    toast('📥 PDF download started', 'success');
  } else if (ct === 'video' && s.video_url) {
    window.open(s.video_url, '_blank');
    toast('📥 Video download started', 'success');
  } else if (ct === 'video' && s.youtube_url) {
    window.open(s.youtube_url, '_blank');
    toast('🌐 Opening YouTube link', 'info');
  } else if (ct === 'url' && s.url_link) {
    window.open(s.url_link, '_blank');
    toast('🌐 Opening story link', 'info');
  } else if (ct === 'audio' && s.audio_url) {
    window.open(s.audio_url, '_blank');
    toast('📥 Audio download started', 'success');
  } else {
    // Text story — download as TXT file!
    const textContent = `Title: ${s.title}\nLanguage: ${s.language}\nCategory: ${s.category}\n\nStory Content:\n${s.preview || 'No content available.'}`;
    downloadTextAsFile(`${s.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_story.txt`, textContent);
    toast('📥 Story text extracted & downloaded', 'success');
  }
}

function toggleAudio(btn) {
  audioPlaying = !audioPlaying;
  btn.innerHTML = audioPlaying ? '<i class="bi bi-pause-fill"></i>' : '<i class="bi bi-play-fill"></i>';
  if (audioPlaying) {
    audioInterval = setInterval(() => {
      audioProgress = Math.min(100, audioProgress + 0.5);
      const f = document.getElementById('ap-fill'); if (f) f.style.width = audioProgress + '%';
      const secs = Math.round(audioProgress * 1.5);
      const t = document.getElementById('ap-time');
      if (t) t.textContent = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
      if (audioProgress >= 100) { clearInterval(audioInterval); audioInterval = null; audioPlaying = false; btn.innerHTML = '<i class="bi bi-play-fill"></i>'; audioProgress = 0; }
    }, 150);
  } else {
    clearInterval(audioInterval); audioInterval = null;
  }
}
function scrubAudio(e, el) { const r = el.getBoundingClientRect(); audioProgress = Math.max(0, Math.min(100, ((e.clientX - r.left) / r.width) * 100)); }
function prevAudio() { audioProgress = 0;   const f = document.getElementById('ap-fill'); if (f) f.style.width = '0%'; }
function nextAudio() { audioProgress = 100; const f = document.getElementById('ap-fill'); if (f) f.style.width = '100%'; }

// Reset audio when modal is closed
document.addEventListener('hidden.bs.modal', () => {
  if (audioInterval) { clearInterval(audioInterval); audioInterval = null; }
  audioPlaying = false; audioProgress = 0;
});

// ── MEETINGS ─────────────────────────────────────────────────────
function renderMeetings(filter) {
  document.querySelectorAll('#page-meetings .ptab').forEach((b, i) =>
    b.classList.toggle('active', i === (filter === 'upcoming' ? 0 : 1)));

  const now  = new Date();
  const data = filter === 'upcoming'
    ? DB.meetings.filter(m => !m.completed && new Date(m.meeting_date) >= now)
    : DB.meetings;

  document.getElementById('meetings-grid').innerHTML = data.length ? data.map(m => {
    const d    = new Date(m.meeting_date);
    const past = d < now || m.completed;
    return `<div class="col-md-6 col-xl-4">
      <div class="meet-card" style="border-left-color:${past ? '#9CA3AF' : 'var(--primary)'}">
        <div class="meet-date-badge" style="background:${past ? 'var(--bg)' : 'var(--primary-l)'};color:${past ? 'var(--text-s)' : 'var(--primary)'}">
          <i class="bi bi-calendar3"></i> ${d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} &bull; ${d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
        </div>
        <div class="meet-title">${m.title}</div>
        <div class="meet-desc">${m.description || ''}</div>
        <div class="meet-loc"><i class="bi bi-geo-alt-fill" style="color:var(--primary)"></i> ${m.location || 'Center Hall'}</div>
        <div style="display:flex;gap:8px;margin-top:14px;align-items:center">
          ${past ? '<span class="tag tag-s"><i class="bi bi-check2-circle"></i> Completed</span>' : '<span class="tag tag-g"><i class="bi bi-clock"></i> Upcoming</span>'}
          <button class="tbl-btn tbl-btn-del" onclick="deleteMeeting('${m.id}')" style="margin-left:auto" title="Delete"><i class="bi bi-trash-fill"></i></button>
        </div>
      </div>
    </div>`;
  }).join('')
    : '<div class="col-12"><div class="palert palert-ok"><i class="bi bi-calendar-check"></i> No meetings found.</div></div>';
}

function filterMeetings(f) { renderMeetings(f); }

function openMeetingModal() {
  ['mm-title','mm-loc','mm-desc'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('mm-date').value = '';
  new bootstrap.Modal(document.getElementById('meetingModal')).show();
}

async function saveMeeting() {
  const title = document.getElementById('mm-title').value.trim();
  const date  = document.getElementById('mm-date').value;
  const loc   = document.getElementById('mm-loc').value.trim() || 'Center Hall';
  const desc  = document.getElementById('mm-desc').value.trim();

  if (!title) { toast('Enter meeting title', 'error'); return; }
  if (!date)  { toast('Select a date and time', 'error'); return; }

  const payload = {
    title: title,
    meeting_date: new Date(date).toISOString(),
    location: loc,
    description: desc
  };

  const res = await apiFetch('/meetings', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (res.success) {
    bootstrap.Modal.getInstance(document.getElementById('meetingModal')).hide();
    toast(`✅ Meeting "${title}" created!`, 'success');
    const fetchRes = await apiFetch('/meetings');
    if (fetchRes.success) {
      DB.meetings = fetchRes.data;
      renderMeetings('upcoming');
    }
  } else {
    toast(res.message || 'Failed to create meeting', 'error');
  }
}

async function deleteMeeting(id) {
  const m = DB.meetings.find(x => String(x.id) === String(id));
  if (!m) return;
  if (!confirm(`Delete "${m.title}"?`)) return;
  
  const res = await apiFetch(`/meetings/${id}`, { method: 'DELETE' });
  if (res.success) {
    toast('Meeting deleted.', 'info');
    const fetchRes = await apiFetch('/meetings');
    if (fetchRes.success) {
      DB.meetings = fetchRes.data;
      renderMeetings('upcoming');
    }
  } else {
    toast(res.message || 'Failed to delete meeting', 'error');
  }
}

// ── REPORTS ──────────────────────────────────────────────────────
function renderReports() {
  const reports = [
    { id: 'stock',        icon: 'bi-box-seam-fill',          bg: 'bg-o',  col: 'col-o',  title: 'Stock Management Report',   desc: 'Current inventory levels, stock status and remaining quantities for all items.',                    fn: 'downloadStockPdf()' },
    { id: 'distribution', icon: 'bi-arrow-right-circle-fill', bg: 'bg-g',  col: 'col-g',  title: 'Stock Distribution Report', desc: 'Complete history of all stock distributions with dates and beneficiary details.',                   fn: 'downloadDistributionPdf()' },
    { id: 'children',     icon: 'bi-people-fill',             bg: 'bg-p',  col: 'col-p',  title: 'Children Report',           desc: 'All enrolled children with parent details, age and gender breakdown.',                           fn: 'downloadChildrenPdf()' },
    { id: 'attendance',   icon: 'bi-calendar-check-fill',    bg: 'bg-info',col: 'text-info',title: 'Attendance Report',         desc: 'Complete history of child attendance rates and daily logs.',                                      fn: 'downloadAttendancePdf()' },
    { id: 'bmi',          icon: 'bi-heart-pulse-fill',        bg: 'bg-v',  col: 'col-v',  title: 'BMI & Nutrition Report',    desc: 'BMI values, nutrition status and AI recommendations for all children.',                          fn: 'downloadBmiPdf()' },
    { id: 'beneficiary',  icon: 'bi-person-heart',            bg: 'bg-pk', col: 'col-pk', title: 'Beneficiaries Report',      desc: 'Pregnant women and lactating mothers registered at the center.',                                  fn: 'downloadBenefPdf()' },
    { id: 'survey',       icon: 'bi-file-earmark-bar-graph-fill',bg: 'bg-y',col: 'col-y', title: 'Village Survey Report',     desc: 'Village demographic logs, families, and population tracking.',                                    fn: 'downloadSurveyPdf()' },
  ];

  const grid = document.getElementById('report-cards-grid');
  if (!grid) return;
  grid.innerHTML = reports.map(r => `
    <div class="col-md-6 col-xl-4">
      <div class="pcard report-card">
        <div class="report-card-icon ${r.bg}"><i class="bi ${r.icon} ${r.col}" style="font-size:28px"></i></div>
        <div class="report-card-title">${r.title}</div>
        <div class="report-card-desc">${r.desc}</div>
        <div class="report-card-actions">
          <button class="btn-ph btn-ph-outline" onclick="previewReport('${r.id}')"><i class="bi bi-eye-fill"></i> Preview</button>
          <button class="btn-pdf" onclick="${r.fn}"><i class="bi bi-file-earmark-pdf-fill"></i> Download PDF</button>
        </div>
      </div>
    </div>`).join('');

  // Stats row above cards
  const totalDist = DB.stockHistory.filter(h => h.action === 'Distributed').reduce((s, h) => s + h.qty, 0);
  const normalBmi = DB.bmiRecords.filter(r => r.category === 'Normal').length;
  const critBmi   = DB.bmiRecords.filter(r => r.category === 'Severe Underweight' || r.category === 'Underweight').length;
  document.getElementById('report-stats').innerHTML = `
    <div class="scard"><div class="scard-icon bg-p"><i class="bi bi-people-fill col-p" style="font-size:24px"></i></div><div><div class="scard-val col-p">${DB.children.length}</div><div class="scard-lbl">Total Children</div></div></div>
    <div class="scard"><div class="scard-icon bg-pk"><i class="bi bi-person-heart col-pk" style="font-size:24px"></i></div><div><div class="scard-val col-pk">${DB.beneficiaries.length}</div><div class="scard-lbl">Beneficiaries</div></div></div>
    <div class="scard"><div class="scard-icon bg-g"><i class="bi bi-arrow-right-circle-fill col-g" style="font-size:24px"></i></div><div><div class="scard-val col-g">${totalDist}</div><div class="scard-lbl">Items Distributed</div></div></div>
    <div class="scard"><div class="scard-icon bg-t"><i class="bi bi-heart-pulse-fill col-t" style="font-size:24px"></i></div><div><div class="scard-val col-t">${normalBmi}</div><div class="scard-lbl">Normal BMI Kids</div></div></div>
    <div class="scard"><div class="scard-icon bg-r"><i class="bi bi-exclamation-triangle-fill col-r" style="font-size:24px"></i></div><div><div class="scard-val col-r">${critBmi}</div><div class="scard-lbl">BMI Alerts</div></div></div>
  `;

  renderReportsHistory();
}

function previewReport(type) {
  const modal = document.getElementById('reportPreviewModal');
  const body  = document.getElementById('rpt-preview-body');
  if (!modal || !body) return;

  let html = '';
  if (type === 'stock') {
    html = `<div class="table-responsive"><table class="ptable"><thead><tr><th>Item</th><th>Category</th><th>In Stock</th><th>Distributed</th><th>Min Qty</th><th>Status</th></tr></thead><tbody>${DB.stock.map(s => {
      const dist = DB.stockHistory.filter(h=>h.item===s.item_name&&h.action==='Distributed').reduce((a,b)=>a+b.qty,0);
      const st   = s.qty<=s.minQty ? '<span class="tag tag-r">Critical</span>' : s.qty<=s.minQty*2 ? '<span class="tag tag-y">Low</span>' : '<span class="tag tag-g">Good</span>';
      return `<tr><td><strong>${s.item_name}</strong></td><td>${s.category}</td><td>${s.qty} ${s.unit}</td><td>${dist}</td><td>${s.minQty}</td><td>${st}</td></tr>`;
    }).join('')}</tbody></table></div>`;
  } else if (type === 'distribution') {
    const rows = DB.stockHistory.filter(h=>h.action==='Distributed');
    html = `<div class="table-responsive"><table class="ptable"><thead><tr><th>Date</th><th>Item</th><th>Qty</th><th>Details</th></tr></thead><tbody>${rows.map(h=>`<tr><td>${fmt(h.date)}</td><td><strong>${h.item}</strong></td><td>${h.qty}</td><td class="col-soft">${h.detail}</td></tr>`).join('')}</tbody></table></div>`;
  } else if (type === 'children') {
    html = `<div class="table-responsive"><table class="ptable"><thead><tr><th>#</th><th>Name</th><th>Age</th><th>Gender</th><th>Parent</th><th>Mobile</th></tr></thead><tbody>${DB.children.map((c,i)=>`<tr><td>${i+1}</td><td><strong>${c.child_name}</strong></td><td>${c.age}y</td><td>${c.gender}</td><td>${c.parent_name||'—'}</td><td>${c.parent_mobile||'—'}</td></tr>`).join('')}</tbody></table></div>`;
  } else if (type === 'attendance') {
    const grouped = {};
    DB.attendance.forEach(a => {
      if (a.saved) {
        const tot = DB.children.length || Object.keys(a.records).length;
        const present = Object.values(a.records).filter(v => v === 'Present').length;
        const absent = tot - present;
        const pct = tot > 0 ? Math.round((present / tot) * 100) : 0;
        grouped[a.date] = { total: tot, present, absent, rate: pct + '%' };
      }
    });
    const sortedDates = Object.keys(grouped).sort((a,b) => b.localeCompare(a));
    html = `<div class="table-responsive"><table class="ptable"><thead><tr><th>Date</th><th>Total Kids</th><th>Present</th><th>Absent</th><th>Attendance Rate</th></tr></thead><tbody>${sortedDates.map(d => `<tr><td><strong>${fmt(d)}</strong></td><td>${grouped[d].total}</td><td>${grouped[d].present}</td><td>${grouped[d].absent}</td><td><strong>${grouped[d].rate}</strong></td></tr>`).join('')}</tbody></table></div>`;
  } else if (type === 'bmi') {
    html = `<div class="table-responsive"><table class="ptable"><thead><tr><th>#</th><th>Name</th><th>Age</th><th>Height</th><th>Weight</th><th>BMI</th><th>Category</th></tr></thead><tbody>${DB.bmiRecords.map((r,i)=>`<tr><td>${i+1}</td><td><strong>${r.child_name}</strong></td><td>${r.age}y</td><td>${r.height}cm</td><td>${r.weight}kg</td><td><strong>${r.bmi}</strong></td><td>${bmiTag(r.category)}</td></tr>`).join('')}</tbody></table></div>`;
  } else if (type === 'beneficiary') {
    html = `<div class="table-responsive"><table class="ptable"><thead><tr><th>#</th><th>Name</th><th>Category</th><th>Mobile</th><th>Address</th></tr></thead><tbody>${DB.beneficiaries.map((b,i)=>`<tr><td>${i+1}</td><td><strong>${b.name}</strong></td><td><span class="tag ${b.category==='Pregnant Woman'?'tag-r':'tag-v'}">${b.category}</span></td><td>${b.mobile||'—'}</td><td>${b.address||'—'}</td></tr>`).join('')}</tbody></table></div>`;
  } else if (type === 'survey') {
    html = `<div class="table-responsive"><table class="ptable"><thead><tr><th>Village</th><th>Year/Month</th><th>Population</th><th>Families</th><th>Children</th><th>Pregnant</th><th>Lactating</th></tr></thead><tbody>${DB.villageSurveys.map(s => `<tr><td><strong>${s.village_name}</strong></td><td>${s.survey_year} / ${s.survey_month || 'Yearly'}</td><td>${s.total_population}</td><td>${s.total_families}</td><td>${s.total_children}</td><td>${s.pregnant_women}</td><td>${s.lactating_mothers}</td></tr>`).join('')}</tbody></table></div>`;
  }

  body.innerHTML = html;
  new bootstrap.Modal(modal).show();
}

function exportReport() {
  downloadStockPdf();
}

// ── FILL DEMO CREDENTIALS HELPER ─────────────────────────────────
function fillDemo(email, pass) {
  document.getElementById('login-email').value    = email;
  document.getElementById('login-password').value = pass;
  document.getElementById('login-err').style.display = 'none';
}

function filterDistHistory(filter) {
  document.querySelectorAll('#dist-filter-row .ptab').forEach((b, i) =>
    b.classList.toggle('active', ['today','yesterday','tomorrow','week','month','all'][i] === filter));

  const now       = new Date();
  const today     = now.toISOString().split('T')[0];
  const yesterday = new Date(now - 86400000).toISOString().split('T')[0];
  const tomorrow  = new Date(+now + 86400000).toISOString().split('T')[0];

  let filtered = DB.stockHistory.filter(h => h.action === 'Distributed');
  if (filter === 'today')     filtered = filtered.filter(h => h.date === today);
  else if (filter === 'yesterday') filtered = filtered.filter(h => h.date === yesterday);
  else if (filter === 'tomorrow')  filtered = filtered.filter(h => h.date === tomorrow);
  else if (filter === 'week')  {
    const weekAgo = new Date(now - 7*86400000).toISOString().split('T')[0];
    filtered = filtered.filter(h => h.date >= weekAgo);
  } else if (filter === 'month') {
    const monthAgo = new Date(now - 30*86400000).toISOString().split('T')[0];
    filtered = filtered.filter(h => h.date >= monthAgo);
  }

  const tbody = document.getElementById('stock-dist-tbody');
  if (!tbody) return;
  tbody.innerHTML = filtered.length
    ? filtered.map(h => `<tr>
        <td class="col-soft">${fmt(h.date)}</td>
        <td><strong>${h.item}</strong></td>
        <td><span class="tag tag-o"><i class="bi bi-arrow-right-circle-fill"></i> Distributed</span></td>
        <td><strong>${h.qty}</strong></td>
        <td class="col-soft fs-13">${h.detail}</td>
      </tr>`).join('')
    : '<tr><td colspan="5" class="text-center" style="padding:28px;color:var(--text-s)">No distribution records for this period.</td></tr>';
}

// ── PDF REPORTING VIA BACKEND ──────────────────────────────────────
async function downloadBackendReport(type) {
  toast(`Generating and downloading ${type} report PDF...`, 'info');
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_URL}/reports/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ report_type: type })
    });
    
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.message || 'Server error generating report');
    }
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}_report_${new Date().toISOString().slice(0,10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    toast(`✅ ${type} report downloaded!`, 'success');
    
    await refreshReportsHistory();
  } catch (error) {
    console.error(error);
    toast(`❌ Failed to generate report: ${error.message}`, 'error');
  }
}

function downloadStockPdf() { downloadBackendReport('stock'); }
function downloadDistributionPdf() { downloadBackendReport('distribution'); }
function downloadChildrenPdf() { downloadBackendReport('children'); }
function downloadAttendancePdf() { downloadBackendReport('attendance'); }
function downloadBmiPdf() { downloadBackendReport('bmi'); }
function downloadBenefPdf() { downloadBackendReport('beneficiary'); }
function downloadSurveyPdf() { downloadBackendReport('survey'); }
function triggerReportGenerate(type) { downloadBackendReport(type); }

async function refreshReportsHistory() {
  const res = await apiFetch('/reports/history');
  if (res.success) {
    DB.reportsHistory = res.data || [];
    renderReportsHistory();
  }
}

function renderReportsHistory() {
  const tbody = document.getElementById('reports-history-tbody');
  if (!tbody) return;
  
  const history = DB.reportsHistory || [];
  if (history.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="padding:28px;color:var(--text-s)">No reports generated yet. Click Download PDF on any report above.</td></tr>`;
    return;
  }
  
  tbody.innerHTML = history.map(r => {
    return `<tr>
      <td>${fmt(r.created_at)}</td>
      <td><strong>${r.report_type}</strong></td>
      <td class="col-soft">${r.generated_by || '—'}</td>
      <td>
        <a href="${r.pdf_url}" target="_blank" class="tbl-btn tbl-btn-view" style="width:auto;padding:4px 10px;font-size:12px;border-radius:8px;text-decoration:none;display:inline-flex;align-items:center;gap:4px">
          <i class="bi bi-download"></i> Download
        </a>
      </td>
    </tr>`;
  }).join('');
}

// ── ATTENDANCE PHOTOS ──────────────────────────────────────────────
function renderAttendancePhoto(dateStr) {
  const previewBox = document.getElementById('att-photo-preview-box');
  if (!previewBox) return;
  
  const photo = DB.attendancePhotos.find(p => p.upload_date === dateStr);
  if (photo) {
    previewBox.innerHTML = `
      <img src="${photo.image_url}" style="max-width:100%; max-height:200px; border-radius:8px; object-fit:cover;" />
      <div class="mt-2 d-flex justify-content-center gap-2">
        <button class="btn btn-sm btn-danger" onclick="deleteAttendancePhoto('${photo.id}')" style="font-size:11px;padding:2px 8px;"><i class="bi bi-trash"></i> Delete Photo</button>
      </div>
    `;
  } else {
    previewBox.innerHTML = `
      <i class="bi bi-image" style="font-size:32px;color:var(--text-s)"></i>
      <div style="font-size:13px;color:var(--text-s);margin-top:6px">No photo uploaded for this date</div>
    `;
  }
}

async function deleteAttendancePhoto(photoId) {
  if (!confirm('Are you sure you want to delete this attendance photo?')) return;
  const res = await apiFetch(`/attendance/photos/${photoId}`, { method: 'DELETE' });
  if (res.success) {
    toast('Attendance photo deleted.', 'info');
    DB.attendancePhotos = DB.attendancePhotos.filter(p => p.id !== photoId);
    renderAttendancePhoto(attSelectedDate);
  } else {
    toast(res.message || 'Failed to delete photo', 'error');
  }
}

async function uploadAttendancePhoto() {
  const fileInput = document.getElementById('att-photo-file');
  if (!fileInput || !fileInput.files.length) return;
  
  const file = fileInput.files[0];
  const dateStr = attSelectedDate || new Date().toISOString().split('T')[0];
  
  const previewBox = document.getElementById('att-photo-preview-box');
  if (previewBox) {
    previewBox.innerHTML = `
      <div class="spinner-border text-primary" role="status"></div>
      <div style="font-size:13px;color:var(--text-s);margin-top:6px">Uploading image...</div>
    `;
  }
  
  const reader = new FileReader();
  reader.onload = async function(e) {
    const base64Content = e.target.result.split(',')[1];
    const payload = {
      filename: file.name,
      content_base64: base64Content,
      upload_date: dateStr
    };
    
    const res = await apiFetch('/attendance/photos', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    
    fileInput.value = '';
    
    if (res.success) {
      toast('✅ Attendance photo uploaded successfully!', 'success');
      DB.attendancePhotos = DB.attendancePhotos.filter(p => p.upload_date !== dateStr);
      DB.attendancePhotos.push(res.data);
      renderAttendancePhoto(dateStr);
    } else {
      toast(res.message || 'Failed to upload photo', 'error');
      renderAttendancePhoto(dateStr);
    }
  };
  reader.onerror = function() {
    toast('Error reading file.', 'error');
    renderAttendancePhoto(dateStr);
  };
  reader.readAsDataURL(file);
}

// ================================================================
//  BMI & NUTRITION AI MODULE
// ================================================================

// ── BMI HELPERS ──────────────────────────────────────────────────
function calcBmi(height, weight) {
  if (!height || !weight || height <= 0) return null;
  return Math.round((weight / Math.pow(height / 100, 2)) * 10) / 10;
}

function getBmiCategory(bmi) {
  if (bmi === null) return 'Unknown';
  if (bmi < 14.0)  return 'Severe Underweight';
  if (bmi < 16.0)  return 'Underweight';
  if (bmi < 22.0)  return 'Normal';
  if (bmi < 26.0)  return 'Overweight';
  return 'Obese';
}

function getBmiConfig(category) {
  const map = {
    'Severe Underweight': { cls: 'bmi-severe', color: '#EF4444', bg: '#FEE2E2', dotBg: '#FEE2E2', dotCol: '#991B1B', icon: '🔴', tagCls: 'tag-r' },
    'Underweight':        { cls: 'bmi-under',  color: '#F59E0B', bg: '#FEF3C7', dotBg: '#FEF3C7', dotCol: '#92400E', icon: '🟠', tagCls: 'tag-y' },
    'Normal':             { cls: 'bmi-normal', color: '#10B981', bg: '#D1FAE5', dotBg: '#D1FAE5', dotCol: '#065F46', icon: '🟢', tagCls: 'tag-g' },
    'Overweight':         { cls: 'bmi-over',   color: '#EAB308', bg: '#FEF9C3', dotBg: '#FEF9C3', dotCol: '#854D0E', icon: '🟡', tagCls: 'tag-y' },
    'Obese':              { cls: 'bmi-obese',  color: '#F97316', bg: '#FFE4CC', dotBg: '#FFE4CC', dotCol: '#9A3412', icon: '🟤', tagCls: 'tag-o' },
  };
  return map[category] || map['Normal'];
}

function bmiTag(category) {
  const cfg = getBmiConfig(category);
  return `<span class="bmi-tag ${cfg.cls}">${cfg.icon} ${category}</span>`;
}

// ── AI NUTRITION ENGINE (local rule-based, no API needed) ─────────
function generateAiRecommendation(rec) {
  const { child_name, age, gender, height, weight, bmi, category } = rec;

  const data = {
    'Severe Underweight': {
      assessment: `${child_name} (${age} yrs, ${gender}) is <strong>severely underweight</strong> with a BMI of ${bmi}. This requires <strong>immediate nutritional intervention</strong> and medical consultation. The child needs intensive calorie and protein supplementation.`,
      foods: ['Eggs (daily)', 'Full-fat Milk', 'Peanuts & Groundnuts', 'Bananas', 'Dates', 'Chikki (jaggery + peanuts)', 'Dal with ghee', 'Rice with curd', 'Ragi porridge', 'Dry fruits'],
      avoid: ['Skipping meals', 'Watery diluted food', 'Excessive tea or coffee', 'Packaged junk food'],
      meals: {
        'Morning (6–7am)': 'Warm milk with banana or ragi porridge with jaggery',
        'Breakfast (8–9am)': 'Egg (boiled or scrambled) + 2 rotis with ghee + dal',
        'Mid-Morning (11am)': 'Handful of peanuts or dates or dry fruits',
        'Lunch (1pm)': 'Rice + dal + sabzi with oil/ghee + curd + one egg',
        'Evening (4pm)': 'Milk with chikki or banana with peanut butter',
        'Dinner (7pm)': 'Khichdi with ghee or roti + dal + vegetable curry',
      },
      tips: [
        'Offer 5–6 small meals daily instead of 3 large ones',
        'Add ghee, peanut butter or coconut oil to increase calorie density',
        'Consult an ICDS/health worker for therapeutic food supplements',
        'Weigh child every 2 weeks to track progress',
        'Ensure clean drinking water to prevent infection-related weight loss',
        'Refer to the nearest Primary Health Center for nutritional assessment',
      ],
      followup: 'Immediate follow-up required. Re-measure BMI in 2 weeks. Refer to PHC if no improvement.',
    },
    'Underweight': {
      assessment: `${child_name} (${age} yrs, ${gender}) is <strong>mildly underweight</strong> with a BMI of ${bmi}. Dietary intake needs improvement with increased calorie and protein-rich foods suited to Indian households.`,
      foods: ['Eggs', 'Milk & curd', 'Dal & legumes', 'Peanuts', 'Bananas', 'Sweet potato', 'Ragi', 'Green leafy vegetables', 'Seasonal fruits'],
      avoid: ['Processed snacks (chips, biscuits)', 'Sugary cold drinks', 'Excess spicy food that reduces appetite'],
      meals: {
        'Morning': 'Milk or ragi porridge with jaggery',
        'Breakfast': '2 idli/dosa with sambar + one banana',
        'Mid-Morning': 'Peanuts / roasted chana / fruit',
        'Lunch': 'Rice + dal + vegetable curry + curd',
        'Evening': 'Milk with banana or boiled egg',
        'Dinner': 'Roti + sabzi + dal or khichdi',
      },
      tips: [
        'Ensure 3 nutritious meals and 2 healthy snacks daily',
        'Add protein to every meal — egg, dal, milk, or curd',
        'Use whole grains — ragi, jowar, bajra are calorie-dense and nutritious',
        'Monitor weight monthly and report no-change to health worker',
        'Encourage physical activity appropriate for age',
      ],
      followup: 'Monitor closely. Re-measure BMI in 4 weeks.',
    },
    'Normal': {
      assessment: `${child_name} (${age} yrs, ${gender}) has a <strong>healthy BMI of ${bmi}</strong>. Continue the current balanced diet to maintain good nutritional status. Focus on variety and age-appropriate foods.`,
      foods: ['Milk & dairy', 'Eggs', 'Dal & legumes', 'Seasonal vegetables', 'Fruits (banana, guava, papaya)', 'Whole grains (rice, ragi, wheat)', 'Nuts in moderation'],
      avoid: ['Excess oily/fried foods', 'Sugary drinks and candy', 'Ultra-processed snacks'],
      meals: {
        'Morning': 'Milk / ragi porridge',
        'Breakfast': 'Idli / dosa / paratha with dal',
        'Mid-Morning': 'Fruit or nuts',
        'Lunch': 'Rice + dal + vegetables + curd',
        'Evening': 'Milk with fruit',
        'Dinner': 'Roti + sabzi + dal',
      },
      tips: [
        'Maintain current eating habits — they are working well',
        'Include iron-rich foods like spinach, dal, and jaggery',
        'Limit screen time and encourage 30 min outdoor play daily',
        'Regular 6-monthly health check-up is sufficient',
      ],
      followup: 'Routine monitoring. Re-measure BMI in 3 months.',
    },
    'Overweight': {
      assessment: `${child_name} (${age} yrs, ${gender}) is <strong>slightly overweight</strong> with a BMI of ${bmi}. Focus on reducing high-calorie dense foods and increasing physical activity. Avoid crash diets at this age.`,
      foods: ['Green vegetables (spinach, beans, lauki)', 'Fruits low in sugar (guava, apple, papaya)', 'Dal & legumes', 'Whole grains', 'Buttermilk/curd (low fat)'],
      avoid: ['Fried foods (pakoda, samosa, poori)', 'Sugary drinks and juices', 'Chocolates, biscuits, chips', 'Excess rice and maida products'],
      meals: {
        'Morning': 'Low-fat milk or buttermilk',
        'Breakfast': 'Oats porridge / daliya / idli with sambar (no excess oil)',
        'Mid-Morning': 'Fresh fruit (avoid banana, mango)',
        'Lunch': 'Less rice + more dal + lots of vegetables + curd',
        'Evening': 'Cucumber/carrot sticks or roasted chana',
        'Dinner': 'Light khichdi or 1–2 rotis with vegetable curry',
      },
      tips: [
        'Encourage 45 min of active play or outdoor games daily',
        'Do NOT restrict food completely — just replace junk with nutritious options',
        'Serve smaller portions on a smaller plate',
        'Limit TV time during mealtimes to prevent overeating',
        'Monthly weight monitoring recommended',
      ],
      followup: 'Monitor monthly. Consult if BMI continues to increase.',
    },
    'Obese': {
      assessment: `${child_name} (${age} yrs, ${gender}) is <strong>obese</strong> with a BMI of ${bmi}. This is a health concern. Immediate dietary changes combined with increased physical activity are essential. Medical consultation is recommended.`,
      foods: ['Steamed vegetables', 'Dal & beans', 'Low-fat curd', 'Whole grain rotis', 'Fruits with fibre (guava, apple, pear)', 'Buttermilk'],
      avoid: ['All fried foods', 'Full-fat sweets and mithai', 'Sugary drinks', 'White bread, maida', 'Chips and namkeen', 'Excess rice'],
      meals: {
        'Morning': 'Warm water with lemon / low-fat milk',
        'Breakfast': 'Daliya or moong dal cheela with green chutney (no oil)',
        'Mid-Morning': 'Apple or pear or guava',
        'Lunch': 'Small portion rice or 1 roti + lots of dal + green vegetables',
        'Evening': 'Roasted makhana / sprouts / cucumber',
        'Dinner': 'Vegetable soup + 1 roti or moong dal khichdi',
      },
      tips: [
        'Immediate medical referral recommended for full assessment',
        'Replace screen time with outdoor physical activity — minimum 1 hour',
        'No sugary drinks or processed snacks at all',
        'Weigh every 2 weeks and record progress',
        'Family dietary habits may need adjustment — involve parents',
        'Ensure adequate sleep — poor sleep worsens childhood obesity',
      ],
      followup: 'Urgent review in 2 weeks. Refer to PHC/pediatrician for assessment.',
    },
  };

  return data[category] || data['Normal'];
}

// ── AI RECOMMENDATION HTML RENDERER ──────────────────────────────
function buildAiRecHtml(rec, aiData) {
  const cfg = getBmiConfig(rec.category);

  const mealCards = Object.entries(aiData.meals).map(([lbl, val]) => `
    <div class="ai-meal-item">
      <div class="ai-meal-label">${lbl}</div>
      <div class="ai-meal-val">${val}</div>
    </div>`).join('');

  const foodItems = aiData.foods.map(f => `<li><i class="bi bi-check-circle-fill"></i> ${f}</li>`).join('');
  const avoidItems = aiData.avoid.map(f => `<li><i class="bi bi-x-circle-fill"></i> ${f}</li>`).join('');
  const tipItems = aiData.tips.map(t => `<li style="margin-bottom:8px"><i class="bi bi-lightbulb-fill" style="color:var(--yellow)"></i> &nbsp;${t}</li>`).join('');

  return `
    <div class="ai-rec-card">
      <div class="ai-rec-header">
        <div class="ai-badge"><i class="bi bi-robot"></i> AI Nutrition Engine</div>
        <div>
          <div class="ai-rec-title">${rec.child_name}</div>
          <div style="font-size:13px;color:var(--text-s);margin-top:2px">${rec.age} yrs · ${rec.gender} · BMI ${rec.bmi} · ${fmt(rec.date)}</div>
        </div>
        ${bmiTag(rec.category)}
      </div>

      <!-- BMI Visual Gauge -->
      <div style="background:var(--card);border-radius:14px;padding:20px;border:1px solid var(--border);margin-bottom:14px">
        <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap">
          <div class="bmi-gauge-circle" style="background:${cfg.bg};border-color:${cfg.color};width:110px;height:110px">
            <div class="bmi-gauge-num" style="color:${cfg.color};font-size:32px">${rec.bmi}</div>
            <div class="bmi-gauge-unit">BMI</div>
          </div>
          <div style="flex:1;min-width:200px">
            <div style="font-weight:800;font-size:16px;margin-bottom:10px;color:${cfg.color}">${cfg.icon} ${rec.category}</div>
            <div class="bmi-scale">
              <div class="bmi-scale-seg" style="background:#EF4444;flex:1.5"></div>
              <div class="bmi-scale-seg" style="background:#F59E0B;flex:2"></div>
              <div class="bmi-scale-seg" style="background:#10B981;flex:3"></div>
              <div class="bmi-scale-seg" style="background:#EAB308;flex:2"></div>
              <div class="bmi-scale-seg" style="background:#F97316;flex:1.5"></div>
            </div>
            <div class="bmi-scale-labels"><span>Severe &lt;14</span><span>Under 14–16</span><span>Normal 16–22</span><span>Over 22–26</span><span>&gt;26</span></div>
            <div style="margin-top:12px;font-size:13px;color:var(--text-m);line-height:1.6">
              <strong>Height:</strong> ${rec.height} cm &nbsp;&nbsp;
              <strong>Weight:</strong> ${rec.weight} kg &nbsp;&nbsp;
              <strong>Date:</strong> ${fmt(rec.date)}
            </div>
          </div>
        </div>
      </div>

      <!-- Assessment -->
      <div class="ai-section">
        <div class="ai-section-title"><i class="bi bi-clipboard2-pulse-fill"></i> Nutrition Assessment</div>
        <p class="ai-tip">${aiData.assessment}</p>
      </div>

      <!-- Recommended + Avoid -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px">
        <div class="ai-section" style="margin-bottom:0">
          <div class="ai-section-title" style="color:var(--green)"><i class="bi bi-check-circle-fill"></i> Recommended Foods</div>
          <ul class="ai-list">${foodItems}</ul>
        </div>
        <div class="ai-section" style="margin-bottom:0">
          <div class="ai-section-title" style="color:var(--red)"><i class="bi bi-x-circle-fill"></i> Foods to Avoid</div>
          <ul class="ai-list avoid">${avoidItems}</ul>
        </div>
      </div>

      <!-- Daily Meal Plan -->
      <div class="ai-section">
        <div class="ai-section-title"><i class="bi bi-calendar3"></i> Daily Meal Suggestions</div>
        <div class="ai-meal-grid">${mealCards}</div>
      </div>

      <!-- Health Tips -->
      <div class="ai-section">
        <div class="ai-section-title" style="color:var(--yellow)"><i class="bi bi-lightbulb-fill"></i> Health Tips</div>
        <ul style="list-style:none;padding:0;margin:0">${tipItems}</ul>
      </div>

      <!-- Follow-up -->
      <div class="ai-section" style="background:${cfg.bg};border-color:${cfg.color}30;margin-bottom:0">
        <div class="ai-section-title" style="color:${cfg.color}"><i class="bi bi-calendar-check-fill"></i> Follow-up Recommendation</div>
        <p class="ai-tip" style="color:var(--text-d);font-weight:700">${aiData.followup}</p>
      </div>
    </div>
  `;
}

// ── BMI PAGE RENDERER ─────────────────────────────────────────────
function renderBmiPage() {
  updateBmiBadge();
  switchBmiTab('records');

  // Populate child dropdowns
  const opts = '<option value="">Choose a child…</option>' + DB.children.map(c =>
    `<option value="${c.id}">${c.child_name} (${c.age} yrs, ${c.gender})</option>`).join('');
  const calcChild = document.getElementById('calc-child');
  const bmChildSel = document.getElementById('bm-child-sel');
  if (calcChild)  calcChild.innerHTML  = opts;
  if (bmChildSel) bmChildSel.innerHTML = '<option value="">— Enter manually below —</option>' +
    DB.children.map(c => `<option value="${c.id}">${c.child_name} (${c.age} yrs, ${c.gender})</option>`).join('');

  // Set today date on calc form
  const today = new Date().toISOString().split('T')[0];
  const calcDate = document.getElementById('calc-date');
  const bmDateIn = document.getElementById('bm-date-in');
  if (calcDate) calcDate.value = today;
  if (bmDateIn) bmDateIn.value = today;
}

function updateBmiBadge() {
  const crit = DB.bmiRecords.filter(r => r.category === 'Severe Underweight' || r.category === 'Underweight').length;
  const badge = document.getElementById('sb-bmi-badge');
  if (badge) { badge.textContent = crit > 0 ? crit : ''; }
}

function switchBmiTab(tab) {
  const tabs = ['records', 'calculator', 'critical', 'history'];
  tabs.forEach(t => {
    const el = document.getElementById('bmi-tab-' + t);
    if (el) el.style.display = t === tab ? '' : 'none';
  });
  document.querySelectorAll('#page-bmi .ptab').forEach((b, i) =>
    b.classList.toggle('active', tabs[i] === tab));

  if (tab === 'records')    renderBmiTable(DB.bmiRecords);
  if (tab === 'critical')   renderBmiCritical();
  if (tab === 'history')    renderBmiTrends();
}

// ── BMI STATS ─────────────────────────────────────────────────────
function renderBmiStats(records) {
  const r = records || DB.bmiRecords;
  const normal  = r.filter(x => x.category === 'Normal').length;
  const severe  = r.filter(x => x.category === 'Severe Underweight').length;
  const under   = r.filter(x => x.category === 'Underweight').length;
  const over    = r.filter(x => x.category === 'Overweight').length;
  const obese   = r.filter(x => x.category === 'Obese').length;
  const critical = severe + under;

  document.getElementById('bmi-stats').innerHTML = `
    <div class="scard"><div class="scard-icon bg-p"><i class="bi bi-people-fill col-p" style="font-size:24px"></i></div><div><div class="scard-val col-p">${r.length}</div><div class="scard-lbl">Total Records</div></div></div>
    <div class="scard"><div class="scard-icon bg-g"><i class="bi bi-check-circle-fill col-g" style="font-size:24px"></i></div><div><div class="scard-val col-g">${normal}</div><div class="scard-lbl">Normal BMI</div></div></div>
    <div class="scard"><div class="scard-icon bg-r"><i class="bi bi-exclamation-triangle-fill col-r" style="font-size:24px"></i></div><div><div class="scard-val col-r">${severe}</div><div class="scard-lbl">Severe Underweight</div></div></div>
    <div class="scard"><div class="scard-icon bg-y"><i class="bi bi-dash-circle-fill col-y" style="font-size:24px"></i></div><div><div class="scard-val col-y">${under}</div><div class="scard-lbl">Underweight</div></div></div>
    <div class="scard"><div class="scard-icon bg-o"><i class="bi bi-arrow-up-circle-fill col-o" style="font-size:24px"></i></div><div><div class="scard-val col-o">${over}</div><div class="scard-lbl">Overweight</div></div></div>
    <div class="scard"><div class="scard-icon bg-pk"><i class="bi bi-exclamation-circle-fill col-pk" style="font-size:24px"></i></div><div><div class="scard-val col-pk">${obese}</div><div class="scard-lbl">Obese</div></div></div>
  `;

  // Alert banner
  const alertArea = document.getElementById('bmi-alert-area');
  if (alertArea) {
    const critList = DB.bmiRecords.filter(r => r.category === 'Severe Underweight' || r.category === 'Underweight');
    alertArea.innerHTML = critList.length
      ? `<div class="bmi-alert-banner"><div class="bmi-alert-icon">⚠️</div><div><div class="bmi-alert-title">${critList.length} Children Require Immediate Nutrition Attention</div><div class="bmi-alert-kids">${critList.map(r => `<span class="bmi-tag bmi-${r.category === 'Severe Underweight' ? 'severe' : 'under'}" style="margin-right:6px;margin-top:4px;display:inline-flex">${r.child_name}</span>`).join('')}</div></div></div>`
      : '<div class="palert palert-ok"><i class="bi bi-check-circle-fill"></i> All children are within healthy BMI range.</div>';
  }
}

// ── BMI TABLE ────────────────────────────────────────────────────
function renderBmiTable(rows) {
  renderBmiStats(rows);
  document.getElementById('bmi-tbody').innerHTML = rows.length
    ? rows.map((r, i) => {
        const cfg = getBmiConfig(r.category);
        return `<tr>
          <td>${i + 1}</td>
          <td><strong>${r.child_name}</strong></td>
          <td>${r.age} yrs</td>
          <td><span class="tag ${r.gender === 'Male' ? 'tag-s' : 'tag-pk'}">${r.gender}</span></td>
          <td>${r.height} cm</td>
          <td>${r.weight} kg</td>
          <td><span class="bmi-num-cell" style="color:${cfg.color}">${r.bmi}</span></td>
          <td>${bmiTag(r.category)}</td>
          <td>
            <button class="tbl-btn tbl-btn-view" onclick="viewAiRec('${r.id}')" title="View AI Recommendation">
              <i class="bi bi-robot"></i>
            </button>
          </td>
          <td class="col-soft fs-13">${fmt(r.date)}</td>
          <td>
            <button class="tbl-btn tbl-btn-edit" onclick="editBmiRecord('${r.id}')" title="Edit"><i class="bi bi-pencil-fill"></i></button>
            <button class="tbl-btn tbl-btn-del"  onclick="deleteBmiRecord('${r.id}')" title="Delete"><i class="bi bi-trash-fill"></i></button>
          </td>
        </tr>`;
      }).join('')
    : '<tr><td colspan="11" class="text-center" style="padding:36px;color:var(--text-s)">No BMI records found. Add a record using the calculator or the Add BMI button.</td></tr>';
}

function searchBmiRecords(q) {
  renderBmiTable(DB.bmiRecords.filter(r => r.child_name.toLowerCase().includes(q.toLowerCase())));
}

function filterBmiRecords(cat) {
  renderBmiTable(cat ? DB.bmiRecords.filter(r => r.category === cat) : DB.bmiRecords);
}

// ── VIEW AI RECOMMENDATION MODAL ────────────────────────────────
function viewAiRec(id) {
  const rec = DB.bmiRecords.find(r => String(r.id) === String(id));
  if (!rec) return;

  // Generate AI data if not already cached
  if (!rec.ai_recommendation) {
    rec.ai_recommendation = generateAiRecommendation(rec);
  }

  const titleEl = document.getElementById('ai-modal-title');
  const bodyEl  = document.getElementById('ai-modal-body');
  if (titleEl) titleEl.innerHTML = `<i class="bi bi-robot"></i> ${rec.child_name} — AI Nutrition Report`;
  if (bodyEl)  bodyEl.innerHTML  = buildAiRecHtml(rec, rec.ai_recommendation);

  new bootstrap.Modal(document.getElementById('aiRecModal')).show();
}

function printAiRec() {
  window.print();
}

// ── BMI CALCULATOR (tab) ──────────────────────────────────────────
function autoFillCalc(childId) {
  if (!childId) return;
  const c = DB.children.find(x => String(x.id) === String(childId));
  if (!c) return;
  const nameEl   = document.getElementById('calc-name');
  const ageEl    = document.getElementById('calc-age');
  const genderEl = document.getElementById('calc-gender');
  if (nameEl)   nameEl.value   = c.child_name;
  if (ageEl)    ageEl.value    = c.age;
  if (genderEl) genderEl.value = c.gender;
}

function liveCalcBmi() {
  const h = parseFloat(document.getElementById('calc-height')?.value);
  const w = parseFloat(document.getElementById('calc-weight')?.value);
  const bmi = calcBmi(h, w);
  const wrap = document.getElementById('calc-live-preview');
  if (!wrap) return;
  if (bmi) {
    const cat = getBmiCategory(bmi);
    const cfg = getBmiConfig(cat);
    wrap.style.display = '';
    const prev = document.getElementById('calc-bmi-preview');
    const catPrev = document.getElementById('calc-cat-preview');
    if (prev) { prev.textContent = bmi; prev.style.color = cfg.color; }
    if (catPrev) { catPrev.textContent = `${cfg.icon} ${cat}`; catPrev.style.color = cfg.color; }
  } else {
    wrap.style.display = 'none';
  }
}

async function calculateAndSaveBmi() {
  const name   = document.getElementById('calc-name')?.value.trim();
  const age    = parseInt(document.getElementById('calc-age')?.value);
  const gender = document.getElementById('calc-gender')?.value;
  const height = parseFloat(document.getElementById('calc-height')?.value);
  const weight = parseFloat(document.getElementById('calc-weight')?.value);
  const date   = document.getElementById('calc-date')?.value || new Date().toISOString().split('T')[0];

  if (!name)   { toast('Enter child name', 'error'); return; }
  if (!age)    { toast('Enter valid age', 'error'); return; }
  if (!gender) { toast('Select gender', 'error'); return; }
  if (!height || height < 40)  { toast('Enter valid height (40–200 cm)', 'error'); return; }
  if (!weight || weight < 2)   { toast('Enter valid weight (2–80 kg)', 'error'); return; }

  const childRec = DB.children.find(c => c.child_name === name);
  const payload = {
    child_id: childRec?.id || null,
    child_name: name,
    age: age,
    gender: gender,
    height_cm: height,
    weight_kg: weight,
    measurement_date: date
  };

  const res = await apiFetch('/bmi', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (!res.success) {
    toast(res.message || 'Failed to save BMI record', 'error');
    return;
  }

  const newRec = res.data;
  toast(`✅ BMI calculated for ${name}: ${newRec.bmi_value} — ${newRec.bmi_category}`, 'success');

  // Refresh BMI data
  const fetchRes = await apiFetch('/bmi');
  if (fetchRes.success) {
    DB.bmiRecords = (fetchRes.data || []).map(normalizeBmi);
    updateBmiBadge();
  }

  // Clear form
  ['calc-name','calc-age','calc-height','calc-weight'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  const calcChild = document.getElementById('calc-child');
  const calcGender = document.getElementById('calc-gender');
  if (calcChild)  calcChild.value  = '';
  if (calcGender) calcGender.value = '';
  const calcPrev = document.getElementById('calc-live-preview');
  if (calcPrev) calcPrev.style.display = 'none';
}

// ── BMI MODAL (Add via modal) ─────────────────────────────────────
function openBmiModal(id) {
  editBmiId = id || null;
  ['bm-name-in','bm-age-in','bm-height-in','bm-weight-in'].forEach(x => {
    const el = document.getElementById(x); if (el) el.value = '';
  });
  const gEl = document.getElementById('bm-gender-in');
  if (gEl) gEl.value = '';
  const dateEl = document.getElementById('bm-date-in');
  if (dateEl) dateEl.value = new Date().toISOString().split('T')[0];
  const prevWrap = document.getElementById('bm-bmi-preview-wrap');
  if (prevWrap) prevWrap.style.display = 'none';

  if (id) {
    const rec = DB.bmiRecords.find(r => String(r.id) === String(id));
    if (rec) {
      document.getElementById('bm-name-in').value   = rec.child_name;
      document.getElementById('bm-age-in').value    = rec.age;
      document.getElementById('bm-gender-in').value = rec.gender;
      document.getElementById('bm-height-in').value = rec.height;
      document.getElementById('bm-weight-in').value = rec.weight;
      document.getElementById('bm-date-in').value   = rec.date;
      modalLiveBmi();
    }
  }

  // Populate child selector
  const sel = document.getElementById('bm-child-sel');
  if (sel) {
    sel.innerHTML = '<option value="">— Enter manually below —</option>' +
      DB.children.map(c => `<option value="${c.id}">${c.child_name} (${c.age} yrs, ${c.gender})</option>`).join('');
  }

  new bootstrap.Modal(document.getElementById('bmiModal')).show();
}

function editBmiRecord(id) { openBmiModal(id); }

function prefillBmiModal(childId) {
  if (!childId) return;
  const c = DB.children.find(x => String(x.id) === String(childId));
  if (!c) return;
  document.getElementById('bm-name-in').value   = c.child_name;
  document.getElementById('bm-age-in').value    = c.age;
  document.getElementById('bm-gender-in').value = c.gender;
}

function modalLiveBmi() {
  const h = parseFloat(document.getElementById('bm-height-in')?.value);
  const w = parseFloat(document.getElementById('bm-weight-in')?.value);
  const bmi = calcBmi(h, w);
  const wrap = document.getElementById('bm-bmi-preview-wrap');
  if (!wrap) return;
  if (bmi) {
    const cat = getBmiCategory(bmi);
    const cfg = getBmiConfig(cat);
    wrap.style.display = '';
    const prev = document.getElementById('bm-bmi-preview');
    const catPrev = document.getElementById('bm-cat-preview');
    if (prev) { prev.textContent = bmi; prev.style.color = cfg.color; }
    if (catPrev) { catPrev.textContent = `${cfg.icon} ${cat}`; catPrev.style.color = cfg.color; }
  } else {
    wrap.style.display = 'none';
  }
}

async function saveBmiRecord() {
  const name   = document.getElementById('bm-name-in')?.value.trim();
  const age    = parseInt(document.getElementById('bm-age-in')?.value);
  const gender = document.getElementById('bm-gender-in')?.value;
  const height = parseFloat(document.getElementById('bm-height-in')?.value);
  const weight = parseFloat(document.getElementById('bm-weight-in')?.value);
  const date   = document.getElementById('bm-date-in')?.value || new Date().toISOString().split('T')[0];

  if (!name)   { toast('Enter child name', 'error'); return; }
  if (!age)    { toast('Enter valid age', 'error'); return; }
  if (!gender) { toast('Select gender', 'error'); return; }
  if (!height || height < 40) { toast('Enter valid height', 'error'); return; }
  if (!weight || weight < 2)  { toast('Enter valid weight', 'error'); return; }

  const childRec = DB.children.find(c => c.child_name === name);
  const payload = {
    child_id: childRec?.id || null,
    child_name: name,
    age: age,
    gender: gender,
    height_cm: height,
    weight_kg: weight,
    measurement_date: date
  };

  if (editBmiId) {
    const res = await apiFetch(`/bmi/${editBmiId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    if (res.success) {
      toast(`✅ Updated BMI record for ${name}`, 'success');
    } else {
      toast(res.message || 'Failed to update BMI record', 'error');
      return;
    }
  } else {
    const res = await apiFetch('/bmi', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res.success) {
      toast(`✅ BMI record saved for ${name}`, 'success');
    } else {
      toast(res.message || 'Failed to save BMI record', 'error');
      return;
    }
  }

  bootstrap.Modal.getInstance(document.getElementById('bmiModal')).hide();
  
  // Refresh BMI data
  const fetchRes = await apiFetch('/bmi');
  if (fetchRes.success) {
    DB.bmiRecords = (fetchRes.data || []).map(normalizeBmi);
    updateBmiBadge();
    renderBmiTable(DB.bmiRecords);
  }
}

async function deleteBmiRecord(id) {
  const r = DB.bmiRecords.find(x => String(x.id) === String(id));
  if (!r) return;
  if (!confirm(`Delete BMI record for ${r.child_name}?`)) return;
  
  const res = await apiFetch(`/bmi/${id}`, { method: 'DELETE' });
  if (res.success) {
    toast('BMI record deleted.', 'info');
    const fetchRes = await apiFetch('/bmi');
    if (fetchRes.success) {
      DB.bmiRecords = (fetchRes.data || []).map(normalizeBmi);
      updateBmiBadge();
      renderBmiTable(DB.bmiRecords);
    }
  } else {
    toast(res.message || 'Failed to delete BMI record', 'error');
  }
}

// ── CRITICAL TAB ──────────────────────────────────────────────────
function renderBmiCritical() {
  const groups = {
    severe:  DB.bmiRecords.filter(r => r.category === 'Severe Underweight'),
    under:   DB.bmiRecords.filter(r => r.category === 'Underweight'),
    over:    DB.bmiRecords.filter(r => r.category === 'Overweight'),
    obese:   DB.bmiRecords.filter(r => r.category === 'Obese'),
  };

  const makeList = (arr, emptyMsg) => arr.length
    ? arr.map(r => {
        const cfg = getBmiConfig(r.category);
        return `<div class="bmi-tl-item">
          <div class="bmi-tl-dot" style="background:${cfg.dotBg};color:${cfg.dotCol}">${r.bmi}</div>
          <div class="bmi-tl-info">
            <div class="bmi-tl-name">${r.child_name}</div>
            <div class="bmi-tl-meta">${r.age} yrs · ${r.gender} · ${r.height}cm / ${r.weight}kg · ${fmt(r.date)}</div>
          </div>
          <button class="tbl-btn tbl-btn-view" onclick="viewAiRec('${r.id}')" title="AI Recommendation"><i class="bi bi-robot"></i></button>
        </div>`;
      }).join('')
    : `<div class="palert palert-ok"><i class="bi bi-check-circle-fill"></i> ${emptyMsg}</div>`;

  document.getElementById('bmi-critical-severe').innerHTML = makeList(groups.severe, 'No severely underweight children.');
  document.getElementById('bmi-critical-under').innerHTML  = makeList(groups.under,  'No underweight children.');
  document.getElementById('bmi-critical-over').innerHTML   = makeList(groups.over,   'No overweight children.');
  document.getElementById('bmi-critical-obese').innerHTML  = makeList(groups.obese,  'No obese children.');
}

// ── TRENDS TAB ────────────────────────────────────────────────────
function renderBmiTrends() {
  // Timeline
  const sorted = [...DB.bmiRecords].sort((a, b) => new Date(b.date) - new Date(a.date));
  document.getElementById('bmi-timeline').innerHTML = sorted.length
    ? sorted.map(r => {
        const cfg = getBmiConfig(r.category);
        return `<div class="bmi-tl-item">
          <div class="bmi-tl-dot" style="background:${cfg.dotBg};color:${cfg.dotCol}">${r.bmi}</div>
          <div class="bmi-tl-info">
            <div class="bmi-tl-name">${r.child_name} <span style="font-weight:600;color:var(--text-s)">${r.age} yrs · ${r.gender}</span></div>
            <div class="bmi-tl-meta"><strong>${r.height} cm</strong> / <strong>${r.weight} kg</strong> · ${fmt(r.date)}</div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
            ${bmiTag(r.category)}
            <button class="tbl-btn tbl-btn-view" onclick="viewAiRec('${r.id}')" style="width:auto;padding:4px 10px;font-size:12px;border-radius:8px"><i class="bi bi-robot"></i> AI</button>
          </div>
        </div>`;
      }).join('')
    : '<div class="palert palert-ok"><i class="bi bi-info-circle"></i> No records yet.</div>';

  // Distribution
  const total = DB.bmiRecords.length || 1;
  const cats  = ['Severe Underweight', 'Underweight', 'Normal', 'Overweight', 'Obese'];
  const colMap = { 'Severe Underweight': '#EF4444', 'Underweight': '#F59E0B', 'Normal': '#10B981', 'Overweight': '#EAB308', 'Obese': '#F97316' };
  document.getElementById('bmi-distribution').innerHTML = cats.map(cat => {
    const count = DB.bmiRecords.filter(r => r.category === cat).length;
    const pct = Math.round((count / total) * 100);
    const cfg = getBmiConfig(cat);
    return `<div class="rpt-row">
      <div class="rpt-label" style="min-width:150px">${cfg.icon} ${cat}</div>
      <div class="rpt-bar"><div class="pbar"><div class="pbar-fill" style="width:${pct}%;background:${colMap[cat]}"></div></div></div>
      <div class="rpt-val">${count}</div>
    </div>`;
  }).join('');
}

// ── BMI EXPORT ────────────────────────────────────────────────────
function exportBmiReport() {
  const u = DB.user || {};
  const lines = [
    '===== SMART ANGANWADI PORTAL — BMI & NUTRITION REPORT =====',
    `Center: ${u.center || ''}`,
    `Generated: ${new Date().toLocaleDateString('en-IN')}`,
    `Total Records: ${DB.bmiRecords.length}`,
    '',
    '--- BMI SUMMARY ---',
    `Normal:            ${DB.bmiRecords.filter(r => r.category === 'Normal').length}`,
    `Underweight:       ${DB.bmiRecords.filter(r => r.category === 'Underweight').length}`,
    `Severe Underweight:${DB.bmiRecords.filter(r => r.category === 'Severe Underweight').length}`,
    `Overweight:        ${DB.bmiRecords.filter(r => r.category === 'Overweight').length}`,
    `Obese:             ${DB.bmiRecords.filter(r => r.category === 'Obese').length}`,
    '',
    '--- INDIVIDUAL RECORDS ---',
    ...DB.bmiRecords.map(r =>
      `${r.child_name} | ${r.age}y | ${r.gender} | ${r.height}cm | ${r.weight}kg | BMI:${r.bmi} | ${r.category} | ${r.date}`
    ),
    '',
    '--- CHILDREN REQUIRING ATTENTION ---',
    ...DB.bmiRecords
      .filter(r => r.category === 'Severe Underweight' || r.category === 'Underweight')
      .map(r => `⚠️ ${r.child_name} (${r.category}) — BMI ${r.bmi}`),
  ];
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/plain' }));
  a.download = `bmi_report_${new Date().toISOString().slice(0, 10)}.txt`;
  a.click();
  toast('📥 BMI report exported!', 'success');
}

// ── ATTENDANCE REDIRECT FUNCTION ──────────────────────────────────
function exportAttendancePdf() {
  downloadBackendReport('attendance');
}

// ── VILLAGE SURVEY FUNCTIONS ──────────────────────────────────────
function renderSurveyPage() {
  switchSurveyTab('history');
  
  // Pre-fill Mandal and Village from user profile if available
  const u = DB.user || {};
  const villageIn = document.getElementById('vs-village-name');
  if (villageIn && !villageIn.value) {
    villageIn.value = u.village || '';
  }
  
  const yearIn = document.getElementById('vs-year');
  if (yearIn) {
    yearIn.value = new Date().getFullYear();
  }
  
  const monthIn = document.getElementById('vs-month');
  if (monthIn) {
    monthIn.value = '';
  }
}

function switchSurveyTab(tab) {
  const tabs = ['history', 'add', 'trends', 'villagers'];
  tabs.forEach(t => {
    const el = document.getElementById('survey-tab-' + t);
    if (el) el.style.display = t === tab ? '' : 'none';
  });
  
  document.querySelectorAll('#page-survey .ptab').forEach((b, i) => {
    b.classList.toggle('active', tabs[i] === tab);
  });

  if (tab === 'history') {
    renderSurveyTable(DB.villageSurveys);
  } else if (tab === 'trends') {
    renderSurveyTrends();
  } else if (tab === 'villagers') {
    renderVillagersTable();
  }
}

function renderSurveyTable(rows) {
  const tbody = document.getElementById('survey-tbody');
  if (!tbody) return;

  const surveyList = rows || DB.villageSurveys;
  if (surveyList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="padding:28px;color:var(--text-s)">No survey records found. Conduct a survey.</td></tr>`;
    return;
  }

  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];

  tbody.innerHTML = surveyList.map(r => {
    const monthText = r.survey_month ? months[parseInt(r.survey_month, 10) - 1] : 'Yearly';
    return `<tr>
      <td><strong>${r.village_name}</strong></td>
      <td>${r.survey_year}</td>
      <td><span class="tag tag-s">${monthText}</span></td>
      <td><strong>${r.total_population}</strong></td>
      <td>${r.total_families}</td>
      <td>${r.total_children}</td>
      <td><span class="tag tag-r">${r.pregnant_women}</span></td>
      <td><span class="tag tag-v">${r.lactating_mothers}</span></td>
      <td>
        <button class="tbl-btn tbl-btn-edit" onclick="editSurvey('${r.id}')" title="Edit"><i class="bi bi-pencil-fill"></i></button>
        <button class="tbl-btn tbl-btn-del"  onclick="deleteSurvey('${r.id}')" title="Delete"><i class="bi bi-trash-fill"></i></button>
      </td>
    </tr>`;
  }).join('');
}

function searchSurveys(q) {
  const filtered = DB.villageSurveys.filter(s => 
    s.village_name.toLowerCase().includes(q.toLowerCase())
  );
  renderSurveyTable(filtered);
}

function editSurvey(sid) {
  const s = DB.villageSurveys.find(r => String(r.id) === String(sid));
  if (!s) return;

  editSurveyId = s.id;
  document.getElementById('vs-village-name').value = s.village_name;
  document.getElementById('vs-year').value = s.survey_year;
  document.getElementById('vs-month').value = s.survey_month || '';
  document.getElementById('vs-population').value = s.total_population;
  document.getElementById('vs-families').value = s.total_families;
  document.getElementById('vs-children').value = s.total_children;
  document.getElementById('vs-pregnant').value = s.pregnant_women;
  document.getElementById('vs-lactating').value = s.lactating_mothers;

  const titleEl = document.getElementById('survey-form-title');
  if (titleEl) titleEl.innerHTML = `<i class="bi bi-pencil-fill"></i> Edit Survey Entry`;

  const cancelBtn = document.getElementById('btn-cancel-survey-edit');
  if (cancelBtn) cancelBtn.style.display = 'inline-block';

  switchSurveyTab('add');
}

function cancelSurveyEdit() {
  editSurveyId = null;
  
  const u = DB.user || {};
  document.getElementById('vs-village-name').value = u.village || '';
  document.getElementById('vs-year').value = new Date().getFullYear();
  document.getElementById('vs-month').value = '';
  ['vs-population', 'vs-families', 'vs-children', 'vs-pregnant', 'vs-lactating'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });

  const titleEl = document.getElementById('survey-form-title');
  if (titleEl) titleEl.innerHTML = `<i class="bi bi-plus-circle-fill"></i> Add New Survey Entry`;

  const cancelBtn = document.getElementById('btn-cancel-survey-edit');
  if (cancelBtn) cancelBtn.style.display = 'none';

  switchSurveyTab('history');
}

async function saveSurvey() {
  const village_name = document.getElementById('vs-village-name').value.trim();
  const survey_year = parseInt(document.getElementById('vs-year').value, 10);
  const survey_month_val = document.getElementById('vs-month').value;
  const survey_month = survey_month_val ? parseInt(survey_month_val, 10) : null;
  const total_population = parseInt(document.getElementById('vs-population').value, 10);
  const total_families = parseInt(document.getElementById('vs-families').value, 10);
  const total_children = parseInt(document.getElementById('vs-children').value, 10);
  const pregnant_women = parseInt(document.getElementById('vs-pregnant').value, 10);
  const lactating_mothers = parseInt(document.getElementById('vs-lactating').value, 10);

  if (!village_name) { toast('Enter village name', 'error'); return; }
  if (isNaN(survey_year) || survey_year < 2000) { toast('Enter a valid survey year', 'error'); return; }
  if (isNaN(total_population) || total_population < 0) { toast('Population must be a non-negative number', 'error'); return; }
  if (isNaN(total_families) || total_families < 0) { toast('Families count must be a non-negative number', 'error'); return; }
  if (isNaN(total_children) || total_children < 0) { toast('Children count must be a non-negative number', 'error'); return; }
  if (isNaN(pregnant_women) || pregnant_women < 0) { toast('Pregnant women count must be a non-negative number', 'error'); return; }
  if (isNaN(lactating_mothers) || lactating_mothers < 0) { toast('Lactating mothers count must be a non-negative number', 'error'); return; }

  const payload = {
    village_name,
    survey_year,
    survey_month,
    total_population,
    total_families,
    total_children,
    pregnant_women,
    lactating_mothers
  };

  let res;
  if (editSurveyId) {
    res = await apiFetch(`/village-surveys/${editSurveyId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  } else {
    res = await apiFetch('/village-surveys', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  if (res.success) {
    toast(editSurveyId ? '✅ Survey record updated successfully!' : '✅ Survey record saved successfully!', 'success');
    editSurveyId = null;
    cancelSurveyEdit();
    
    // Refresh surveys
    const fetchRes = await apiFetch('/village-surveys');
    if (fetchRes.success) {
      DB.villageSurveys = fetchRes.data || [];
      renderSurveyTable(DB.villageSurveys);
      if (document.getElementById('page-dashboard').classList.contains('active')) {
        renderDashboard();
      }
    }
  } else {
    toast(res.message || 'Failed to save survey record', 'error');
  }
}

async function deleteSurvey(sid) {
  const s = DB.villageSurveys.find(r => String(r.id) === String(sid));
  if (!s) return;
  if (!confirm(`Are you sure you want to delete the survey for ${s.village_name} (${s.survey_year}${s.survey_month ? '-' + s.survey_month : ''})?`)) return;

  const res = await apiFetch(`/village-surveys/${sid}`, {
    method: 'DELETE'
  });

  if (res.success) {
    toast('✅ Survey record deleted successfully', 'success');
    const fetchRes = await apiFetch('/village-surveys');
    if (fetchRes.success) {
      DB.villageSurveys = fetchRes.data || [];
      renderSurveyTable(DB.villageSurveys);
      if (document.getElementById('page-dashboard').classList.contains('active')) {
        renderDashboard();
      }
    }
  } else {
    toast(res.message || 'Failed to delete survey record', 'error');
  }
}

function renderSurveyTrends() {
  const sortedSurveys = [...DB.villageSurveys].sort((a, b) => {
    if (a.survey_year !== b.survey_year) {
      return a.survey_year - b.survey_year;
    }
    return (a.survey_month || 0) - (b.survey_month || 0);
  });

  const monthsShort = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const labels = sortedSurveys.map(s => {
    return s.survey_month ? `${monthsShort[s.survey_month - 1]} ${s.survey_year}` : `Yearly ${s.survey_year}`;
  });
  const pregnantData = sortedSurveys.map(s => s.pregnant_women || 0);
  const lactatingData = sortedSurveys.map(s => s.lactating_mothers || 0);

  const ctx1 = document.getElementById('surveyTrendsChart');
  if (trendsChartInstance) {
    trendsChartInstance.destroy();
    trendsChartInstance = null;
  }
  if (ctx1) {
    trendsChartInstance = new Chart(ctx1, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Pregnant Women',
            data: pregnantData,
            borderColor: '#EF4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderWidth: 3,
            tension: 0.3,
            fill: true
          },
          {
            label: 'Lactating Mothers',
            data: lactatingData,
            borderColor: '#EC4899',
            backgroundColor: 'rgba(236, 72, 153, 0.1)',
            borderWidth: 3,
            tension: 0.3,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(108, 99, 255, 0.08)'
            }
          },
          x: {
            grid: {
              color: 'rgba(108, 99, 255, 0.08)'
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
          }
        }
      }
    });
  }

  const ctx2 = document.getElementById('surveyRatioChart');
  if (ratioChartInstance) {
    ratioChartInstance.destroy();
    ratioChartInstance = null;
  }
  if (ctx2) {
    const latest = sortedSurveys.length > 0 ? sortedSurveys[sortedSurveys.length - 1] : null;
    const data = latest ? [
      latest.total_children || 0,
      latest.total_families || 0,
      latest.pregnant_women || 0,
      latest.lactating_mothers || 0
    ] : [0, 0, 0, 0];

    ratioChartInstance = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['Children', 'Families', 'Pregnant Women', 'Lactating Mothers'],
        datasets: [{
          label: latest ? `Latest Survey (${latest.survey_year}${latest.survey_month ? '-' + latest.survey_month : ''})` : 'No Data',
          data: data,
          backgroundColor: [
            '#6C63FF',
            '#10B981',
            '#EF4444',
            '#EC4899'
          ],
          borderWidth: 0,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(108, 99, 255, 0.08)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }
}

// ── VILLAGERS REGISTRY FUNCTIONS ──────────────────────────────────
function renderVillagersTable(rows) {
  const tbody = document.getElementById('villagers-tbody');
  if (!tbody) return;

  const list = rows || DB.villagers;
  if (!list || list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:28px;color:var(--text-s)">No villagers registered. Click 'Add Villager' to add.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(v => `
    <tr>
      <td><strong>${escapeHtml(v.name)}</strong></td>
      <td>${v.age}</td>
      <td><span class="tag ${v.gender === 'Male' ? 'tag-s' : 'tag-pk'}">${v.gender}</span></td>
      <td><span class="tag ${v.category === 'Child' ? 'tag-v' : v.category === 'Pregnant Woman' ? 'tag-r' : v.category === 'Lactating Mother' ? 'tag-pk' : 'tag-t'}" style="font-size:11px; padding:2px 8px; border-radius:4px; font-weight:500;">${v.category}</span></td>
      <td>${v.contact_number || '—'}</td>
      <td>${v.address ? escapeHtml(v.address) : '—'}</td>
      <td>
        <button class="tbl-btn tbl-btn-edit" onclick="openVillagerModal('${v.id}')" title="Edit"><i class="bi bi-pencil-fill"></i></button>
        <button class="tbl-btn tbl-btn-del" onclick="deleteVillager('${v.id}')" title="Delete"><i class="bi bi-trash-fill"></i></button>
      </td>
    </tr>
  `).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function filterVillagers(cat) {
  const q = document.getElementById('villager-search').value.toLowerCase();
  let filtered = DB.villagers;
  if (cat) {
    filtered = filtered.filter(v => v.category === cat);
  }
  if (q) {
    filtered = filtered.filter(v => 
      v.name.toLowerCase().includes(q) || 
      (v.address && v.address.toLowerCase().includes(q))
    );
  }
  renderVillagersTable(filtered);
}

function searchVillagers(q) {
  const cat = document.getElementById('villager-filter-category').value;
  let filtered = DB.villagers;
  if (cat) {
    filtered = filtered.filter(v => v.category === cat);
  }
  if (q) {
    const term = q.toLowerCase();
    filtered = filtered.filter(v => 
      v.name.toLowerCase().includes(term) || 
      (v.address && v.address.toLowerCase().includes(term))
    );
  }
  renderVillagersTable(filtered);
}

function openVillagerModal(vid) {
  editVillagerId = vid || null;
  const titleEl = document.getElementById('villager-modal-title');
  
  if (editVillagerId) {
    titleEl.innerHTML = `<i class="bi bi-pencil-square"></i> Edit Villager`;
    const v = DB.villagers.find(item => String(item.id) === String(editVillagerId));
    if (v) {
      document.getElementById('vm-name').value = v.name;
    }
  }
  
  const modal = document.getElementById('villagerModal');
  if (modal) new bootstrap.Modal(modal).show();
}


// ================================================================
//  VACCINATION & ALERTS MODULE
// ================================================================

// Master Render Entry Point
function renderVaccinationsPage() {
  // Fill child select dropdown in schedule card
  const childSelect = document.getElementById('vax-child-select');
  if (childSelect) {
    const origVal = childSelect.value;
    childSelect.innerHTML = '<option value="">-- Select Child --</option>';
    DB.children.forEach(c => {
      childSelect.innerHTML += `<option value="${c.id}">${c.child_name} (Age: ${c.age} Y)</option>`;
    });
    if (origVal) childSelect.value = origVal;
  }

  // Render list queue
  renderVaxQueue();
}

async function scheduleVaccination() {
  const child_id = document.getElementById('vax-child-select').value;
  const name = document.getElementById('vax-name-input').value.trim();
  const purpose = document.getElementById('vax-purpose-input').value.trim();
  const due = document.getElementById('vax-due-input').value;

  if (!child_id || !name || !due) {
    toast('⚠️ Please select a child, vaccine name, and due date.', 'error');
    return;
  }

  const res = await apiFetch('/vaccinations', {
    method: 'POST',
    body: JSON.stringify({
      child_id,
      vaccine_name: name,
      vaccine_purpose: purpose || 'Scheduled Immunization Alert',
      dose_number: 1,
      due_date: due,
      notes: ''
    })
  });

  if (res.success) {
    toast('✅ Immunization schedule saved successfully.', 'success');
    document.getElementById('vax-schedule-form').reset();
    
    // Sync DB and reload queue
    await loadInitialData();
    renderVaccinationsPage();
  } else {
    toast(`❌ Error: ${res.message}`, 'error');
  }
}

function renderVaxQueue() {
  const search = document.getElementById('vax-queue-search').value.toLowerCase();
  const tbody = document.getElementById('vax-queue-tbody');
  
  tbody.innerHTML = '';
  
  let list = DB.vaccinations || [];
  
  if (search) {
    list = list.filter(v => 
      v.vaccine_name.toLowerCase().includes(search) ||
      (v.children && v.children.child_name.toLowerCase().includes(search))
    );
  }

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 24px; color: var(--text-s)">No active schedules found.</td></tr>`;
    return;
  }

  list.forEach(v => {
    const child = v.children || {};
    tbody.innerHTML += `
      <tr>
        <td class="fw-bold">${child.child_name || 'N/A'}</td>
        <td>${v.vaccine_name}</td>
        <td><span class="badge bg-warning-subtle text-warning-emphasis">${fmt(v.due_date)}</span></td>
        <td>
          <div style="font-size:13px; font-weight:600">${child.parent_name || '—'}</div>
          <div style="font-size:11px;color:var(--text-s)">📞 ${child.parent_mobile || '—'}</div>
        </td>
        <td class="text-end text-nowrap">
          <button class="btn btn-sm btn-success" id="btn-notify-wa-${v.id}" onclick="sendVaxNotification('${v.id}', 'whatsapp')" title="Send WhatsApp Message">
            <i class="bi bi-whatsapp"></i> WhatsApp
          </button>
          <button class="btn btn-sm btn-primary ms-1" id="btn-notify-sms-${v.id}" onclick="sendVaxNotification('${v.id}', 'sms')" title="Send SMS Message">
            <i class="bi bi-chat-text"></i> SMS
          </button>
          <button class="btn btn-sm btn-outline-danger ms-1" onclick="deleteVaccinationRecord('${v.id}')" title="Delete Schedule">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  });
}

async function deleteVaccinationRecord(id) {
  if (!confirm('Are you sure you want to delete this vaccination schedule?')) return;
  
  const res = await apiFetch(`/vaccinations/${id}`, { method: 'DELETE' });
  if (res.success) {
    toast('✅ Schedule deleted successfully', 'success');
    await loadInitialData();
    renderVaccinationsPage();
  } else {
    toast(`❌ Failed to delete: ${res.message}`, 'error');
  }
}

async function sendVaxNotification(id, channel = 'whatsapp') {
  const targetBtnId = channel === 'whatsapp' ? `btn-notify-wa-${id}` : `btn-notify-sms-${id}`;
  const btn = document.getElementById(targetBtnId);
  const original = btn ? btn.innerHTML : '';
  if (btn) {
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>...';
    btn.disabled = true;
  }

  const res = await apiFetch(`/vaccinations/${id}/notify`, { method: 'POST' });
  
  if (btn) {
    btn.innerHTML = original;
    btn.disabled = false;
  }

  if (res.success) {
    toast('📣 Notification reminder pushed to parents.', 'success');
    await loadInitialData();
    
    if (res.data && res.data.message_body && res.data.parent_mobile) {
      let phone = res.data.parent_mobile.replace(/[^0-9]/g, '');
      if (phone.length === 10) {
        phone = "91" + phone; // Add default India country code if omitted
      }
      const text = encodeURIComponent(res.data.message_body);
      
      if (channel === 'whatsapp') {
        const waUrl = `https://api.whatsapp.com/send?phone=${phone}&text=${text}`;
        window.open(waUrl, '_blank');
      } else if (channel === 'sms') {
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
        const separator = isIOS ? '&' : '?';
        const smsUrl = `sms:${phone}${separator}body=${text}`;
        window.open(smsUrl, '_blank');
      }
    }
  } else {
    toast(`❌ Notification failed: ${res.message}`, 'error');
  }
}