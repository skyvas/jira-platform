// Orbit Enterprise Agile Application Logic

// ==================== GLOBAL STATE ====================
let currentUser = null;
let allProjects = [];
let currentProjectId = null;
let currentBoardColumns = [];
let allSprints = [];
let currentSprintId = 'ALL';
let allIssues = [];
let allUsers = [];
let allNotifications = [];
let activeNotifTab = 'all';
let activeIssueDetail = null;
let pendingCreateFiles = [];
let stagedCommentImages = [];
let lastUnreadNotificationCount = 0;
let draggedIssueId = null;
let newProjectColumns = [];
let existingBoardColumns = [];

// Default 5 Kanban Columns
const DEFAULT_COLUMNS = [
  { id: 'col-backlog', name: 'Backlog', status: 'BACKLOG', order_index: 0 },
  { id: 'col-todo', name: 'To Do', status: 'TODO', order_index: 1 },
  { id: 'col-progress', name: 'In Progress', status: 'IN_PROGRESS', order_index: 2 },
  { id: 'col-review', name: 'In Review', status: 'REVIEW', order_index: 3 },
  { id: 'col-done', name: 'Done', status: 'DONE', order_index: 4 }
];

// ==================== SVG ICONS HELPER ====================
function getSvgIcon(name, extraClass = 'svg-icon') {
  const icons = {
    bell: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>`,
    search: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`,
    user: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`,
    users: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`,
    calendar: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`,
    columns: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,
    plus: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>`,
    check: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
    paperclip: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>`,
    message: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`,
    logout: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>`,
    close: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
    play: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`,
    history: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`,
    flag: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>`,
    mention: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"></circle><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path></svg>`,
    trash: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`,
    up: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>`,
    down: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>`,
    userMinus: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="18" y1="11" x2="23" y2="11"></line></svg>`,
    edit: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`,
    shield: `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`
  };

  return icons[name] || '';
}

// ==================== LIFECYCLE & VIEW ROUTER ====================
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();

  const urlParams = new URLSearchParams(window.location.search);
  const autoUser = urlParams.get('auto_login');
  if (autoUser) {
    try {
      await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: autoUser, password: `${autoUser}123` })
      });
    } catch (e) {
      console.warn('Auto login failed:', e);
    }
  }

  await checkAuth();

  const modalParam = urlParams.get('modal');
  if (modalParam === 'create') {
    setTimeout(() => {
      const btn = document.getElementById('btn-create-issue');
      if (btn) btn.click();
    }, 700);
  } else if (modalParam === 'ticket') {
    setTimeout(async () => {
      if (allIssues && allIssues.length > 0) {
        await openIssueDetail(allIssues[0].id);
      } else {
        await openIssueDetail('iss-1');
      }
    }, 1000);
  }

  // Periodic notification check (every 8 seconds when authenticated)
  setInterval(() => {
    if (currentUser) loadNotifications();
  }, 8000);
});

function showView(viewName) {
  const loginView = document.getElementById('login-view');
  const logoutView = document.getElementById('logout-view');
  const appView = document.getElementById('app-view');

  loginView.style.display = 'none';
  logoutView.style.display = 'none';
  appView.style.display = 'none';

  if (viewName === 'login') {
    loginView.style.display = 'flex';
    document.getElementById('login-error-alert').style.display = 'none';
  } else if (viewName === 'logout') {
    logoutView.style.display = 'flex';
  } else if (viewName === 'app') {
    appView.style.display = 'flex';
  }
}

// ==================== AUTHENTICATION ====================
async function checkAuth() {
  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      currentUser = await res.json();
      showView('app');
      updateAuthUI();
      await initWorkspace();
    } else {
      // Unauthenticated -> Strictly show Login view. Never auto-login.
      currentUser = null;
      clearClientData();
      showView('login');
    }
  } catch (err) {
    console.warn('Auth verification check failed:', err);
    currentUser = null;
    clearClientData();
    showView('login');
  }
}

function clearClientData() {
  allIssues = [];
  allProjects = [];
  allSprints = [];
  allNotifications = [];
  currentProjectId = null;
  currentSprintId = 'ALL';
  const boardEl = document.getElementById('kanban-board');
  if (boardEl) boardEl.innerHTML = '';
}

function updateAuthUI() {
  const profileEl = document.getElementById('user-profile');
  const avatarEl = document.getElementById('user-avatar');
  const nameEl = document.getElementById('user-name');
  const roleBadgeEl = document.getElementById('user-role-badge');
  const manageUsersBtn = document.getElementById('btn-manage-users');
  const manageColsBtn = document.getElementById('btn-manage-columns');
  const newProjectBtn = document.getElementById('btn-new-project');
  const tabCreateSprint = document.getElementById('tab-sprints-create');

  if (currentUser) {
    profileEl.style.display = 'flex';
    avatarEl.src = currentUser.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUser.username}`;
    nameEl.textContent = currentUser.full_name || currentUser.username;
    roleBadgeEl.textContent = currentUser.role;
    roleBadgeEl.className = `role-badge role-${currentUser.role}`;

    const isAdmin = currentUser.role === 'ADMIN' ||
      (currentUser.role && currentUser.role.value === 'ADMIN') ||
      String(currentUser.role).toUpperCase() === 'ADMIN';

    if (manageUsersBtn) manageUsersBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    if (manageColsBtn) manageColsBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    if (newProjectBtn) newProjectBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    if (tabCreateSprint) tabCreateSprint.style.display = isAdmin ? 'block' : 'none';

    updateSprintBanner();
  } else {
    profileEl.style.display = 'none';
    if (manageUsersBtn) manageUsersBtn.style.display = 'none';
    if (manageColsBtn) manageColsBtn.style.display = 'none';
    if (newProjectBtn) newProjectBtn.style.display = 'none';
    if (tabCreateSprint) tabCreateSprint.style.display = 'none';
  }
}


async function handleLogin(username, password) {
  const errorAlert = document.getElementById('login-error-alert');
  const errorText = document.getElementById('login-error-text');
  errorAlert.style.display = 'none';

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok) {
      currentUser = await res.json();
      showView('app');
      updateAuthUI();
      await initWorkspace();
      showToast(`Welcome back, ${currentUser.full_name}!`, 'success');
    } else {
      const err = await res.json();
      errorText.textContent = err.detail || 'Invalid username or password';
      errorAlert.style.display = 'flex';
    }
  } catch (err) {
    console.error('Login request error:', err);
    errorText.textContent = 'Server connection error. Please try again.';
    errorAlert.style.display = 'flex';
  }
}

async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
  } catch (err) {
    console.warn('Logout endpoint error:', err);
  }

  // Clear all in-memory, local storage, session storage, and cookie data
  currentUser = null;
  clearClientData();
  try {
    localStorage.clear();
    sessionStorage.clear();
  } catch (e) {}

  // Expire cookies explicitly
  document.cookie = 'session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';

  // Navigate to dedicated post-logout view
  showView('logout');
}

// ==================== WORKSPACE INITIALIZATION ====================
async function initWorkspace() {
  await loadProjects();
  await loadUsers();
  await loadBoard();
  await loadNotifications();
}

