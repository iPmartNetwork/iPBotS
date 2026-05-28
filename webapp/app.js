/**
 * V2Ray Shop - Telegram Mini App
 */

// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Apply theme
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#1a1a2e');

// State
let currentTab = 'shop';
let userData = null;
let categories = [];
let plans = [];
let services = [];

// API Base URL (set this to your server)
const API_BASE = window.location.origin + '/api/webapp';

// ============ INITIALIZATION ============

async function init() {
    // Get user data from Telegram
    const initData = tg.initData;
    const user = tg.initDataUnsafe?.user;

    if (user) {
        document.getElementById('userName').textContent = user.first_name || 'کاربر';
        document.getElementById('profileName').textContent =
            `${user.first_name || ''} ${user.last_name || ''}`.trim();
        document.getElementById('profileId').textContent = `ID: ${user.id}`;
    }

    // Load data
    await loadCategories();
    await loadUserData();
}

// ============ TAB NAVIGATION ============

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');

    currentTab = tab;

    // Load tab-specific data
    if (tab === 'services') loadServices();
    if (tab === 'wallet') loadWallet();
}

// ============ SHOP ============

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`, {
            headers: { 'X-Telegram-Init-Data': tg.initData }
        });
        categories = await response.json();
        renderCategories();
    } catch (e) {
        // Demo data
        categories = [
            { id: 1, name: 'اقتصادی', icon: '💰' },
            { id: 2, name: 'استاندارد', icon: '📦' },
            { id: 3, name: 'حرفه‌ای', icon: '⚡' },
            { id: 4, name: 'نامحدود', icon: '♾️' },
        ];
        renderCategories();
    }
}

function renderCategories() {
    const container = document.getElementById('categories');
    container.innerHTML = categories.map(cat => `
        <div class="category-card" onclick="loadPlans(${cat.id})">
            <div class="icon">${cat.icon}</div>
            <div class="name">${cat.name}</div>
        </div>
    `).join('');
}

async function loadPlans(categoryId) {
    try {
        const response = await fetch(`${API_BASE}/plans?category=${categoryId}`, {
            headers: { 'X-Telegram-Init-Data': tg.initData }
        });
        plans = await response.json();
    } catch (e) {
        // Demo data
        plans = [
            { id: 1, name: 'پلن 10 گیگ', data: '10 GB', duration: '30 روز', price: 50000, discount: 0, ip_limit: 1 },
            { id: 2, name: 'پلن 30 گیگ', data: '30 GB', duration: '30 روز', price: 120000, discount: 10, ip_limit: 2 },
            { id: 3, name: 'پلن 50 گیگ', data: '50 GB', duration: '60 روز', price: 200000, discount: 15, ip_limit: 2 },
        ];
    }
    renderPlans();
}

function renderPlans() {
    const container = document.getElementById('plans');
    const title = document.getElementById('plansTitle');
    title.style.display = 'block';

    container.innerHTML = plans.map(plan => {
        const discountBadge = plan.discount > 0
            ? `<span class="discount-badge">${plan.discount}% تخفیف</span>`
            : '';
        const finalPrice = plan.discount > 0
            ? Math.floor(plan.price * (100 - plan.discount) / 100)
            : plan.price;

        return `
            <div class="plan-card" onclick="selectPlan(${plan.id})">
                <div class="plan-header">
                    <span class="plan-name">${plan.name}</span>
                    ${discountBadge}
                </div>
                <div class="plan-specs">
                    <span>📊 ${plan.data}</span>
                    <span>⏱️ ${plan.duration}</span>
                    <span>👥 ${plan.ip_limit} کاربر</span>
                </div>
                <div class="plan-header" style="margin-top:10px; margin-bottom:0;">
                    <span></span>
                    <span class="plan-price">${finalPrice.toLocaleString('fa-IR')} تومان</span>
                </div>
            </div>
        `;
    }).join('');
}

function selectPlan(planId) {
    const plan = plans.find(p => p.id === planId);
    if (!plan) return;

    const finalPrice = plan.discount > 0
        ? Math.floor(plan.price * (100 - plan.discount) / 100)
        : plan.price;

    showModal(`
        <h3 style="margin-bottom:16px;">🛒 خرید ${plan.name}</h3>
        <div style="margin-bottom:16px; font-size:14px;">
            <p>📊 حجم: ${plan.data}</p>
            <p>⏱️ مدت: ${plan.duration}</p>
            <p>👥 کاربر همزمان: ${plan.ip_limit}</p>
            <p style="margin-top:8px; font-size:18px; font-weight:700; color:var(--success);">
                💰 ${finalPrice.toLocaleString('fa-IR')} تومان
            </p>
        </div>
        <div style="display:flex; flex-direction:column; gap:8px;">
            <button class="btn btn-primary" onclick="pay('zarinpal', ${planId})" style="width:100%;">
                💳 پرداخت آنلاین (زرین‌پال)
            </button>
            <button class="btn btn-success" onclick="pay('wallet', ${planId})" style="width:100%;">
                💰 پرداخت از کیف پول
            </button>
            <button class="btn btn-outline" onclick="pay('crypto', ${planId})" style="width:100%;">
                🪙 ارز دیجیتال
            </button>
            <button class="btn btn-outline" onclick="pay('card2card', ${planId})" style="width:100%;">
                🏦 کارت به کارت
            </button>
            <button class="btn btn-outline" onclick="closeModal()" style="width:100%;">
                ❌ انصراف
            </button>
        </div>
    `);
}

// ============ SERVICES ============

async function loadServices() {
    try {
        const response = await fetch(`${API_BASE}/services`, {
            headers: { 'X-Telegram-Init-Data': tg.initData }
        });
        services = await response.json();
        renderServices();
    } catch (e) {
        // Demo
        services = [];
        renderServices();
    }
}

function renderServices() {
    const container = document.getElementById('servicesList');

    if (services.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📦</div>
                <p>سرویسی خریداری نشده</p>
                <button class="btn btn-primary" onclick="switchTab('shop')">خرید سرویس</button>
            </div>
        `;
        return;
    }

    container.innerHTML = services.map(svc => {
        const statusClass = svc.is_active ? 'status-active' : 'status-expired';
        const statusText = svc.is_active ? 'فعال' : 'منقضی';
        const percent = svc.traffic_percent || 0;
        const progressClass = percent < 50 ? 'progress-green' : percent < 80 ? 'progress-yellow' : 'progress-red';

        return `
            <div class="service-card" onclick="showServiceDetail(${svc.id})">
                <div class="service-header">
                    <span class="service-name">${svc.plan_name}</span>
                    <span class="service-status ${statusClass}">${statusText}</span>
                </div>
                <div class="progress-bar">
                    <div class="fill ${progressClass}" style="width:${percent}%"></div>
                </div>
                <div class="service-info">
                    <span>📊 ${svc.used_gb}/${svc.total_gb} GB</span>
                    <span>⏱️ ${svc.remaining_days} روز</span>
                </div>
            </div>
        `;
    }).join('');
}

