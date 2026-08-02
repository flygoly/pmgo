const platform = window.pmgoPlatform;
const defaultSettings = { provider: 'openai-compatible', model: 'gpt-4.1-mini', base_url: 'https://api.openai.com/v1' };
let state = { project_id: null, projects: [], tasks: [], risks: [], counts: {} };
let settings = defaultSettings;
let activeNote = 'overview';

try { settings = { ...defaultSettings, ...JSON.parse(localStorage.getItem('pmgo.provider') || '{}') }; } catch { settings = defaultSettings; }

const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' })[char]);
const noteLabels = { overview: '项目概览', meetings: '会议记录', decisions: '决策日志', weekly: '周报' };

function toast(message) {
  $('#toast').textContent = message;
  $('#toast').classList.add('show');
  setTimeout(() => $('#toast').classList.remove('show'), 1800);
}

async function request(options) {
  try { return await platform.request(options); }
  catch (error) { toast(error.message || '操作失败'); throw error; }
}

async function loadDashboard(projectId = state.project_id) {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : '';
  state = await request({ route: `/api/dashboard${query}` });
  $('#project-select').innerHTML = state.projects.map((project) => `<option value="${escapeHtml(project.id)}">${escapeHtml(project.name)}</option>`).join('');
  if (state.project_id) $('#project-select').value = state.project_id;
  for (const status of ['todo', 'doing', 'blocked', 'done']) $(`#count-${status}`).textContent = state.counts[status] || 0;
  const active = state.tasks.filter((task) => !['done', 'cancelled'].includes(task.status)).slice(0, 7);
  $('#focus-list').innerHTML = active.length ? active.map((task) => `<article class="task" data-task-id="${escapeHtml(task.id)}"><span class="task-dot"></span><div><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.due_at || '尚未设置日期')}</small></div><span class="tag">${escapeHtml(task.priority)}</span></article>`).join('') : '<p class="empty">还没有待处理任务。创建第一项行动，让 pmgo 开始帮你组织工作。</p>';
  $('#risk-list').innerHTML = state.risks.length ? state.risks.map((risk) => `<article class="risk-item"><strong>${escapeHtml(risk.title)}</strong><p>${escapeHtml(risk.mitigation_plan || risk.evidence || '等待补充应对计划')}</p></article>`).join('') : '<p class="empty">当前没有开放风险。</p>';
  renderBoard();
}

function renderBoard() {
  const labels = { todo: '待处理', doing: '进行中', blocked: '受阻', done: '已完成' };
  $('#kanban').innerHTML = Object.entries(labels).map(([status, label]) => {
    const tasks = state.tasks.filter((task) => task.status === status);
    return `<section class="lane" data-status="${status}"><h3>${label} · ${tasks.length}</h3>${tasks.map((task) => `<article class="card" draggable="true" data-task-id="${escapeHtml(task.id)}"><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.priority)}${task.due_at ? ` · ${escapeHtml(task.due_at)}` : ''}</small></article>`).join('')}</section>`;
  }).join('');
}

function showTask(task = null) {
  $('#task-id').value = task?.id || '';
  $('#task-dialog-title').textContent = task ? '编辑任务' : '新建任务';
  $('#task-title').value = task?.title || '';
  $('#task-detail').value = task?.detail || '';
  $('#task-status').value = task?.status || 'todo';
  $('#task-priority').value = task?.priority || 'medium';
  $('#task-due').value = task?.due_at ? String(task.due_at).slice(0, 10) : '';
  $('#delete-task').hidden = !task;
  $('#task-dialog').showModal();
}

async function saveTask() {
  const id = $('#task-id').value;
  const body = { title: $('#task-title').value.trim(), detail: $('#task-detail').value.trim(), status: $('#task-status').value, priority: $('#task-priority').value, due_at: $('#task-due').value || null };
  if (!body.title) return;
  if (id) await request({ route: `/api/tasks/${encodeURIComponent(id)}`, method: 'PATCH', body });
  else await request({ route: '/api/tasks', method: 'POST', body: { ...body, project_id: state.project_id } });
  $('#task-dialog').close();
  await loadDashboard();
  toast(id ? '任务已更新' : '任务已创建');
}

async function loadNote(noteId = activeNote) {
  if (!state.project_id) return;
  activeNote = noteId;
  document.querySelectorAll('.note-tab').forEach((button) => button.classList.toggle('active', button.dataset.note === noteId));
  $('#note-title').textContent = noteLabels[noteId];
  $('#note-status').textContent = '正在读取…';
  const note = await request({ route: `/api/notes/${noteId}?project_id=${encodeURIComponent(state.project_id)}` });
  $('#note-content').value = note.content;
  $('#note-status').textContent = '保存在本地 Markdown';
}

async function loadContextPreview() {
  if (!state.project_id || !$('#include-context').checked) {
    $('#context-preview').textContent = '本次只发送你输入的文字。';
    return;
  }
  const includeNotes = $('#include-notes').checked;
  const context = await request({ route: `/api/context?project_id=${encodeURIComponent(state.project_id)}&include_notes=${includeNotes}` });
  $('#context-preview').textContent = `${context.task_count} 项进行中任务 · ${context.risk_count} 项风险 · ${context.notes.length} 份笔记 · 约 ${context.characters} 字符`;
}

document.querySelectorAll('.nav-item').forEach((button) => button.addEventListener('click', async () => {
  document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item === button));
  document.querySelectorAll('.view').forEach((view) => view.classList.toggle('active-view', view.id === button.dataset.view));
  if (button.dataset.view === 'notes') await loadNote();
  if (button.dataset.view === 'assistant') await loadContextPreview();
}));