// ==================== PROJECTS ====================
async function loadProjects() {
  try {
    const res = await fetch('/api/projects');
    if (!res.ok) return;
    allProjects = await res.json();

    const selectEl = document.getElementById('project-select');
    const issueProjSelect = document.getElementById('issue-project');
    selectEl.innerHTML = '';
    issueProjSelect.innerHTML = '';

    if (!currentProjectId && allProjects.length > 0) {
      currentProjectId = allProjects[0].id;
    }

    allProjects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.key}: ${p.name}`;
      if (p.id === currentProjectId) opt.selected = true;
      selectEl.appendChild(opt);

      const issueOpt = document.createElement('option');
      issueOpt.value = p.id;
      issueOpt.textContent = `${p.key}: ${p.name}`;
      if (p.id === currentProjectId) issueOpt.selected = true;
      issueProjSelect.appendChild(issueOpt);
    });
  } catch (err) {
    console.error('Failed to load projects:', err);
  }
}

// ==================== BOARD & COLUMNS ====================
async function loadBoard() {
  try {
    if (!currentProjectId) {
      if (allProjects.length > 0) currentProjectId = allProjects[0].id;
      else return;
    }

    const res = await fetch(`/api/board?project_id=${currentProjectId}`);
    if (res.status === 401) {
      currentUser = null;
      showView('login');
      return;
    }
    if (!res.ok) return;

    const data = await res.json();
    currentBoardColumns = (data.board && data.board.columns) ? data.board.columns : DEFAULT_COLUMNS;
    currentBoardColumns.sort((a, b) => (a.order_index || 0) - (b.order_index || 0));

    allIssues = data.issues || [];

    // Load Sprints for current project
    await loadSprints(currentProjectId);

    updateColumnFilterOptions();
    updateTagFilterOptions();
    renderBoard();
  } catch (err) {
    console.error('Failed to load board data:', err);
  }
}

function updateColumnFilterOptions() {
  const select = document.getElementById('status-filter');
  const issueStatusSelect = document.getElementById('issue-status');
  select.innerHTML = '<option value="ALL">All Columns</option>';
  issueStatusSelect.innerHTML = '';

  currentBoardColumns.forEach((col, idx) => {
    const opt = document.createElement('option');
    opt.value = col.status;
    opt.textContent = col.name;
    select.appendChild(opt);

    const issueOpt = document.createElement('option');
    issueOpt.value = col.status;
    issueOpt.textContent = col.name;
    if (idx === 1 || col.status === 'TODO') issueOpt.selected = true;
    issueStatusSelect.appendChild(issueOpt);
  });
}

// ==================== MULTIPLE SPRINTS ====================
async function loadSprints(projectId) {
  try {
    const res = await fetch(`/api/sprints?project_id=${projectId}`);
    if (!res.ok) return;
    allSprints = await res.json();

    const sprintSelect = document.getElementById('sprint-select');
    const issueSprintSelect = document.getElementById('issue-sprint');

    sprintSelect.innerHTML = '<option value="ALL">All Sprints & Backlog</option>';
    issueSprintSelect.innerHTML = '<option value="">No Sprint (Backlog)</option>';

    // Find active sprint
    const activeSprint = allSprints.find(s => s.state === 'ACTIVE');

    allSprints.forEach(s => {
      const stateLabel = s.state === 'ACTIVE' ? '🟢 Active' : (s.state === 'COMPLETED' ? '✓ Completed' : 'Planned');
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = `${s.name} (${stateLabel})`;
      if (s.id === currentSprintId) opt.selected = true;
      sprintSelect.appendChild(opt);

      const issueOpt = document.createElement('option');
      issueOpt.value = s.id;
      issueOpt.textContent = `${s.name} (${s.state})`;
      if (activeSprint && s.id === activeSprint.id) issueOpt.selected = true;
      issueSprintSelect.appendChild(issueOpt);
    });

    updateSprintBanner();
  } catch (err) {
    console.error('Failed to load sprints:', err);
  }
}

function updateSprintBanner() {
  const banner = document.getElementById('sprint-banner');
  const statePill = document.getElementById('banner-sprint-state');
  const titleEl = document.getElementById('banner-sprint-name');
  const goalEl = document.getElementById('banner-sprint-goal');
  const datesEl = document.getElementById('banner-sprint-dates');
  const statsEl = document.getElementById('banner-progress-stats');
  const percentEl = document.getElementById('banner-progress-percent');
  const fillEl = document.getElementById('banner-progress-fill');
  const completeBtn = document.getElementById('btn-banner-complete-sprint');
  const startBtn = document.getElementById('btn-banner-start-sprint');

  let targetSprint = null;
  if (currentSprintId && currentSprintId !== 'ALL') {
    targetSprint = allSprints.find(s => s.id === currentSprintId);
  } else {
    // Default to active sprint
    targetSprint = allSprints.find(s => s.state === 'ACTIVE') || (allSprints.length > 0 ? allSprints[0] : null);
  }

  if (!targetSprint) {
    banner.style.display = 'none';
    return;
  }

  banner.style.display = 'flex';
  statePill.textContent = targetSprint.state;
  statePill.className = `sprint-state-pill ${targetSprint.state}`;

  titleEl.textContent = targetSprint.name;
  goalEl.textContent = targetSprint.goal ? `“${targetSprint.goal}”` : 'No sprint goal specified';

  const datesText = (targetSprint.start_date || targetSprint.end_date)
    ? `${targetSprint.start_date || 'Start'} to ${targetSprint.end_date || 'End'}`
    : `${targetSprint.duration_weeks || 2} Weeks`;
  datesEl.textContent = datesText;

  // Calculate metrics for this sprint
  const sprintIssues = allIssues.filter(i => i.sprint_id === targetSprint.id);
  const doneCount = sprintIssues.filter(i => String(i.status).toUpperCase() === 'DONE').length;
  const totalCount = sprintIssues.length;
  const percent = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  statsEl.textContent = `${doneCount} of ${totalCount} Done`;
  percentEl.textContent = `${percent}%`;
  fillEl.style.width = `${percent}%`;

  const isAdmin = currentUser && (
    currentUser.role === 'ADMIN' ||
    (currentUser.role && currentUser.role.value === 'ADMIN') ||
    String(currentUser.role).toUpperCase() === 'ADMIN'
  );

  const bannerNewSprintBtn = document.getElementById('btn-banner-new-sprint');
  if (bannerNewSprintBtn) {
    bannerNewSprintBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    bannerNewSprintBtn.onclick = () => {
      openSprintManagementModal();
      const tabCreate = document.getElementById('tab-sprints-create');
      if (tabCreate) tabCreate.click();
    };
  }

  if (targetSprint.state === 'ACTIVE') {
    completeBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    completeBtn.onclick = () => openCompleteSprintModal(targetSprint);
    startBtn.style.display = 'none';
  } else if (targetSprint.state === 'PLANNED') {
    completeBtn.style.display = 'none';
    startBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    startBtn.onclick = () => handleStartSprint(targetSprint.id);
  } else {
    completeBtn.style.display = 'none';
    startBtn.style.display = 'none';
  }
}


async function handleStartSprint(sprintId) {
  try {
    const res = await fetch(`/api/sprints/${sprintId}/start`, { method: 'POST' });
    if (res.ok) {
      showToast('Sprint started successfully!', 'success');
      await loadSprints(currentProjectId);
      renderBoard();
    } else {
      const err = await res.json();
      showToast(`Error: ${err.detail || 'Could not start sprint'}`, 'error');
    }
  } catch (err) {
    console.error('Error starting sprint:', err);
  }
}

function openCompleteSprintModal(sprint) {
  const modal = document.getElementById('complete-sprint-modal');
  document.getElementById('complete-sprint-name-display').textContent = sprint.name;

  const sprintIssues = allIssues.filter(i => i.sprint_id === sprint.id);
  const doneCount = sprintIssues.filter(i => String(i.status).toUpperCase() === 'DONE').length;
  const incompleteCount = sprintIssues.length - doneCount;

  document.getElementById('complete-stat-done').textContent = doneCount;
  document.getElementById('complete-stat-incomplete').textContent = incompleteCount;

  const confirmBtn = document.getElementById('btn-confirm-complete-sprint');
  confirmBtn.onclick = async () => {
    const dest = document.getElementById('incomplete-issues-destination').value;
    try {
      const res = await fetch(`/api/sprints/${sprint.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ move_incomplete_to: dest })
      });
      if (res.ok) {
        modal.style.display = 'none';
        showToast(`Sprint "${sprint.name}" completed!`, 'success');
        await loadBoard();
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Failed to complete sprint'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to complete sprint:', err);
    }
  };

  modal.style.display = 'flex';
}

function openSprintManagementModal() {
  const modal = document.getElementById('sprint-mgmt-modal');
  renderSprintsList();
  modal.style.display = 'flex';
}

function renderSprintsList() {
  const container = document.getElementById('sprints-list-container');
  container.innerHTML = '';

  if (allSprints.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); padding: 24px; text-align: center;">No sprints created yet for this project.</div>';
    return;
  }

  const isAdmin = currentUser && (
    currentUser.role === 'ADMIN' ||
    (currentUser.role && currentUser.role.value === 'ADMIN') ||
    String(currentUser.role).toUpperCase() === 'ADMIN'
  );

  allSprints.forEach(s => {
    const card = document.createElement('div');
    card.className = 'sprint-item-card';

    const sprintIssues = allIssues.filter(i => i.sprint_id === s.id);
    const doneCount = sprintIssues.filter(i => String(i.status).toUpperCase() === 'DONE').length;

    card.innerHTML = `
      <div class="sprint-card-info">
        <div class="sprint-card-header">
          <span class="sprint-state-pill ${s.state}">${s.state}</span>
          <span class="sprint-card-name">${escapeHtml(s.name)}</span>
        </div>
        <div class="sprint-card-goal">${s.goal ? escapeHtml(s.goal) : 'No goal'}</div>
        <div class="sprint-card-meta">
          <span>${s.start_date || 'TBD'} to ${s.end_date || 'TBD'}</span> •
          <span>${sprintIssues.length} issues (${doneCount} done)</span>
        </div>
      </div>
      <div class="sprint-card-actions">
        ${isAdmin && s.state === 'PLANNED' ? `
          <button class="btn btn-xs btn-primary btn-start-sprint-action" data-id="${s.id}">Start Sprint</button>
        ` : ''}
        ${isAdmin && s.state === 'ACTIVE' ? `
          <button class="btn btn-xs btn-outline btn-complete-sprint-action" data-id="${s.id}">Complete</button>
        ` : ''}
      </div>
    `;

    const startBtn = card.querySelector('.btn-start-sprint-action');
    if (startBtn) {
      startBtn.onclick = async () => {
        await handleStartSprint(s.id);
        renderSprintsList();
      };
    }

    const compBtn = card.querySelector('.btn-complete-sprint-action');
    if (compBtn) {
      compBtn.onclick = () => openCompleteSprintModal(s);
    }

    container.appendChild(card);
  });
}