// ============ WALLET ============

async function loadWallet() {
    try {
        const response = await fetch(`${API_BASE}/wallet`, {
            headers: { 'X-Telegram-Init-Data': tg.initData }
        });
        const data = await response.json();
        document.getElementById('walletBalance').textContent = data.balance.toLocaleString('fa-IR');
    } catch (e) {
        document.getElementById('walletBalance').textContent = '0';
    }
}

async function loadUserData() {
    try {
        const response = await fetch(`${API_BASE}/user`, {
            headers: { 'X-Telegram-Init-Data': tg.initData }
        });
        userData = await response.json();
        document.getElementById('userBalance').textContent = `💰 ${(userData.balance || 0).toLocaleString('fa-IR')} تومان`;
        document.getElementById('statPurchases').textContent = userData.total_purchases || 0;
        document.getElementById('statSpent').textContent = (userData.total_spent || 0).toLocaleString('fa-IR');
        document.getElementById('statReferrals').textContent = userData.referral_count || 0;
    } catch (e) {
        // Ignore
    }
}

// ============ ACTIONS ============

function requestTrial() {
    tg.sendData(JSON.stringify({ action: 'trial' }));
    tg.showAlert('درخواست تست رایگان ارسال شد!');
}

function pay(method, planId) {
    tg.sendData(JSON.stringify({ action: 'pay', method, planId }));
    closeModal();
    if (method === 'zarinpal') {
        tg.showAlert('در حال انتقال به درگاه پرداخت...');
    } else if (method === 'wallet') {
        tg.showAlert('در حال پردازش...');
    }
}

function chargeWallet() {
    tg.sendData(JSON.stringify({ action: 'charge_wallet' }));
}

function withdrawWallet() {
    tg.sendData(JSON.stringify({ action: 'withdraw' }));
}

function openCustomPlan() {
    tg.sendData(JSON.stringify({ action: 'custom_plan' }));
}

function showReferral() {
    tg.sendData(JSON.stringify({ action: 'referral' }));
}

function showLoyalty() {
    tg.sendData(JSON.stringify({ action: 'loyalty' }));
}

function showReseller() {
    tg.sendData(JSON.stringify({ action: 'reseller' }));
}

function showSupport() {
    tg.sendData(JSON.stringify({ action: 'support' }));
}

function showTutorial() {
    showModal(`
        <h3 style="margin-bottom:16px;">📖 آموزش اتصال</h3>
        <div class="profile-menu" style="margin-bottom:16px;">
            <div class="menu-item" onclick="openTutorial('android')">
                <span>🤖 اندروید (v2rayNG)</span>
                <span class="arrow">←</span>
            </div>
            <div class="menu-item" onclick="openTutorial('ios')">
                <span>🍎 آیفون (Streisand)</span>
                <span class="arrow">←</span>
            </div>
            <div class="menu-item" onclick="openTutorial('windows')">
                <span>🖥️ ویندوز (v2rayN)</span>
                <span class="arrow">←</span>
            </div>
            <div class="menu-item" onclick="openTutorial('mac')">
                <span>💻 مک (V2Box)</span>
                <span class="arrow">←</span>
            </div>
        </div>
        <button class="btn btn-outline" onclick="closeModal()" style="width:100%;">بستن</button>
    `);
}

function openTutorial(platform) {
    tg.sendData(JSON.stringify({ action: 'tutorial', platform }));
}

function changeLanguage() {
    tg.sendData(JSON.stringify({ action: 'change_language' }));
}

function showServiceDetail(serviceId) {
    tg.sendData(JSON.stringify({ action: 'service_detail', serviceId }));
}

// ============ MODAL ============

function showModal(content) {
    document.getElementById('modalContent').innerHTML = content;
    document.getElementById('modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

// Close modal on backdrop click
document.getElementById('modal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modal')) {
        closeModal();
    }
});

// ============ INIT ============
init();
