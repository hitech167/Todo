/**
 * Modern Todo & Scheduler JavaScript
 * Handles real-time reminders, notification chimes, schedule validations, and quick toggles.
 */

// Sound chime synthesizer using Web Audio API (Zero external assets required)
function playReminderChime() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        
        // Gentle bell chime: Two harmonic sine tones
        const now = ctx.currentTime;
        
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(587.33, now); // D5
        osc1.frequency.exponentialRampToValueAtTime(880, now + 0.15); // A5
        gain1.gain.setValueAtTime(0.3, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
        
        osc1.connect(gain1);
        gain1.connect(ctx.destination);
        osc1.start(now);
        osc1.stop(now + 1.2);

        // Echo harmonic
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(880, now + 0.15);
        osc2.frequency.exponentialRampToValueAtTime(1174.66, now + 0.35); // D6
        gain2.gain.setValueAtTime(0.2, now + 0.15);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 1.4);

        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start(now + 0.15);
        osc2.stop(now + 1.4);
    } catch (e) {
        console.warn('Audio playback not permitted or supported:', e);
    }
}

// Request Desktop Notifications
function requestNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            Notification.requestPermission().then(perm => {
                if (perm === 'granted') {
                    showToast('Notifications enabled!', 'You will now receive desktop alerts for scheduled reminders.', 'success');
                }
            });
        }
    }
}

// Show In-App Toast
function showToast(title, message, type = 'info', actions = null) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `reminder-toast ${type === 'danger' ? 'border-danger' : ''}`;
    
    let actionsHtml = '';
    if (actions) {
        actionsHtml = `<div class="reminder-toast-actions">${actions}</div>`;
    }

    toast.innerHTML = `
        <div class="reminder-toast-icon">
            <i class="bi bi-bell-fill"></i>
        </div>
        <div class="reminder-toast-content">
            <div class="reminder-toast-title">${title}</div>
            <div class="reminder-toast-desc">${message}</div>
            ${actionsHtml}
        </div>
        <button type="button" class="btn-close ms-2" aria-label="Close" onclick="this.parentElement.remove()"></button>
    `;

    container.appendChild(toast);

    // Auto dismiss after 10 seconds if no actions
    if (!actions) {
        setTimeout(() => {
            if (toast && toast.parentElement) {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 400);
            }
        }, 10000);
    }
}

// Track already triggered reminders in this session to prevent spamming
const triggeredReminders = new Set();

// Poll reminders from API
async function checkActiveReminders() {
    try {
        const resp = await fetch('/api/reminders');
        if (!resp.ok) return;
        const data = await resp.json();
        
        // Update bell badge
        const badge = document.getElementById('bellBadge');
        if (badge) {
            if (data.active_count > 0) {
                badge.textContent = data.active_count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }

        // Check for reminders due now or overdue
        if (data.due_reminders && data.due_reminders.length > 0) {
            data.due_reminders.forEach(todo => {
                if (!triggeredReminders.has(todo.sno)) {
                    triggeredReminders.add(todo.sno);
                    playReminderChime();
                    
                    // Show in-app banner
                    const actions = `
                        <button class="btn btn-sm btn-primary py-0 px-2" onclick="dismissReminder(${todo.sno}, this)">Dismiss</button>
                        <a href="/update/${todo.sno}" class="btn btn-sm btn-outline-secondary py-0 px-2">View Task</a>
                    `;
                    showToast(`⏰ Reminder: ${todo.title}`, `${todo.desc || 'Scheduled task due now!'}`, 'danger', actions);

                    // Show system desktop notification
                    if ('Notification' in window && Notification.permission === 'granted') {
                        new Notification(`⏰ Reminder: ${todo.title}`, {
                            body: `Scheduled: ${todo.schedule_date || ''} ${todo.start_time || ''}\n${todo.desc || ''}`,
                            icon: '/static/favicon.ico'
                        });
                    }
                }
            });
        }
    } catch (err) {
        // Silent catch for background polling
    }
}

// Dismiss Reminder
async function dismissReminder(sno, btnElement) {
    try {
        const resp = await fetch(`/dismiss-reminder/${sno}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        });
        if (resp.ok) {
            if (btnElement) {
                const toast = btnElement.closest('.reminder-toast');
                if (toast) toast.remove();
            }
            checkActiveReminders();
        }
    } catch (e) {
        console.error('Error dismissing reminder:', e);
    }
}

// Toggle Task Status (Pending / Completed)
async function toggleStatus(sno, btn) {
    try {
        const resp = await fetch(`/toggle-status/${sno}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        });
        const data = await resp.json();
        if (data.success) {
            const card = document.getElementById(`todo-card-${sno}`);
            if (card) {
                if (data.new_status === 'Completed') {
                    card.classList.add('is-completed');
                    btn.classList.add('is-checked');
                    btn.innerHTML = '<i class="bi bi-check-lg"></i>';
                } else {
                    card.classList.remove('is-completed');
                    btn.classList.remove('is-checked');
                    btn.innerHTML = '';
                }
            } else {
                // If in table or another view, reload or refresh
                location.reload();
            }
            checkActiveReminders();
        }
    } catch (e) {
        console.error('Status toggle error:', e);
    }
}

// Schedule Form Validation helper
document.addEventListener('DOMContentLoaded', () => {
    // Schedule time validation
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');

    if (startTimeInput && endTimeInput) {
        endTimeInput.addEventListener('change', () => {
            if (startTimeInput.value && endTimeInput.value) {
                if (endTimeInput.value < startTimeInput.value) {
                    alert('End time cannot be earlier than start time for the same day.');
                    endTimeInput.value = '';
                }
            }
        });
    }

    // Set default schedule date to today if empty on creation form
    const scheduleDateInput = document.getElementById('schedule_date');
    if (scheduleDateInput && !scheduleDateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        scheduleDateInput.value = today;
    }

    // Initial check for reminders and set recurring timer
    checkActiveReminders();
    setInterval(checkActiveReminders, 15000); // Check every 15 seconds
});