async function renderSprintHistory() {
  const container = document.getElementById('sprint-history-container');
  container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted);">Loading historical sprints...</div>';

  try {
    const res = await fetch(`/api/sprints/history?project_id=${currentProjectId}`);
    if (!res.ok) return;
    const history = await res.json();
    container.innerHTML = '';

    if (history.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--text-muted);">No completed sprints in history yet. Complete an active sprint to see historical records here.</div>';
      return;
    }

    history.forEach(item => {
      const s = item.sprint;
      const card = document.createElement('div');
      card.className = 'history-card';
      const completedDate = s.completed_at ? new Date(s.completed_at).toLocaleDateString() : 'Completed';

      card.innerHTML = `
        <div class="history-card-top">
          <span class="history-title">${escapeHtml(s.name)}</span>
          <span class="history-date">Completed on ${completedDate}</span>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); font-style: italic;">
          ${s.goal ? escapeHtml(s.goal) : 'No goal documented'}
        </div>
        <div class="history-stats-bar">
          <span class="stat-pill success">${getSvgIcon('check', 'svg-icon-xs')} ${item.completed_count} Issues Completed</span>
          <span class="stat-pill warning">${item.incomplete_count} Carried Over</span>
          <span>Velocity: <strong>${item.completion_percentage}%</strong></span>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error('Failed to load sprint history:', err);
    container.innerHTML = '<div style="padding: 20px; text-align: center; color: #f87171;">Failed to load sprint history.</div>';
  }
}

// ==================== KANBAN BOARD RENDERING ====================
function renderBoard() {
  const boardEl = document.getElementById('kanban-board');
  boardEl.innerHTML = '';

  const searchVal = document.getElementById('search-input').value.toLowerCase().trim();
  const tagVal = document.getElementById('tag-filter').value;
  const statusVal = document.getElementById('status-filter').value;
  const assigneeVal = document.getElementById('assignee-filter').value;
  const roleVal = document.getElementById('role-filter').value;
  const priorityVal = document.getElementById('priority-filter').value;

  const isFiltered = (
    searchVal !== '' ||
    tagVal !== 'ALL' ||
    statusVal !== 'ALL' ||
    assigneeVal !== 'ALL' ||
    roleVal !== 'ALL' ||
    priorityVal !== 'ALL' ||
    currentSprintId !== 'ALL'
  );

  document.getElementById('btn-reset-filters').style.display = isFiltered ? 'inline-flex' : 'none';

  // Build user role map
  const userRoleMap = {};
  allUsers.forEach(u => { userRoleMap[u.username.toLowerCase()] = u.role; });

  const filtered = allIssues.filter(issue => {
    // Sprint filter
    if (currentSprintId && currentSprintId !== 'ALL') {
      if (issue.sprint_id !== currentSprintId) return false;
    }

    // Search filter
    if (searchVal) {
      const matchKey = issue.key.toLowerCase().includes(searchVal);
      const matchTitle = issue.title.toLowerCase().includes(searchVal);
      const matchDesc = (issue.description || '').toLowerCase().includes(searchVal);
      const matchAssignee = (issue.assignee || '').toLowerCase().includes(searchVal);
      const matchTags = (issue.tags || []).some(t => t.toLowerCase().includes(searchVal));
      if (!matchKey && !matchTitle && !matchDesc && !matchAssignee && !matchTags) return false;
    }

    // Tag filter
    if (tagVal !== 'ALL') {
      if (!(issue.tags || []).includes(tagVal)) return false;
    }

    // Column status filter
    if (statusVal !== 'ALL') {
      if (String(issue.status).toUpperCase() !== statusVal.toUpperCase()) return false;
    }

    // Assignee filter
    if (assigneeVal !== 'ALL') {
      if (assigneeVal === 'UNASSIGNED') {
        if (issue.assignee) return false;
      } else {
        if (!issue.assignee || issue.assignee.toLowerCase() !== assigneeVal.toLowerCase()) return false;
      }
    }

    // User Role filter
    if (roleVal !== 'ALL') {
      if (!issue.assignee) return false;
      const role = userRoleMap[issue.assignee.toLowerCase()];
      if (role !== roleVal) return false;
    }

    // Priority filter
    if (priorityVal !== 'ALL') {
      if (issue.priority !== priorityVal) return false;
    }

    return true;
  });

  document.getElementById('total-issues-count').textContent = filtered.length;

  // Render Columns dynamically based on project's configured column lanes
  currentBoardColumns.forEach(col => {
    const colStatusNorm = String(col.status).toUpperCase();
    const colIssues = filtered.filter(i => String(i.status).toUpperCase() === colStatusNorm);

    const colEl = document.createElement('div');
    colEl.className = 'kanban-column';
    colEl.innerHTML = `
      <div class="column-header">
        <span class="column-title">${escapeHtml(col.name)}</span>
        <span class="column-count">${colIssues.length}</span>
      </div>
      <div class="cards-container" data-status="${col.status}"></div>
    `;

    const container = colEl.querySelector('.cards-container');
    setupDragDropContainer(container, col.status);

    colIssues.forEach(issue => {
      const card = createCardElement(issue);
      container.appendChild(card);
    });

    boardEl.appendChild(colEl);
  });
}

function createCardElement(issue) {
  const card = document.createElement('div');
  card.className = 'issue-card';
  card.draggable = true;
  card.dataset.id = issue.id;

  // Tags HTML
  let tagsHtml = '';
  if (issue.tags && issue.tags.length > 0) {
    tagsHtml = '<div class="card-tags">' +
      issue.tags.map(t => `<span class="tag-chip">${escapeHtml(t)}</span>`).join('') +
      '</div>';
  }

  // Attachment Thumbnail Preview
  let thumbHtml = '';
  if (issue.attachments && issue.attachments.length > 0) {
    const firstImg = issue.attachments[0];
    thumbHtml = `
      <div class="card-thumb-preview">
        <img src="${firstImg.file_url}" alt="${escapeHtml(firstImg.filename)}" loading="lazy">
      </div>
    `;
  }

  // PROMINENT ASSIGNEE PILL
  let assigneeHtml = '';
  if (issue.assignee && issue.assignee.trim()) {
    const cleanUser = issue.assignee.toLowerCase().trim().replace(/^@/, '');
    const userObj = allUsers.find(u => u.username.toLowerCase() === cleanUser);
    const displayName = userObj ? userObj.full_name : issue.assignee;
    const avatarUrl = (userObj && userObj.avatar_url)
      ? userObj.avatar_url
      : `https://api.dicebear.com/7.x/avataaars/svg?seed=${cleanUser}`;

    assigneeHtml = `
      <div class="card-assignee-pill" title="Assigned to ${escapeHtml(displayName)}">
        <img src="${avatarUrl}" class="card-assignee-avatar" alt="Avatar">
        <span class="card-assignee-name">${escapeHtml(displayName)}</span>
      </div>
    `;
  } else {
    assigneeHtml = `
      <div class="card-assignee-pill unassigned" title="Click to assign a team member">
        ${getSvgIcon('user', 'svg-icon-xs')}
        <span class="card-assignee-name">Unassigned</span>
      </div>
    `;
  }

  const commentCount = (issue.comments || []).length;
  const attachCount = (issue.attachments || []).length;

  card.innerHTML = `
    <div class="card-top">
      <span class="issue-key">${issue.key}</span>
      <span class="priority-badge priority-${issue.priority}">${issue.priority}</span>
    </div>
    <div class="card-title">${escapeHtml(issue.title)}</div>
    ${tagsHtml}
    ${thumbHtml}
    <div class="card-bottom">
      ${assigneeHtml}
      <div class="card-meta-badges">
        ${attachCount > 0 ? `<span class="meta-icon-item">${getSvgIcon('paperclip', 'svg-icon-xs')} ${attachCount}</span>` : ''}
        <span class="meta-icon-item">${getSvgIcon('message', 'svg-icon-xs')} ${commentCount}</span>
      </div>
    </div>
  `;

  // Click card to open Issue Detail Modal
  card.addEventListener('click', () => {
    openIssueDetail(issue.id);
  });

  // Drag & drop handlers
  card.addEventListener('dragstart', (e) => {
    draggedIssueId = issue.id;
    card.classList.add('dragging');
    e.dataTransfer.setData('text/plain', issue.id);
  });

  card.addEventListener('dragend', () => {
    card.classList.remove('dragging');
    draggedIssueId = null;
  });

  return card;
}

function setupDragDropContainer(container, targetStatus) {
  container.addEventListener('dragover', (e) => {
    e.preventDefault();
    container.classList.add('drag-over');
  });

  container.addEventListener('dragleave', () => {
    container.classList.remove('drag-over');
  });

  container.addEventListener('drop', async (e) => {
    e.preventDefault();
    container.classList.remove('drag-over');
    const issueId = e.dataTransfer.getData('text/plain');
    if (!issueId) return;

    const issue = allIssues.find(i => i.id === issueId);
    if (!issue || String(issue.status).toUpperCase() === String(targetStatus).toUpperCase()) return;

    try {
      const res = await fetch(`/api/issues/${issueId}/move`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: targetStatus })
      });

      if (!res.ok) {
        const errorData = await res.json();
        showToast(`Workflow Guard: ${errorData.detail || 'Forbidden state transition'}`, 'error');
        return;
      }

      const updated = await res.json();
      const idx = allIssues.findIndex(i => i.id === issueId);
      if (idx !== -1) allIssues[idx] = updated;
      renderBoard();
      updateSprintBanner();
      loadNotifications();
    } catch (err) {
      console.error('Failed to move issue:', err);
    }
  });
}

// ==================== ISSUE DETAIL MODAL ====================
async function openIssueDetail(issueId) {
  try {
    const res = await fetch(`/api/issues/${issueId}`);
    if (!res.ok) return;
    activeIssueDetail = await res.json();

    // Reset staged comment images and composer inputs
    stagedCommentImages = [];
    renderStagedCommentImages();
    const commentInput = document.getElementById('comment-input');
    if (commentInput) commentInput.value = '';
    const detailFileInput = document.getElementById('detail-upload-file');
    if (detailFileInput) detailFileInput.value = '';

    renderIssueDetailModal();
    document.getElementById('issue-detail-modal').style.display = 'flex';
  } catch (err) {
    console.error('Failed to load issue detail:', err);
  }
}

