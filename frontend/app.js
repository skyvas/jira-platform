// JiraPlatform Kanban Board Logic
let allIssues = [];
let boardConfig = null;
let draggedIssueId = null;

const COLUMNS = [
  { id: 'BACKLOG', name: 'Backlog' },
  { id: 'TODO', name: 'To Do' },
  { id: 'IN_PROGRESS', name: 'In Progress' },
  { id: 'REVIEW', name: 'In Review' },
  { id: 'DONE', name: 'Done' }
];

document.addEventListener('DOMContentLoaded', () => {
  initBoard();
  setupEventListeners();
});

async function initBoard() {
  try {
    const res = await fetch('/api/board');
    const data = await res.json();
    boardConfig = data.board;
    allIssues = data.issues || [];
    renderBoard();
  } catch (err) {
    console.error('Failed to load board data:', err);
  }
}

function renderBoard() {
  const boardEl = document.getElementById('kanban-board');
  boardEl.innerHTML = '';

  const searchVal = document.getElementById('search-input').value.toLowerCase();
  const priorityVal = document.getElementById('priority-filter').value;

  const filtered = allIssues.filter(issue => {
    const matchesSearch = issue.title.toLowerCase().includes(searchVal) || issue.key.toLowerCase().includes(searchVal);
    const matchesPriority = priorityVal === 'ALL' || issue.priority === priorityVal;
    return matchesSearch && matchesPriority;
  });

  document.getElementById('total-issues-count').textContent = filtered.length;

  COLUMNS.forEach(col => {
    const colIssues = filtered.filter(i => i.status === col.id);
    const colEl = document.createElement('div');
    colEl.className = 'kanban-column';
    colEl.innerHTML = `
      <div class="column-header">
        <span class="column-title">${col.name}</span>
        <span class="column-count">${colIssues.length}</span>
      </div>
      <div class="cards-container" data-status="${col.id}"></div>
    `;

    const container = colEl.querySelector('.cards-container');
    setupDragDropContainer(container, col.id);

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

  card.innerHTML = `
    <div class="card-top">
      <span class="issue-key">${issue.key}</span>
      <span class="priority-badge priority-${issue.priority}">${issue.priority}</span>
    </div>
    <div class="card-title">${escapeHtml(issue.title)}</div>
    <div class="card-bottom">
      <span class="card-assignee">👤 ${issue.assignee || 'Unassigned'}</span>
    </div>
  `;

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
    if (!issue || issue.status === targetStatus) return;

    try {
      const res = await fetch(`/api/issues/${issueId}/move`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: targetStatus })
      });

      if (!res.ok) {
        const errorData = await res.json();
        alert(`Transition Rejected: ${errorData.detail || 'Forbidden state change'}`);
        return;
      }

      const updated = await res.json();
      const idx = allIssues.findIndex(i => i.id === issueId);
      if (idx !== -1) allIssues[idx] = updated;
      renderBoard();
    } catch (err) {
      console.error('Failed to move issue:', err);
    }
  });
}

function setupEventListeners() {
  document.getElementById('search-input').addEventListener('input', renderBoard);
  document.getElementById('priority-filter').addEventListener('change', renderBoard);

  const modal = document.getElementById('create-modal');
  document.getElementById('btn-create-issue').addEventListener('click', () => {
    modal.style.display = 'flex';
  });
  document.getElementById('modal-close').addEventListener('click', () => {
    modal.style.display = 'none';
  });
  document.getElementById('btn-cancel').addEventListener('click', () => {
    modal.style.display = 'none';
  });

  document.getElementById('create-issue-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('issue-title').value;
    const desc = document.getElementById('issue-desc').value;
    const priority = document.getElementById('issue-priority').value;
    const status = document.getElementById('issue-status').value;
    const assignee = document.getElementById('issue-assignee').value || null;

    try {
      const res = await fetch('/api/issues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description: desc, priority, status, assignee })
      });

      if (res.ok) {
        const newIssue = await res.json();
        allIssues.push(newIssue);
        renderBoard();
        modal.style.display = 'none';
        document.getElementById('create-issue-form').reset();
      }
    } catch (err) {
      console.error('Failed to create issue:', err);
    }
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