$('#project-select').addEventListener('change', async (event) => {
  await loadDashboard(event.target.value);
  if ($('#notes').classList.contains('active-view')) await loadNote();
  if ($('#assistant').classList.contains('active-view')) await loadContextPreview();
});
$('#add-project').addEventListener('click', () => $('#project-dialog').showModal());
$('#create-project').addEventListener('click', async (event) => {
  event.preventDefault();
  const name = $('#project-name').value.trim();
  if (!name) return;
  const project = await request({ route: '/api/projects', method: 'POST', body: { name, description: $('#project-description').value.trim() } });
  $('#project-name').value = '';
  $('#project-description').value = '';
  $('#project-dialog').close();
  await loadDashboard(project.id);
  toast('项目已创建');
});

$('#add-task').addEventListener('click', () => showTask());
$('#save-task').addEventListener('click', async (event) => { event.preventDefault(); await saveTask(); });
$('#delete-task').addEventListener('click', async () => {
  const id = $('#task-id').value;
  if (!id || !window.confirm('确定删除这项任务吗？')) return;
  await request({ route: `/api/tasks/${encodeURIComponent(id)}`, method: 'DELETE' });
  $('#task-dialog').close();
  await loadDashboard();
  toast('任务已删除');
});
$('#refresh').addEventListener('click', () => loadDashboard());
$('#focus-list').addEventListener('click', (event) => {
  const element = event.target.closest('[data-task-id]');
  if (element) showTask(state.tasks.find((task) => task.id === element.dataset.taskId));
});
$('#kanban').addEventListener('click', (event) => {
  const element = event.target.closest('[data-task-id]');
  if (element) showTask(state.tasks.find((task) => task.id === element.dataset.taskId));
});
$('#kanban').addEventListener('dragstart', (event) => { const card = event.target.closest('.card'); if (card) { card.classList.add('dragging'); event.dataTransfer.setData('text/plain', card.dataset.taskId); } });
$('#kanban').addEventListener('dragend', (event) => event.target.closest('.card')?.classList.remove('dragging'));
$('#kanban').addEventListener('dragover', (event) => { const lane = event.target.closest('.lane'); if (lane) { event.preventDefault(); lane.classList.add('drag-over'); } });
$('#kanban').addEventListener('dragleave', (event) => event.target.closest('.lane')?.classList.remove('drag-over'));
$('#kanban').addEventListener('drop', async (event) => {
  const lane = event.target.closest('.lane');
  if (!lane) return;
  event.preventDefault();
  lane.classList.remove('drag-over');
  const id = event.dataTransfer.getData('text/plain');
  await request({ route: `/api/tasks/${encodeURIComponent(id)}`, method: 'PATCH', body: { status: lane.dataset.status } });
  await loadDashboard();
});

document.querySelectorAll('.note-tab').forEach((button) => button.addEventListener('click', () => loadNote(button.dataset.note)));
$('#note-content').addEventListener('input', () => { $('#note-status').textContent = '有未保存修改'; });
$('#save-note').addEventListener('click', async () => {
  await request({ route: `/api/notes/${activeNote}?project_id=${encodeURIComponent(state.project_id)}`, method: 'PUT', body: { content: $('#note-content').value } });
  $('#note-status').textContent = '已保存';
  toast('笔记已保存');
});

async function loadProviders() {
  const result = await request({ route: '/api/providers' });
  $('#provider').innerHTML = result.providers.map((provider) => `<option value="${provider.id}">${escapeHtml(provider.name)}</option>`).join('');
  $('#provider').value = settings.provider;
  $('#model').value = settings.model;
  $('#base-url').value = settings.base_url;
  $('#data-dir').textContent = await platform.dataDir();
  if (await platform.hasProviderKey()) $('#api-key').placeholder = '已由系统安全存储保存';
}

$('#provider').addEventListener('change', async () => {
  const result = await request({ route: '/api/providers' });
  const provider = result.providers.find((item) => item.id === $('#provider').value);
  if (provider) { $('#model').value = provider.default_model; $('#base-url').value = provider.default_url; }
});
$('#save-settings').addEventListener('click', async () => {
  settings = { provider: $('#provider').value, model: $('#model').value.trim(), base_url: $('#base-url').value.trim() };
  localStorage.setItem('pmgo.provider', JSON.stringify(settings));
  if ($('#api-key').value) await platform.saveProviderKey($('#api-key').value);
  $('#api-key').value = '';
  $('#save-status').textContent = '已保存';
});
$('#include-context').addEventListener('change', loadContextPreview);
$('#include-notes').addEventListener('change', loadContextPreview);
$('#ask').addEventListener('click', async () => {
  const prompt = $('#prompt').value.trim();
  if (!prompt) return;
  $('#assistant-status').textContent = '模型正在思考…';
  $('#answer').textContent = '';
  try {
    const result = await request({ route: '/api/chat', method: 'POST', body: { ...settings, prompt, project_id: state.project_id, include_context: $('#include-context').checked, include_notes: $('#include-notes').checked } });
    $('#answer').textContent = result.content || '模型没有返回文本。';
    $('#assistant-status').textContent = '完成';
  } catch (error) { $('#answer').textContent = `请求失败：${error.message}`; $('#assistant-status').textContent = ''; }
});

Promise.all([loadDashboard(), loadProviders()]).catch((error) => { $('#focus-list').innerHTML = `<p class="empty">启动失败：${escapeHtml(error.message)}</p>`; });