function renderIssueDetailModal() {
  if (!activeIssueDetail) return;
  const issue = activeIssueDetail;

  document.getElementById('detail-issue-key').textContent = issue.key;
  const priorityBadge = document.getElementById('detail-priority-badge');
  priorityBadge.textContent = issue.priority;
  priorityBadge.className = `priority-badge priority-${issue.priority}`;

  document.getElementById('detail-status-badge').textContent = issue.status;
  document.getElementById('detail-title-input').value = issue.title;
  document.getElementById('detail-desc-input').value = issue.description || '';
  document.getElementById('detail-priority-select').value = issue.priority;
  document.getElementById('detail-assignee-select').value = issue.assignee || '';
  const sprintObj = allSprints.find(s => s.id === issue.sprint_id);
  const sprintNameEl = document.getElementById('detail-sprint-name');
  if (sprintNameEl) {
    sprintNameEl.textContent = sprintObj ? sprintObj.name : 'No Sprint (Backlog)';
  }
  document.getElementById('detail-save-msg').textContent = '';

  // Update Prominent Assignee Spotlight in Ticket Detail
  updateAssigneeSpotlightUI(issue.assignee);

  renderDetailTags();
  renderDetailAttachments();
  renderDetailComments();
}

function updateAssigneeSpotlightUI(assigneeUsername) {
  const avatarEl = document.getElementById('spotlight-avatar');
  const nameEl = document.getElementById('spotlight-name');

  if (assigneeUsername && assigneeUsername.trim()) {
    const cleanUser = assigneeUsername.toLowerCase().trim().replace(/^@/, '');
    const userObj = allUsers.find(u => u.username.toLowerCase() === cleanUser);
    const displayName = userObj ? userObj.full_name : assigneeUsername;
    const avatarUrl = (userObj && userObj.avatar_url)
      ? userObj.avatar_url
      : `https://api.dicebear.com/7.x/avataaars/svg?seed=${cleanUser}`;

    avatarEl.src = avatarUrl;
    nameEl.textContent = displayName;
  } else {
    avatarEl.src = 'https://api.dicebear.com/7.x/avataaars/svg?seed=unassigned';
    nameEl.textContent = 'Unassigned';
  }
}

function renderDetailTags() {
  const container = document.getElementById('detail-tags-display');
  container.innerHTML = '';
  const tags = activeIssueDetail.tags || [];

  tags.forEach((tag, idx) => {
    const pill = document.createElement('span');
    pill.className = 'tag-pill';
    pill.innerHTML = `
      <span>${escapeHtml(tag)}</span>
      <button type="button" class="tag-remove-btn" data-idx="${idx}">&times;</button>
    `;
    pill.querySelector('.tag-remove-btn').addEventListener('click', () => {
      activeIssueDetail.tags.splice(idx, 1);
      renderDetailTags();
    });
    container.appendChild(pill);
  });
}

function renderDetailAttachments() {
  const grid = document.getElementById('detail-attachments-grid');
  const countEl = document.getElementById('detail-attachment-count');
  const attachments = activeIssueDetail.attachments || [];
  countEl.textContent = attachments.length;
  grid.innerHTML = '';

  if (attachments.length === 0) {
    grid.innerHTML = '<span style="font-size: 12px; color: var(--text-muted);">No attachments uploaded yet.</span>';
    return;
  }

  attachments.forEach(att => {
    const card = document.createElement('div');
    card.className = 'attachment-card';
    card.innerHTML = `
      <img src="${att.file_url}" alt="${escapeHtml(att.filename)}" class="attachment-thumb">
      <button class="attachment-del-btn" title="Delete Attachment" data-id="${att.id}">&times;</button>
      <div class="attachment-name" title="${escapeHtml(att.filename)}">${escapeHtml(att.filename)}</div>
    `;

    card.querySelector('.attachment-thumb').addEventListener('click', () => {
      openLightbox(att.file_url, `${att.filename} • Uploaded by @${att.uploaded_by}`, att.filename);
    });

    card.querySelector('.attachment-del-btn').addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        const res = await fetch(`/api/issues/${activeIssueDetail.id}/attachments/${att.id}`, { method: 'DELETE' });
        if (res.ok) {
          activeIssueDetail.attachments = activeIssueDetail.attachments.filter(a => a.id !== att.id);
          renderDetailAttachments();
          syncIssueInList(activeIssueDetail);
          showToast(`Attachment "${att.filename}" removed`, 'info');
        }
      } catch (err) {
        console.error('Failed to delete attachment:', err);
      }
    });

    grid.appendChild(card);
  });
}

function renderDetailComments() {
  const stream = document.getElementById('detail-comments-stream');
  const countEl = document.getElementById('detail-comments-count');
  const comments = activeIssueDetail.comments || [];
  countEl.textContent = `${comments.length} comment${comments.length === 1 ? '' : 's'}`;
  stream.innerHTML = '';

  if (comments.length === 0) {
    stream.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; padding: 20px 0; text-align: center;">No comments yet. Start the discussion below!</div>';
    return;
  }

  comments.forEach(c => {
    const bubble = document.createElement('div');
    bubble.className = 'comment-bubble';
    const formattedContent = highlightMentions(escapeHtml(c.content));
    const timeAgo = formatTimeAgo(c.created_at);

    let imagesHtml = '';
    if (c.images && c.images.length > 0) {
      imagesHtml = `<div class="comment-images-grid">` +
        c.images.map(imgUrl => `
          <div class="comment-img-card" data-url="${imgUrl}" title="Click to view full image">
            <div class="comment-img-badge">
              <svg class="svg-icon-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
              <span>Image</span>
            </div>
            <img src="${imgUrl}" alt="Comment image attachment" class="comment-img-thumb" loading="lazy">
          </div>
        `).join('') +
        `</div>`;
    }

    bubble.innerHTML = `
      <div class="comment-author-row">
        <span class="comment-author-name">${escapeHtml(c.author_name || c.author_username)}</span>
        <span class="role-badge role-${c.author_role || 'MEMBER'}">${c.author_role || 'MEMBER'}</span>
        <span class="comment-time">${timeAgo}</span>
      </div>
      <div class="comment-text">${formattedContent}</div>
      ${imagesHtml}
    `;

    bubble.querySelectorAll('.comment-img-card').forEach(card => {
      card.addEventListener('click', () => {
        openLightbox(card.dataset.url, 'Comment image attachment');
      });
    });

    stream.appendChild(bubble);
  });

  stream.scrollTop = stream.scrollHeight;
}

function highlightMentions(text) {
  return text.replace(/@([a-zA-Z0-9_-]+)/g, '<span class="mention-pill">@$1</span>');
}

function insertMention(username) {
  const textarea = document.getElementById('comment-input');
  textarea.value += ` @${username} `;
  textarea.focus();
}

function renderStagedCommentImages() {
  const stagingEl = document.getElementById('comment-img-staging');
  if (!stagingEl) return;
  stagingEl.innerHTML = '';
  if (stagedCommentImages.length === 0) {
    stagingEl.style.display = 'none';
    return;
  }
  stagingEl.style.display = 'flex';
  stagedCommentImages.forEach((imgUrl, idx) => {
    const chip = document.createElement('div');
    chip.className = 'staged-thumb-chip';
    chip.innerHTML = `
      <img src="${imgUrl}" alt="Staged image">
      <button type="button" class="staged-thumb-remove" data-idx="${idx}">&times;</button>
    `;
    chip.querySelector('.staged-thumb-remove').onclick = () => {
      stagedCommentImages.splice(idx, 1);
      renderStagedCommentImages();
    };
    stagingEl.appendChild(chip);
  });
}

let currentLightboxUrl = '';
let currentLightboxFilename = '';

function openLightbox(url, caption, filename) {
  const modal = document.getElementById('lightbox-modal');
  currentLightboxUrl = url;

  let cleanName = filename;
  if (!cleanName && url) {
    const rawName = url.split('/').pop().split('?')[0] || 'attachment.png';
    cleanName = rawName.includes('_') ? rawName.substring(rawName.indexOf('_') + 1) : rawName;
  }
  currentLightboxFilename = cleanName || 'attachment.png';

  document.getElementById('lightbox-img').src = url;
  document.getElementById('lightbox-caption').textContent = caption || currentLightboxFilename;
  modal.style.display = 'flex';
}

function closeLightboxModal() {
  const modal = document.getElementById('lightbox-modal');
  if (modal) modal.style.display = 'none';
  currentLightboxUrl = '';
  currentLightboxFilename = '';
}

function syncIssueInList(updatedIssue) {
  const idx = allIssues.findIndex(i => i.id === updatedIssue.id);
  if (idx !== -1) allIssues[idx] = updatedIssue;
  updateTagFilterOptions();
  renderBoard();
  updateSprintBanner();
}

// ==================== NOTIFICATIONS ====================
async function loadNotifications() {
  try {
    const res = await fetch('/api/notifications');
    if (!res.ok) return;
    allNotifications = await res.json();
    renderNotifications();
  } catch (err) {
    console.warn('Failed to load notifications:', err);
  }
}

