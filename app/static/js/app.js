/**
 * Solar - AI Meeting -> Execution Frontend JS
 */

document.addEventListener('DOMContentLoaded', () => {
  initNotificationPolling();
  initMeetingStatusPolling();
  initTaskStatusDropdowns();
  initInlineTaskEditing();
});

// Helper to get CSRF token
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute('content');
  const input = document.querySelector('input[name="csrf_token"]');
  if (input) return input.value;
  return '';
}

// 1. Notification Badge Polling (60s)
function initNotificationPolling() {
  const badgeEl = document.getElementById('nav-notification-badge');
  if (!badgeEl) return;

  function checkCount() {
    fetch('/notifications/count', {
      headers: { 'Accept': 'application/json' }
    })
    .then(res => res.ok ? res.json() : null)
    .then(data => {
      if (data && typeof data.unread_count === 'number') {
        if (data.unread_count > 0) {
          badgeEl.textContent = data.unread_count;
          badgeEl.style.display = 'inline';
        } else {
          badgeEl.style.display = 'none';
        }
      }
    })
    .catch(err => console.debug('Notification count check:', err));
  }

  checkCount();
  setInterval(checkCount, 60000);
}

// 2. Meeting Status Polling (every 3s when processing/pending)
function initMeetingStatusPolling() {
  const statusContainer = document.getElementById('meeting-status-container');
  if (!statusContainer) return;

  const meetingId = statusContainer.getAttribute('data-meeting-id');
  const currentStatus = statusContainer.getAttribute('data-status');

  if (currentStatus === 'pending' || currentStatus === 'processing') {
    const interval = setInterval(() => {
      fetch(`/meetings/${meetingId}/status`)
        .then(res => res.json())
        .then(data => {
          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
            window.location.reload();
          }
        })
        .catch(err => console.error('Status poll error:', err));
    }, 3000);
  }
}

// 3. Task Status Inline Update
function initTaskStatusDropdowns() {
  document.querySelectorAll('.task-status-select').forEach(select => {
    select.addEventListener('change', (e) => {
      const taskId = e.target.getAttribute('data-task-id');
      const newStatus = e.target.value;

      fetch(`/tasks/${taskId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ status: newStatus })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          // Update status badge class if applicable
          const badge = document.getElementById(`task-badge-${taskId}`);
          if (badge) {
            badge.className = `status-badge ${newStatus.toLowerCase().replace(' ', '-')}`;
            badge.textContent = newStatus;
          }
        } else {
          alert('Failed to update task status.');
        }
      })
      .catch(err => {
        console.error('Error updating status:', err);
        alert('An error occurred updating task status.');
      });
    });
  });
}

// 4. Inline Task Details Editor
function initInlineTaskEditing() {
  document.querySelectorAll('.btn-edit-task').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const taskId = btn.getAttribute('data-task-id');
      const editRow = document.getElementById(`task-edit-row-${taskId}`);
      if (editRow) {
        editRow.style.display = editRow.style.display === 'none' ? 'table-row' : 'none';
      }
    });
  });
}

function saveInlineTask(taskId) {
  const title = document.getElementById(`edit-title-${taskId}`)?.value;
  const owner_name = document.getElementById(`edit-owner-${taskId}`)?.value;
  const deadline = document.getElementById(`edit-deadline-${taskId}`)?.value;
  const status = document.getElementById(`edit-status-${taskId}`)?.value;

  fetch(`/tasks/${taskId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({ title, owner_name, deadline, status })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.reload();
    } else {
      alert('Failed to save changes.');
    }
  })
  .catch(err => {
    console.error('Save task error:', err);
    alert('An error occurred while saving.');
  });
}

function deleteTask(taskId) {
  if (!confirm('Are you sure you want to delete this task?')) return;

  fetch(`/tasks/${taskId}`, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': getCsrfToken()
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      const row = document.getElementById(`task-row-${taskId}`);
      if (row) row.remove();
      const editRow = document.getElementById(`task-edit-row-${taskId}`);
      if (editRow) editRow.remove();
    } else {
      alert('Failed to delete task.');
    }
  });
}