function renderNotifications() {
  const badgeEl = document.getElementById('notif-badge');
  const unreadCountEl = document.getElementById('notif-unread-count');
  const listEl = document.getElementById('notif-list');

  const unreadCount = allNotifications.filter(n => !n.read).length;

  if (unreadCount > lastUnreadNotificationCount && unreadCount > 0) {
    const notifBell = document.getElementById('notif-bell');
    if (notifBell) {
      notifBell.classList.remove('bell-ringing');
      void notifBell.offsetWidth; // trigger reflow
      notifBell.classList.add('bell-ringing');
      setTimeout(() => notifBell.classList.remove('bell-ringing'), 1000);
    }
  }
  lastUnreadNotificationCount = unreadCount;

  if (unreadCount > 0) {
    badgeEl.textContent = unreadCount;
    badgeEl.style.display = 'block';
    unreadCountEl.textContent = `${unreadCount} Unread`;
  } else {
    badgeEl.style.display = 'none';
    unreadCountEl.textContent = '0 Unread';
  }

  const filtered = activeNotifTab === 'unread'
    ? allNotifications.filter(n => !n.read)
    : allNotifications;

  listEl.innerHTML = '';
  if (filtered.length === 0) {
    listEl.innerHTML = `<div class="notif-empty">${activeNotifTab === 'unread' ? 'No unread notifications' : 'No notifications yet'}</div>`;
    return;
  }

  filtered.forEach(n => {
    const item = document.createElement('div');
    item.className = `notif-item ${n.read ? 'read' : 'unread'}`;

    let iconSvg = getSvgIcon('bell', 'svg-icon-sm');
    if (n.type === 'MENTION') iconSvg = getSvgIcon('mention', 'svg-icon-sm');
    else if (n.type === 'STATUS_CHANGE') iconSvg = getSvgIcon('columns', 'svg-icon-sm');
    else if (n.type === 'ASSIGNED') iconSvg = getSvgIcon('user', 'svg-icon-sm');
    else if (n.type === 'UNASSIGNED') iconSvg = getSvgIcon('userMinus', 'svg-icon-sm') || getSvgIcon('user', 'svg-icon-sm');
    else if (n.type === 'COMMENT') iconSvg = getSvgIcon('message', 'svg-icon-sm');


    const timeAgo = formatTimeAgo(n.created_at);

    item.innerHTML = `
      <span class="notif-icon">${iconSvg}</span>
      <div class="notif-content">
        <div class="notif-item-title">${escapeHtml(n.title)}</div>
        <div class="notif-item-msg">${escapeHtml(n.message)}</div>
        <div class="notif-item-footer">
          <span class="notif-item-time">${timeAgo}</span>
          <button class="notif-toggle-btn" data-id="${n.id}">
            ${n.read ? 'Mark unread' : 'Mark read'}
          </button>
        </div>
      </div>
    `;

    item.addEventListener('click', (e) => {
      if (e.target.classList.contains('notif-toggle-btn')) return;
      if (!n.read) toggleNotificationRead(n.id, true);
      document.getElementById('notif-popover').style.display = 'none';
      openIssueDetail(n.issue_id);
    });

    const toggleBtn = item.querySelector('.notif-toggle-btn');
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleNotificationRead(n.id, !n.read);
    });

    listEl.appendChild(item);
  });
}

async function toggleNotificationRead(notificationId, targetState) {
  try {
    const res = await fetch(`/api/notifications/${notificationId}/toggle-read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ read: targetState })
    });
    if (res.ok) {
      const updated = await res.json();
      const idx = allNotifications.findIndex(n => n.id === notificationId);
      if (idx !== -1) allNotifications[idx] = updated;
      renderNotifications();
    }
  } catch (err) {
    console.error('Failed to toggle notification:', err);
  }
}

async function markAllNotificationsRead() {
  try {
    const res = await fetch('/api/notifications/mark-all-read', { method: 'POST' });
    if (res.ok) {
      allNotifications.forEach(n => { n.read = true; });
      renderNotifications();
    }
  } catch (err) {
    console.error('Failed to mark all as read:', err);
  }
}

// ==================== USERS & DIRECTORY ====================
async function loadUsers() {
  try {
    const res = await fetch('/api/users');
    if (!res.ok) return;
    allUsers = await res.json();

    const assigneeFilter = document.getElementById('assignee-filter');
    assigneeFilter.innerHTML = '<option value="ALL">All Assignees</option><option value="UNASSIGNED">Unassigned</option>';

    const issueAssignee = document.getElementById('issue-assignee');
    issueAssignee.innerHTML = '<option value="">Unassigned</option>';

    const detailAssignee = document.getElementById('detail-assignee-select');
    detailAssignee.innerHTML = '<option value="">Unassigned</option>';

    const mentionChips = document.getElementById('mention-chips');
    mentionChips.innerHTML = '';

    allUsers.forEach(u => {
      const opt1 = document.createElement('option');
      opt1.value = u.username;
      opt1.textContent = `${u.full_name} (@${u.username})`;
      assigneeFilter.appendChild(opt1);

      const opt2 = document.createElement('option');
      opt2.value = u.username;
      opt2.textContent = `${u.full_name} (${u.role})`;
      issueAssignee.appendChild(opt2);

      const opt3 = document.createElement('option');
      opt3.value = u.username;
      opt3.textContent = `${u.full_name} (${u.role})`;
      detailAssignee.appendChild(opt3);

      const chipBtn = document.createElement('button');
      chipBtn.type = 'button';
      chipBtn.className = 'mention-chip-btn';
      chipBtn.textContent = `@${u.username}`;
      chipBtn.onclick = () => insertMention(u.username);
      mentionChips.appendChild(chipBtn);
    });

    renderUsersTable();
  } catch (err) {
    console.error('Failed to load users:', err);
  }
}

function renderUsersTable() {
  const tbody = document.getElementById('users-table-body');
  tbody.innerHTML = '';

  const isAdmin = currentUser && (
    currentUser.role === 'ADMIN' ||
    (currentUser.role && currentUser.role.value === 'ADMIN') ||
    String(currentUser.role).toUpperCase() === 'ADMIN'
  );

  allUsers.forEach(u => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div class="user-row-name">
          <img src="${u.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${u.username}`}" style="width: 24px; height: 24px; border-radius: 50%;">
          <span>${escapeHtml(u.full_name)}</span>
        </div>
      </td>
      <td><code>@${escapeHtml(u.username)}</code></td>
      <td>${escapeHtml(u.email)}</td>
      <td>
        <select class="role-select-inline" data-userid="${u.id}" ${isAdmin ? '' : 'disabled title="Only Admins can modify user roles"'}>
          <option value="ADMIN" ${u.role === 'ADMIN' ? 'selected' : ''}>ADMIN</option>
          <option value="MEMBER" ${u.role === 'MEMBER' ? 'selected' : ''}>MEMBER</option>
          <option value="VIEWER" ${u.role === 'VIEWER' ? 'selected' : ''}>VIEWER</option>
        </select>
      </td>
      <td>
        <div class="user-row-actions">
          <span class="role-badge role-${u.role}">${u.role}</span>
          ${isAdmin ? `
            <button type="button" class="btn btn-xs btn-outline btn-admin-edit-name" data-id="${u.id}" data-username="${escapeHtml(u.username)}" data-fullname="${escapeHtml(u.full_name)}" title="Change name of @${escapeHtml(u.username)}">
              ${getSvgIcon('edit', 'svg-icon-xs')} Name
            </button>
            <button type="button" class="btn btn-xs btn-outline btn-admin-change-pwd" data-id="${u.id}" data-username="${escapeHtml(u.username)}" title="Reset password for @${escapeHtml(u.username)}">
              ${getSvgIcon('shield', 'svg-icon-xs')} Password
            </button>
          ` : ''}
        </div>
      </td>
    `;

    const select = tr.querySelector('.role-select-inline');
    if (isAdmin) {
      select.addEventListener('change', async (e) => {
        const newRole = e.target.value;
        try {
          const res = await fetch(`/api/users/${u.id}/role`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role: newRole })
          });
          if (res.ok) {
            u.role = newRole;
            showToast(`Updated @${u.username} role to ${newRole}`, 'success');
            renderUsersTable();
            loadUsers();
            if (currentUser && currentUser.id === u.id) {
              currentUser.role = newRole;
              updateAuthUI();
            }
          } else {
            const err = await res.json();
            showToast(`Error: ${err.detail || 'Failed to update role'}`, 'error');
            renderUsersTable();
          }
        } catch (err) {
          console.error('Failed to update role:', err);
          showToast('Failed to update role', 'error');
        }
      });

      const editNameBtn = tr.querySelector('.btn-admin-edit-name');
      if (editNameBtn) {
        editNameBtn.onclick = () => {
          document.getElementById('admin-edit-user-id').value = u.id;
          document.getElementById('admin-edit-user-info-label').textContent = `User: @${u.username} (${u.email})`;
          document.getElementById('admin-edit-fullname-input').value = u.full_name;
          document.getElementById('admin-user-edit-modal').style.display = 'flex';
        };
      }

      const changePwdBtn = tr.querySelector('.btn-admin-change-pwd');
      if (changePwdBtn) {
        changePwdBtn.onclick = () => {
          document.getElementById('admin-password-user-id').value = u.id;
          document.getElementById('admin-password-user-label').textContent = `Resetting password for @${u.username} (${u.full_name})`;
          document.getElementById('admin-new-password-input').value = '';
          document.getElementById('admin-password-modal').style.display = 'flex';
        };
      }
    }

    tbody.appendChild(tr);
  });
}

function updateTagFilterOptions() {
  const tagSelect = document.getElementById('tag-filter');
  const currentVal = tagSelect.value;
  const tagsSet = new Set();
  allIssues.forEach(i => (i.tags || []).forEach(t => tagsSet.add(t)));

  tagSelect.innerHTML = '<option value="ALL">All Tags</option>';
  Array.from(tagsSet).sort().forEach(tag => {
    const opt = document.createElement('option');
    opt.value = tag;
    opt.textContent = tag;
    if (tag === currentVal) opt.selected = true;
    tagSelect.appendChild(opt);
  });
}

// ==================== CUSTOM COLUMNS BUILDER UTILS ====================
function initNewProjectColumnsList() {
  newProjectColumns = JSON.parse(JSON.stringify(DEFAULT_COLUMNS));
  renderNewProjectColumnsList();
}

function renderNewProjectColumnsList() {
  const container = document.getElementById('new-proj-columns-list');
  container.innerHTML = '';

  newProjectColumns.forEach((col, idx) => {
    const row = document.createElement('div');
    row.className = 'column-builder-item';
    row.innerHTML = `
      <span class="col-order-handle">#${idx + 1}</span>
      <input type="text" class="col-name-input" value="${escapeHtml(col.name)}" data-idx="${idx}">
      <span class="col-status-tag">${escapeHtml(col.status)}</span>
      <button type="button" class="btn-col-move btn-move-up" data-idx="${idx}" ${idx === 0 ? 'disabled style="opacity:0.3;"' : ''}>${getSvgIcon('up', 'svg-icon-xs')}</button>
      <button type="button" class="btn-col-move btn-move-down" data-idx="${idx}" ${idx === newProjectColumns.length - 1 ? 'disabled style="opacity:0.3;"' : ''}>${getSvgIcon('down', 'svg-icon-xs')}</button>
      <button type="button" class="btn-col-action btn-del-col" data-idx="${idx}" title="Remove Column">${getSvgIcon('trash', 'svg-icon-xs')}</button>
    `;

    row.querySelector('.col-name-input').addEventListener('input', (e) => {
      newProjectColumns[idx].name = e.target.value;
    });

    row.querySelector('.btn-del-col').addEventListener('click', () => {
      if (newProjectColumns.length <= 2) {
        showToast('A board must retain at least two columns.', 'error');
        return;
      }
      newProjectColumns.splice(idx, 1);
      renderNewProjectColumnsList();
    });

    row.querySelector('.btn-move-up').addEventListener('click', () => {
      if (idx > 0) {
        const temp = newProjectColumns[idx];
        newProjectColumns[idx] = newProjectColumns[idx - 1];
        newProjectColumns[idx - 1] = temp;
        renderNewProjectColumnsList();
      }
    });

    row.querySelector('.btn-move-down').addEventListener('click', () => {
      if (idx < newProjectColumns.length - 1) {
        const temp = newProjectColumns[idx];
        newProjectColumns[idx] = newProjectColumns[idx + 1];
        newProjectColumns[idx + 1] = temp;
        renderNewProjectColumnsList();
      }
    });

    container.appendChild(row);
  });
}

function openConfigureColumnsModal() {
  existingBoardColumns = JSON.parse(JSON.stringify(currentBoardColumns));
  renderExistingBoardColumnsList();
  document.getElementById('configure-columns-modal').style.display = 'flex';
}

function renderExistingBoardColumnsList() {
  const container = document.getElementById('existing-board-columns-list');
  container.innerHTML = '';

  existingBoardColumns.forEach((col, idx) => {
    const row = document.createElement('div');
    row.className = 'column-builder-item';
    row.innerHTML = `
      <span class="col-order-handle">#${idx + 1}</span>
      <input type="text" class="col-name-input" value="${escapeHtml(col.name)}" data-idx="${idx}">
      <span class="col-status-tag">${escapeHtml(col.status)}</span>
      <button type="button" class="btn-col-move btn-move-up" data-idx="${idx}" ${idx === 0 ? 'disabled style="opacity:0.3;"' : ''}>${getSvgIcon('up', 'svg-icon-xs')}</button>
      <button type="button" class="btn-col-move btn-move-down" data-idx="${idx}" ${idx === existingBoardColumns.length - 1 ? 'disabled style="opacity:0.3;"' : ''}>${getSvgIcon('down', 'svg-icon-xs')}</button>
      <button type="button" class="btn-col-action btn-del-col" data-idx="${idx}" title="Remove Column">${getSvgIcon('trash', 'svg-icon-xs')}</button>
    `;

    row.querySelector('.col-name-input').addEventListener('input', (e) => {
      existingBoardColumns[idx].name = e.target.value;
    });

    row.querySelector('.btn-del-col').addEventListener('click', () => {
      if (existingBoardColumns.length <= 2) {
        showToast('A board must have at least two columns.', 'error');
        return;
      }
      existingBoardColumns.splice(idx, 1);
      renderExistingBoardColumnsList();
    });

    row.querySelector('.btn-move-up').addEventListener('click', () => {
      if (idx > 0) {
        const temp = existingBoardColumns[idx];
        existingBoardColumns[idx] = existingBoardColumns[idx - 1];
        existingBoardColumns[idx - 1] = temp;
        renderExistingBoardColumnsList();
      }
    });

    row.querySelector('.btn-move-down').addEventListener('click', () => {
      if (idx < existingBoardColumns.length - 1) {
        const temp = existingBoardColumns[idx];
        existingBoardColumns[idx] = existingBoardColumns[idx + 1];
        existingBoardColumns[idx + 1] = temp;
        renderExistingBoardColumnsList();
      }
    });

    container.appendChild(row);
  });
}

// ==================== EVENT LISTENERS SETUP ====================
function setupEventListeners() {
  // Standalone Login form
  document.getElementById('standalone-login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('standalone-username').value.trim();
    const password = document.getElementById('standalone-password').value;
    await handleLogin(username, password);
  });

  // Demo Sign-in buttons
  document.querySelectorAll('.demo-chip-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const user = btn.dataset.user;
      const pwd = btn.dataset.pwd;
      document.getElementById('standalone-username').value = user;
      document.getElementById('standalone-password').value = pwd;
      await handleLogin(user, pwd);
    });
  });

  // Return to login from post-logout view
  document.getElementById('btn-return-login').addEventListener('click', () => {
    showView('login');
  });

  // Logout button in Navbar
  document.getElementById('btn-auth-action').addEventListener('click', handleLogout);

  // Project Switcher
  document.getElementById('project-select').addEventListener('change', async (e) => {
    currentProjectId = e.target.value;
    currentSprintId = 'ALL';
    document.getElementById('issue-project').value = currentProjectId;
    await loadBoard();
  });

  // Sprint Switcher
  document.getElementById('sprint-select').addEventListener('change', (e) => {
    currentSprintId = e.target.value;
    updateSprintBanner();
    renderBoard();
  });

  // Manage Sprints Button
  document.getElementById('btn-manage-sprints').addEventListener('click', openSprintManagementModal);
  document.getElementById('sprint-mgmt-close').addEventListener('click', () => {
    document.getElementById('sprint-mgmt-modal').style.display = 'none';
  });

  // Sprint Management Tabs
  document.getElementById('tab-sprints-active').addEventListener('click', () => {
    document.getElementById('tab-sprints-active').classList.add('active');
    document.getElementById('tab-sprints-create').classList.remove('active');
    document.getElementById('tab-sprints-history').classList.remove('active');
    document.getElementById('pane-sprints-active').style.display = 'block';
    document.getElementById('pane-sprints-create').style.display = 'none';
    document.getElementById('pane-sprints-history').style.display = 'none';
    renderSprintsList();
  });

  document.getElementById('tab-sprints-create').addEventListener('click', () => {
    document.getElementById('tab-sprints-create').classList.add('active');
    document.getElementById('tab-sprints-active').classList.remove('active');
    document.getElementById('tab-sprints-history').classList.remove('active');
    document.getElementById('pane-sprints-create').style.display = 'block';
    document.getElementById('pane-sprints-active').style.display = 'none';
    document.getElementById('pane-sprints-history').style.display = 'none';
  });

  document.getElementById('tab-sprints-history').addEventListener('click', () => {
    document.getElementById('tab-sprints-history').classList.add('active');
    document.getElementById('tab-sprints-active').classList.remove('active');
    document.getElementById('tab-sprints-create').classList.remove('active');
    document.getElementById('pane-sprints-history').style.display = 'block';
    document.getElementById('pane-sprints-active').style.display = 'none';
    document.getElementById('pane-sprints-create').style.display = 'none';
    renderSprintHistory();
  });

  document.getElementById('btn-sprint-history-trigger').addEventListener('click', () => {
    openSprintManagementModal();
    document.getElementById('tab-sprints-history').click();
  });

  // Complete Sprint Modal Close
  document.getElementById('complete-modal-close').addEventListener('click', () => {
    document.getElementById('complete-sprint-modal').style.display = 'none';
  });
  document.getElementById('btn-cancel-complete').addEventListener('click', () => {
    document.getElementById('complete-sprint-modal').style.display = 'none';
  });

  // Create Sprint Form Submit
  document.getElementById('create-sprint-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('new-sprint-name').value.trim();
    const goal = document.getElementById('new-sprint-goal').value.trim();
    const start_date = document.getElementById('new-sprint-start').value || null;
    const end_date = document.getElementById('new-sprint-end').value || null;

    try {
      const res = await fetch('/api/sprints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: currentProjectId,
          name,
          goal,
          start_date,
          end_date
        })
      });

      if (res.ok) {
        showToast(`Sprint "${name}" planned!`, 'success');
        document.getElementById('create-sprint-form').reset();
        await loadSprints(currentProjectId);
        document.getElementById('tab-sprints-active').click();
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Could not create sprint'}`, 'error');
      }
    } catch (err) {
      console.error('Error creating sprint:', err);
    }
  });

  // Manage Board Columns Button
  document.getElementById('btn-manage-columns').addEventListener('click', openConfigureColumnsModal);
  document.getElementById('columns-modal-close').addEventListener('click', () => {
    document.getElementById('configure-columns-modal').style.display = 'none';
  });
  document.getElementById('btn-cancel-columns').addEventListener('click', () => {
    document.getElementById('configure-columns-modal').style.display = 'none';
  });

  // Add Column in Configure Columns Modal
  document.getElementById('btn-add-existing-column').addEventListener('click', () => {
    const input = document.getElementById('existing-col-name-input');
    const name = input.value.trim();
    if (!name) return;
    const slug = name.toUpperCase().replace(/[^A-Z0-9]/g, '_');
    existingBoardColumns.push({
      id: `col-${Date.now()}`,
      name: name,
      status: slug,
      order_index: existingBoardColumns.length
    });
    input.value = '';
    renderExistingBoardColumnsList();
  });

  // Save Columns Configuration
  document.getElementById('btn-save-columns').addEventListener('click', async () => {
    const payload = existingBoardColumns.map((c, idx) => ({
      id: c.id,
      name: c.name,
      status: c.status,
      order_index: idx
    }));

    try {
      const res = await fetch(`/api/board/${currentProjectId}/columns`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ columns: payload })
      });

      if (res.ok) {
        showToast('Kanban columns updated!', 'success');
        document.getElementById('configure-columns-modal').style.display = 'none';
        await loadBoard();
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Failed to update columns'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to save columns:', err);
    }
  });

  // New Project Button & Modal
  document.getElementById('btn-new-project').addEventListener('click', () => {
    initNewProjectColumnsList();
    document.getElementById('create-project-modal').style.display = 'flex';
  });
  document.getElementById('project-modal-close').addEventListener('click', () => {
    document.getElementById('create-project-modal').style.display = 'none';
  });
  document.getElementById('btn-cancel-project').addEventListener('click', () => {
    document.getElementById('create-project-modal').style.display = 'none';
  });

  // Add custom column to New Project builder
  document.getElementById('btn-add-custom-column').addEventListener('click', () => {
    const input = document.getElementById('new-col-name-input');
    const name = input.value.trim();
    if (!name) return;
    const slug = name.toUpperCase().replace(/[^A-Z0-9]/g, '_');
    newProjectColumns.push({
      id: `col-${Date.now()}`,
      name: name,
      status: slug,
      order_index: newProjectColumns.length
    });
    input.value = '';
    renderNewProjectColumnsList();
  });

  // Create Project Form Submit
  document.getElementById('create-project-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const key = document.getElementById('new-proj-key').value.trim().toUpperCase();
    const name = document.getElementById('new-proj-name').value.trim();
    const description = document.getElementById('new-proj-desc').value.trim();

    const columnsPayload = newProjectColumns.map((c, idx) => ({
      id: c.id,
      name: c.name,
      status: c.status,
      order_index: idx
    }));

    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, name, description, columns: columnsPayload })
      });

      if (res.ok) {
        const proj = await res.json();
        document.getElementById('create-project-modal').style.display = 'none';
        document.getElementById('create-project-form').reset();
        currentProjectId = proj.id;
        showToast(`Project ${proj.key} created!`, 'success');
        await loadProjects();
        await loadBoard();
      } else {
        const err = await res.json();
        showToast(`Failed: ${err.detail || 'Error creating project'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to create project:', err);
    }
  });

  // Notification Bell Toggle
  const notifBell = document.getElementById('notif-bell');
  const notifPopover = document.getElementById('notif-popover');
  notifBell.addEventListener('click', (e) => {
    e.stopPropagation();
    notifPopover.style.display = notifPopover.style.display === 'none' ? 'flex' : 'none';
  });

  document.addEventListener('click', (e) => {
    if (!notifPopover.contains(e.target) && e.target !== notifBell) {
      notifPopover.style.display = 'none';
    }
  });

  // Notification Tabs
  document.getElementById('tab-notif-all').addEventListener('click', () => {
    activeNotifTab = 'all';
    document.getElementById('tab-notif-all').classList.add('active');
    document.getElementById('tab-notif-unread').classList.remove('active');
    renderNotifications();
  });
  document.getElementById('tab-notif-unread').addEventListener('click', () => {
    activeNotifTab = 'unread';
    document.getElementById('tab-notif-unread').classList.add('active');
    document.getElementById('tab-notif-all').classList.remove('active');
    renderNotifications();
  });

  document.getElementById('btn-mark-all-read').addEventListener('click', markAllNotificationsRead);

  // Filters Event Listeners
  document.getElementById('search-input').addEventListener('input', renderBoard);
  document.getElementById('tag-filter').addEventListener('change', renderBoard);
  document.getElementById('status-filter').addEventListener('change', renderBoard);
  document.getElementById('assignee-filter').addEventListener('change', renderBoard);
  document.getElementById('role-filter').addEventListener('change', renderBoard);
  document.getElementById('priority-filter').addEventListener('change', renderBoard);

  document.getElementById('btn-reset-filters').addEventListener('click', () => {
    document.getElementById('search-input').value = '';
    document.getElementById('tag-filter').value = 'ALL';
    document.getElementById('status-filter').value = 'ALL';
    document.getElementById('assignee-filter').value = 'ALL';
    document.getElementById('role-filter').value = 'ALL';
    document.getElementById('priority-filter').value = 'ALL';
    currentSprintId = 'ALL';
    document.getElementById('sprint-select').value = 'ALL';
    updateSprintBanner();
    renderBoard();
  });

  // Create Issue Modal
  const createModal = document.getElementById('create-modal');
  document.getElementById('btn-create-issue').addEventListener('click', () => {
    pendingCreateFiles = [];
    document.getElementById('create-attachments-preview').innerHTML = '';
    createModal.style.display = 'flex';
  });
  document.getElementById('modal-close').addEventListener('click', () => {
    createModal.style.display = 'none';
  });
  document.getElementById('btn-cancel').addEventListener('click', () => {
    createModal.style.display = 'none';
  });

  // File drop & browse in Create Issue Modal
  const dropZone = document.getElementById('file-drop-zone');
  const fileInput = document.getElementById('issue-file-input');

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files) {
      handleSelectedFiles(Array.from(e.dataTransfer.files));
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files) {
      handleSelectedFiles(Array.from(e.target.files));
    }
  });

  function handleSelectedFiles(files) {
    files.forEach(f => {
      if (f.type.startsWith('image/')) {
        pendingCreateFiles.push(f);
      }
    });
    renderCreateFilePreviews();
  }

  function renderCreateFilePreviews() {
    const container = document.getElementById('create-attachments-preview');
    container.innerHTML = '';
    pendingCreateFiles.forEach((file, idx) => {
      const chip = document.createElement('div');
      chip.className = 'preview-chip';
      chip.innerHTML = `
        <span>${getSvgIcon('paperclip', 'svg-icon-xs')} ${escapeHtml(file.name)}</span>
        <button type="button" style="background:transparent;border:none;color:#f87171;cursor:pointer;" data-idx="${idx}">&times;</button>
      `;
      chip.querySelector('button').addEventListener('click', () => {
        pendingCreateFiles.splice(idx, 1);
        renderCreateFilePreviews();
      });
      container.appendChild(chip);
    });
  }

  // Submit Create Issue Form
  document.getElementById('create-issue-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const projId = document.getElementById('issue-project').value || currentProjectId;
    const sprintId = document.getElementById('issue-sprint').value || null;
    const title = document.getElementById('issue-title').value.trim();
    const desc = document.getElementById('issue-desc').value.trim();
    const priority = document.getElementById('issue-priority').value;
    const status = document.getElementById('issue-status').value;
    const assignee = document.getElementById('issue-assignee').value || null;
    const rawTags = document.getElementById('issue-tags').value;
    const tags = rawTags.split(',').map(t => t.trim()).filter(Boolean);

    try {
      const res = await fetch('/api/issues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projId,
          sprint_id: sprintId,
          title,
          description: desc,
          priority,
          status,
          assignee,
          tags
        })
      });

      if (!res.ok) {
        showToast('Failed to create issue', 'error');
        return;
      }

      const newIssue = await res.json();
      showToast(`Issue ${newIssue.key} created!`, 'success');

      // Upload pending files
      if (pendingCreateFiles.length > 0) {
        for (const file of pendingCreateFiles) {
          const formData = new FormData();
          formData.append('file', file);
          const attRes = await fetch(`/api/issues/${newIssue.id}/attachments`, {
            method: 'POST',
            body: formData
          });
          if (attRes.ok) {
            const att = await attRes.json();
            newIssue.attachments.push(att);
          }
        }
      }

      if (newIssue.project_id === currentProjectId) {
        allIssues.push(newIssue);
        updateTagFilterOptions();
        renderBoard();
        updateSprintBanner();
      }

      createModal.style.display = 'none';
      document.getElementById('create-issue-form').reset();
      pendingCreateFiles = [];
      document.getElementById('create-attachments-preview').innerHTML = '';
      loadNotifications();
    } catch (err) {
      console.error('Error creating issue:', err);
    }
  });

  // Issue Detail Modal Close
  document.getElementById('detail-modal-close').addEventListener('click', () => {
    document.getElementById('issue-detail-modal').style.display = 'none';
    activeIssueDetail = null;
    stagedCommentImages = [];
    renderStagedCommentImages();
    const commentInput = document.getElementById('comment-input');
    if (commentInput) commentInput.value = '';
    const detailFileInput = document.getElementById('detail-upload-file');
    if (detailFileInput) detailFileInput.value = '';
  });

  // Add Tag in Detail Modal
  const tagInlineInput = document.getElementById('detail-tags-input');
  tagInlineInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const val = tagInlineInput.value.trim();
      if (val && !activeIssueDetail.tags.includes(val)) {
        activeIssueDetail.tags.push(val);
        renderDetailTags();
        tagInlineInput.value = '';
      }
    }
  });

  // Assignee selection change in Detail Modal Spotlight
  document.getElementById('detail-assignee-select').addEventListener('change', (e) => {
    updateAssigneeSpotlightUI(e.target.value);
  });

  // Save Issue Details button (Sprint cannot be edited from Ticket Details)
  document.getElementById('btn-save-issue-details').addEventListener('click', async () => {
    if (!activeIssueDetail) return;
    const title = document.getElementById('detail-title-input').value.trim();
    const description = document.getElementById('detail-desc-input').value.trim();
    const priority = document.getElementById('detail-priority-select').value;
    const assignee = document.getElementById('detail-assignee-select').value || null;
    const tags = activeIssueDetail.tags || [];

    try {
      const res = await fetch(`/api/issues/${activeIssueDetail.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, priority, assignee, tags })
      });

      if (res.ok) {
        activeIssueDetail = await res.json();
        syncIssueInList(activeIssueDetail);
        const statusMsg = document.getElementById('detail-save-msg');
        statusMsg.textContent = '✓ Saved successfully!';
        setTimeout(() => { statusMsg.textContent = ''; }, 2500);
      }
    } catch (err) {
      console.error('Failed to update issue:', err);
    }
  });

  // Detail Modal Add Image Upload
  document.getElementById('detail-upload-file').addEventListener('change', async (e) => {
    if (!e.target.files || !e.target.files[0] || !activeIssueDetail) return;
    const file = e.target.files[0];
    const targetIssueId = activeIssueDetail.id;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`/api/issues/${targetIssueId}/attachments`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const att = await res.json();
        // Check if user is still on the same issue
        if (activeIssueDetail && activeIssueDetail.id === targetIssueId) {
          activeIssueDetail.attachments = activeIssueDetail.attachments || [];
          activeIssueDetail.attachments.push(att);
          renderDetailAttachments();
          syncIssueInList(activeIssueDetail);
        } else {
          // If user switched ticket during upload, update the target ticket in allIssues
          const target = allIssues.find(i => i.id === targetIssueId);
          if (target) {
            target.attachments = target.attachments || [];
            target.attachments.push(att);
            syncIssueInList(target);
          }
        }
        showToast(`Attachment "${att.filename}" uploaded`, 'success');
      } else {
        showToast('Failed to upload attachment', 'error');
      }
    } catch (err) {
      console.error('Failed to upload attachment:', err);
      showToast('Error uploading attachment', 'error');
    } finally {
      e.target.value = '';
    }
  });

  // Staged Comment Images Helpers (moved to top-level scope)

  const commentAttachBtn = document.getElementById('btn-comment-attach-img');
  const commentFileInput = document.getElementById('comment-img-file-input');
  if (commentAttachBtn && commentFileInput) {
    commentAttachBtn.addEventListener('click', () => {
      commentFileInput.click();
    });

    commentFileInput.addEventListener('change', async (e) => {
      const files = Array.from(e.target.files || []);
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        try {
          const res = await fetch('/api/comments/upload-image', {
            method: 'POST',
            body: formData
          });
          if (res.ok) {
            const data = await res.json();
            const imgUrl = data.file_url || data.url;
            if (imgUrl) {
              stagedCommentImages.push(imgUrl);
              renderStagedCommentImages();
            }
          } else {
            showToast('Failed to upload comment image', 'error');
          }
        } catch (err) {
          console.error('Error uploading comment image:', err);
        }
      }
      commentFileInput.value = '';
    });
  }

  // Post Comment in Detail Modal with Attached Images
  document.getElementById('comment-composer-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!activeIssueDetail) return;
    const content = document.getElementById('comment-input').value.trim();
    if (!content && stagedCommentImages.length === 0) return;

    try {
      const res = await fetch(`/api/issues/${activeIssueDetail.id}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: content || '(Attached picture)',
          images: stagedCommentImages
        })
      });

      if (res.ok) {
        const newComment = await res.json();
        activeIssueDetail.comments.push(newComment);
        renderDetailComments();
        syncIssueInList(activeIssueDetail);
        document.getElementById('comment-input').value = '';
        stagedCommentImages = [];
        renderStagedCommentImages();
        loadNotifications();
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Could not post comment'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to post comment:', err);
    }
  });

  // Lightbox download action
  const lightboxDownloadBtn = document.getElementById('lightbox-download');
  if (lightboxDownloadBtn) {
    lightboxDownloadBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!currentLightboxUrl) return;

      try {
        const res = await fetch(currentLightboxUrl);
        if (!res.ok) throw new Error('Fetch failed');
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = currentLightboxFilename || 'attachment.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      } catch (err) {
        const a = document.createElement('a');
        a.href = currentLightboxUrl;
        a.download = currentLightboxFilename || 'attachment.png';
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    });
  }

  // Lightbox close action
  const lightboxCloseBtn = document.getElementById('lightbox-close');
  if (lightboxCloseBtn) {
    lightboxCloseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeLightboxModal();
    });
  }

  // Lightbox backdrop click to close
  const lightboxModal = document.getElementById('lightbox-modal');
  if (lightboxModal) {
    lightboxModal.addEventListener('click', (e) => {
      if (e.target === lightboxModal) {
        closeLightboxModal();
      }
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modal = document.getElementById('lightbox-modal');
      if (modal && modal.style.display !== 'none') {
        closeLightboxModal();
      }
    }
  });

  // User Profile Modal (Self Name Change)
  document.getElementById('user-profile').addEventListener('click', () => {
    if (!currentUser) return;
    document.getElementById('profile-username-display').value = `@${currentUser.username}`;
    document.getElementById('profile-fullname-input').value = currentUser.full_name || '';
    document.getElementById('user-profile-modal').style.display = 'flex';
  });

  document.getElementById('profile-modal-close').addEventListener('click', () => {
    document.getElementById('user-profile-modal').style.display = 'none';
  });
  document.getElementById('btn-cancel-profile').addEventListener('click', () => {
    document.getElementById('user-profile-modal').style.display = 'none';
  });

  document.getElementById('user-profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentUser) return;
    const newName = document.getElementById('profile-fullname-input').value.trim();
    if (!newName) return;

    try {
      const res = await fetch(`/api/users/${currentUser.id}/name`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: newName })
      });
      if (res.ok) {
        currentUser = await res.json();
        updateAuthUI();
        await loadUsers();
        renderBoard();
        document.getElementById('user-profile-modal').style.display = 'none';
        showToast('Your name has been updated!', 'success');
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Failed to update name'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to update profile name:', err);
    }
  });

  // Admin Edit User Name Modal
  document.getElementById('admin-user-edit-close').addEventListener('click', () => {
    document.getElementById('admin-user-edit-modal').style.display = 'none';
  });
  document.getElementById('btn-cancel-admin-user-edit').addEventListener('click', () => {
    document.getElementById('admin-user-edit-modal').style.display = 'none';
  });

  document.getElementById('admin-user-edit-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = document.getElementById('admin-edit-user-id').value;
    const newName = document.getElementById('admin-edit-fullname-input').value.trim();
    if (!userId || !newName) return;

    try {
      const res = await fetch(`/api/users/${userId}/name`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: newName })
      });
      if (res.ok) {
        const updated = await res.json();
        showToast(`Updated name for @${updated.username}!`, 'success');
        document.getElementById('admin-user-edit-modal').style.display = 'none';
        await loadUsers();
        renderBoard();
        if (currentUser && currentUser.id === updated.id) {
          currentUser.full_name = updated.full_name;
          updateAuthUI();
        }
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Failed to update name'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to update user name:', err);
    }
  });

  // Admin Change Password Modal
  document.getElementById('admin-password-close').addEventListener('click', () => {
    document.getElementById('admin-password-modal').style.display = 'none';
  });
  document.getElementById('btn-cancel-admin-password').addEventListener('click', () => {
    document.getElementById('admin-password-modal').style.display = 'none';
  });

  document.getElementById('admin-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = document.getElementById('admin-password-user-id').value;
    const newPassword = document.getElementById('admin-new-password-input').value;
    if (!userId || !newPassword) return;

    try {
      const res = await fetch(`/api/users/${userId}/password`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: newPassword })
      });
      if (res.ok) {
        const updated = await res.json();
        showToast(`Password for @${updated.username} updated!`, 'success');
        document.getElementById('admin-password-modal').style.display = 'none';
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Failed to change password'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to change password:', err);
    }
  });

  // User Management Modal
  document.getElementById('btn-manage-users').addEventListener('click', () => {
    document.getElementById('user-mgmt-modal').style.display = 'flex';
  });
  document.getElementById('user-mgmt-close').addEventListener('click', () => {
    document.getElementById('user-mgmt-modal').style.display = 'none';
  });

  // User Management Tabs
  document.getElementById('tab-users-list').addEventListener('click', () => {
    document.getElementById('tab-users-list').classList.add('active');
    document.getElementById('tab-users-add').classList.remove('active');
    document.getElementById('pane-users-list').style.display = 'block';
    document.getElementById('pane-users-add').style.display = 'none';
  });

  document.getElementById('tab-users-add').addEventListener('click', () => {
    document.getElementById('tab-users-add').classList.add('active');
    document.getElementById('tab-users-list').classList.remove('active');
    document.getElementById('pane-users-add').style.display = 'block';
    document.getElementById('pane-users-list').style.display = 'none';
  });

  // Add User Form Submit
  document.getElementById('add-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('add-user-username').value.trim();
    const password = document.getElementById('add-user-password').value;
    const full_name = document.getElementById('add-user-fullname').value.trim();
    const email = document.getElementById('add-user-email').value.trim();
    const role = document.getElementById('add-user-role').value;

    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, full_name, email, role })
      });

      if (res.ok) {
        showToast(`User @${username} created successfully!`, 'success');
        document.getElementById('add-user-form').reset();
        document.getElementById('tab-users-list').click();
        await loadUsers();
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || 'Could not create user'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to create user:', err);
    }
  });
}

// ==================== UTILS ====================
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast-pill toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatTimeAgo(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return 'Just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return `${Math.floor(diffSec / 86400)}d ago`;
}
