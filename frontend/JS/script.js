/* ===================================================
   CARCRAFT AUTOMOTIVE - COMPLETE API-BACKED FRONTEND
   JWT Auth + MySQL/SQLite Persistent Cart via Django REST API
   Backend: http://127.0.0.1:8000
   =================================================== */

const API_BASE = 'http://127.0.0.1:8000';
const TOKEN_KEY = 'carcraft_access_token';
const REFRESH_KEY = 'carcraft_refresh_token';
const USER_KEY = 'carcraft_user';
// Guest cart kept in localStorage as fallback (merges on login)
const GUEST_CART_KEY = 'carcraft_guest_cart';
const COUPON_STORAGE_KEY = 'carcraft_applied_coupon';

/* ===================================================
   TOKEN & AUTH HELPERS
   =================================================== */

function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

function saveTokens(access, refresh) {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
}

function saveUser(userObj) {
    localStorage.setItem(USER_KEY, JSON.stringify(userObj));
}

function getUser() {
    try {
        const s = localStorage.getItem(USER_KEY);
        return s ? JSON.parse(s) : null;
    } catch(e) { return null; }
}

function isLoggedIn() {
    return !!getAccessToken();
}

/* ===================================================
   API FETCH HELPER (auto-attaches JWT, handles 401)
   =================================================== */

async function apiFetch(path, options = {}) {
    const token = getAccessToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };
    if (token) headers['Authorization'] = 'Bearer ' + token;

    const response = await fetch(API_BASE + path, {
        ...options,
        headers
    });

    // Try to refresh token on 401
    if (response.status === 401 && getRefreshToken()) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
            headers['Authorization'] = 'Bearer ' + getAccessToken();
            return fetch(API_BASE + path, { ...options, headers });
        } else {
            clearTokens();
            updateNavForAuth();
        }
    }

    return response;
}

async function tryRefreshToken() {
    const refresh = getRefreshToken();
    if (!refresh) return false;
    try {
        const res = await fetch(API_BASE + '/api/auth/token/refresh/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
        });
        if (res.ok) {
            const data = await res.json();
            saveTokens(data.access, data.refresh || refresh);
            return true;
        }
    } catch(e) {}
    return false;
}

/* ===================================================
   CART BADGE UPDATE
   =================================================== */

async function updateCartBadges() {
    let count = 0;
    if (isLoggedIn()) {
        try {
            const res = await apiFetch('/api/cart/');
            if (res.ok) {
                const data = await res.json();
                count = data.total_items || 0;
            }
        } catch(e) {
            // fallback to guest count
            count = getGuestCart().reduce((t, i) => t + (i.quantity || 1), 0);
        }
    } else {
        count = getGuestCart().reduce((t, i) => t + (i.quantity || 1), 0);
    }

    const badges = document.querySelectorAll('.cart-badge-count, #cartCountBadge');
    badges.forEach(badge => {
        badge.innerText = count;
        badge.classList.remove('cart-badge-bounce');
        void badge.offsetWidth;
        badge.classList.add('cart-badge-bounce');
    });
}

/* ===================================================
   GUEST CART (localStorage fallback for unauthenticated)
   =================================================== */

function getGuestCart() {
    try {
        const s = localStorage.getItem(GUEST_CART_KEY);
        return s ? JSON.parse(s) : [];
    } catch(e) { return []; }
}

function saveGuestCart(cart) {
    localStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
    updateCartBadges();
}

/* ===================================================
   FLOATING NOTIFICATION TOAST
   =================================================== */

let toastTimeout = null;

function showCartToast(name, image, price) {
    let toast = document.getElementById('carcraftGlobalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'carcraftGlobalToast';
        toast.className = 'cart-toast';
        document.body.appendChild(toast);
    }
    const imgTag = image ? `<img src="${image}" alt="${name}" class="cart-toast-thumb" onerror="this.src='https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=150&q=80'">` : '';
    const priceStr = price ? '₹' + Number(price).toLocaleString('en-IN') : '';
    toast.innerHTML = `
        ${imgTag}
        <div class="cart-toast-info">
            <div class="small text-warning fw-bold text-uppercase" style="letter-spacing:0.5px;">Added to Cart &check;</div>
            <div class="cart-toast-title">${name || 'Automotive Part'}</div>
            <div class="cart-toast-price">${priceStr}</div>
        </div>
        <a href="cart.html" class="btn btn-warning btn-sm fw-bold px-3 text-nowrap">View Cart</a>
    `;
    toast.classList.add('show');
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => toast.classList.remove('show'), 3800);
}

function showToast(msg, type = 'success') {
    let t = document.getElementById('carcraftMsgToast');
    if (!t) {
        t = document.createElement('div');
        t.id = 'carcraftMsgToast';
        t.style.cssText = 'position:fixed;top:80px;right:24px;z-index:9999;min-width:260px;max-width:360px;padding:14px 18px;border-radius:10px;font-size:14px;font-weight:600;box-shadow:0 4px 18px rgba(0,0,0,0.2);transition:all 0.3s;opacity:0;pointer-events:none;';
        document.body.appendChild(t);
    }
    t.style.background = type === 'success' ? '#198754' : (type === 'error' ? '#dc3545' : '#0d6efd');
    t.style.color = '#fff';
    t.style.opacity = '1';
    t.style.pointerEvents = 'auto';
    t.innerText = msg;
    clearTimeout(t._timeout);
    t._timeout = setTimeout(() => { t.style.opacity = '0'; t.style.pointerEvents = 'none'; }, 3200);
}

/* ===================================================
   ADD TO CART (API-backed for logged in, guest for anon)
   =================================================== */

async function addToCart(itemData) {
    if (!itemData) return;

    if (isLoggedIn()) {
        const productId = itemData.db_id || itemData.product_id || itemData.id || itemData.sku || itemData.name;
        try {
            const res = await apiFetch('/api/cart/items/', {
                method: 'POST',
                body: JSON.stringify({
                    product_id: productId,
                    quantity: itemData.quantity || 1,
                    name: itemData.name,
                    price: itemData.price,
                    category: itemData.category,
                    image: itemData.image
                })
            });
            if (res.ok) {
                showCartToast(itemData.name, itemData.image || '', itemData.price || '');
                await updateCartBadges();
                if (document.getElementById('cartItemsContainer')) {
                    await renderCartPage();
                }
            } else {
                const err = await res.json().catch(() => ({}));
                showToast(err.error || 'Could not add to cart.', 'error');
            }
        } catch(e) {
            showToast('Network error. Please check if the backend is running.', 'error');
        }
    } else {
        addToGuestCart(itemData);
        showCartToast(itemData.name, itemData.image || '', itemData.price || '');
    }
}

function addToGuestCart(itemData) {
    const cart = getGuestCart();
    const key = String(itemData.db_id || itemData.id || itemData.name);
    const idx = cart.findIndex(i => String(i.db_id || i.id || i.name) === key);
    if (idx > -1) {
        cart[idx].quantity = (cart[idx].quantity || 1) + 1;
    } else {
        cart.push({ ...itemData, quantity: 1 });
    }
    saveGuestCart(cart);
}

/* ===================================================
   NAVBAR AUTH STATE UPDATE
   =================================================== */

function updateNavForAuth() {
    const user = getUser();
    const loginLinks = document.querySelectorAll('.nav-login-link');

    loginLinks.forEach(link => {
        if (user) {
            link.textContent = user.username || user.first_name || 'Account';
            link.href = 'dashboard.html';
            link.classList.remove('btn-outline-light');
            link.classList.add('btn-warning');
        } else {
            link.textContent = 'Login';
            link.href = 'login.html';
            link.classList.add('btn-outline-light');
            link.classList.remove('btn-warning');
        }
    });
}

/* ===================================================
   FORMAT CURRENCY
   =================================================== */

function formatCurrency(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN');
}

/* ===================================================
   CART PAGE RENDERING (API-backed)
   =================================================== */

let currentCartData = null; // Store full cart data for checkout

async function renderCartPage() {
    const container = document.getElementById('cartItemsContainer');
    if (!container) return;

    const contentRow = document.getElementById('cartContentRow');
    const emptyView = document.getElementById('emptyCartView');
    const clearBtn = document.getElementById('clearCartBtn');

    if (!isLoggedIn()) {
        // Show guest cart
        renderGuestCartPage();
        return;
    }

    container.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-warning" role="status"></div><p class="mt-2 text-muted">Loading your cart...</p></div>';

    try {
        const res = await apiFetch('/api/cart/');
        if (!res.ok) throw new Error('Cart fetch failed');
        const cart = await res.json();
        currentCartData = cart;

        const items = cart.items || [];

        if (items.length === 0) {
            if (contentRow) contentRow.classList.add('d-none');
            if (emptyView) emptyView.classList.remove('d-none');
            if (clearBtn) clearBtn.classList.add('d-none');
            container.innerHTML = '';
            updateSummary(0, 0, 0, 0);
            return;
        }

        if (contentRow) contentRow.classList.remove('d-none');
        if (emptyView) emptyView.classList.add('d-none');
        if (clearBtn) clearBtn.classList.remove('d-none');

        let html = '';
        items.forEach(item => {
            const qty = item.quantity || 1;
            const price = parseFloat(item.product_price) || 0;
            const subtotal = parseFloat(item.subtotal) || (price * qty);
            const imgSrc = item.product_image || 'https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=150&q=80';

            html += `
            <div class="card cart-item-card p-3 mb-3" id="cart-item-${item.id}">
                <div class="d-flex flex-column flex-sm-row align-items-center gap-3">
                    <img src="${imgSrc}" alt="${item.product_name}" class="cart-item-img shadow-sm"
                         onerror="this.src='https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=150&q=80'">
                    <div class="flex-grow-1 text-center text-sm-start w-100">
                        <span class="badge bg-warning-subtle text-dark small mb-1">${item.product_category || 'PARTS'}</span>
                        <h5 class="fw-bold mb-1">${item.product_name}</h5>
                        <p class="text-muted small mb-2">${item.product_desc || ''}</p>
                        <div class="text-warning fw-bold">${formatCurrency(price)} <span class="text-muted fw-normal small">each</span></div>
                    </div>
                    <div class="d-flex flex-sm-column align-items-center align-items-sm-end justify-content-between w-100 w-sm-auto gap-3">
                        <div class="d-flex align-items-center gap-1 border rounded p-1 bg-light">
                            <button type="button" class="qty-btn" onclick="updateApiQty(${item.id}, ${qty - 1})" title="Decrease">
                                <i class="bi bi-dash"></i>
                            </button>
                            <span class="qty-display">${qty}</span>
                            <button type="button" class="qty-btn" onclick="updateApiQty(${item.id}, ${qty + 1})" title="Increase">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                        <div class="text-end">
                            <strong class="fs-5 text-dark">${formatCurrency(subtotal)}</strong>
                            <div>
                                <button type="button" class="btn-remove-item mt-1" onclick="removeApiItem(${item.id})">
                                    <i class="bi bi-trash3"></i> Remove
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
        });
        container.innerHTML = html;

        // Calculate totals
        const subtotalVal = parseFloat(cart.subtotal) || 0;
        const delivery = cart.delivery_charge || 0;
        const total = cart.total || (subtotalVal + delivery);

        // Apply coupon if any
        const appliedCoupon = localStorage.getItem(COUPON_STORAGE_KEY);
        let discount = 0;
        if (appliedCoupon === 'CARCRAFT10') discount = Math.round(subtotalVal * 0.10);
        else if (appliedCoupon === 'WELCOME50') discount = Math.min(500, 50);

        updateSummary(cart.total_items || items.reduce((t,i) => t + i.quantity, 0), subtotalVal, delivery, discount);

    } catch(e) {
        container.innerHTML = '<div class="alert alert-warning">Could not load cart. Make sure the backend server is running on port 8000.</div>';
    }
}

function updateSummary(totalItems, subtotal, delivery, discount) {
    const net = Math.max(0, subtotal - discount + (delivery || 0));
    const el = id => document.getElementById(id);

    if (el('summaryItemCount')) el('summaryItemCount').innerText = totalItems + (totalItems === 1 ? ' item' : ' items');
    if (el('summarySubtotal')) el('summarySubtotal').innerHTML = formatCurrency(subtotal);
    if (el('summaryDelivery')) {
        const dv = delivery === 0 ? 'FREE' : formatCurrency(delivery);
        el('summaryDelivery').innerHTML = dv;
        el('summaryDelivery').className = delivery === 0 ? 'text-success fw-bold' : 'text-dark fw-bold';
    }
    if (el('discountRow')) {
        if (discount > 0) {
            el('discountRow').style.setProperty('display', 'flex', 'important');
            if (el('discountCodeText')) el('discountCodeText').innerText = localStorage.getItem(COUPON_STORAGE_KEY) || '';
            if (el('summaryDiscount')) el('summaryDiscount').innerHTML = '-' + formatCurrency(discount);
        } else {
            el('discountRow').style.setProperty('display', 'none', 'important');
        }
    }
    if (el('summaryTotal')) el('summaryTotal').innerHTML = formatCurrency(net);
    if (el('modalPayableTotal')) el('modalPayableTotal').innerHTML = formatCurrency(net);
}

function renderGuestCartPage() {
    const container = document.getElementById('cartItemsContainer');
    const contentRow = document.getElementById('cartContentRow');
    const emptyView = document.getElementById('emptyCartView');
    const clearBtn = document.getElementById('clearCartBtn');

    const cart = getGuestCart();

    if (cart.length === 0) {
        if (contentRow) contentRow.classList.add('d-none');
        if (emptyView) emptyView.classList.remove('d-none');
        if (clearBtn) clearBtn.classList.add('d-none');
        container.innerHTML = '';
        // Show login prompt
        const loginPrompt = document.createElement('div');
        loginPrompt.className = 'alert alert-info text-center mb-3';
        loginPrompt.innerHTML = '<i class="bi bi-info-circle me-2"></i><strong>Guest Cart:</strong> <a href="login.html" class="alert-link">Login</a> to save your cart permanently to MySQL.';
        if (emptyView && emptyView.parentNode) emptyView.parentNode.insertBefore(loginPrompt, emptyView);
        updateSummary(0, 0, 0, 0);
        return;
    }

    if (contentRow) contentRow.classList.remove('d-none');
    if (emptyView) emptyView.classList.add('d-none');
    if (clearBtn) clearBtn.classList.remove('d-none');

    let html = '';
    let subtotal = 0;
    cart.forEach(item => {
        const qty = item.quantity || 1;
        const price = parseFloat(item.price) || 0;
        const total = price * qty;
        subtotal += total;
        const imgSrc = item.image || 'https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=150&q=80';
        const idKey = String(item.db_id || item.id || item.name);

        html += `
        <div class="card cart-item-card p-3 mb-3">
            <div class="d-flex flex-column flex-sm-row align-items-center gap-3">
                <img src="${imgSrc}" alt="${item.name}" class="cart-item-img shadow-sm"
                     onerror="this.src='https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=150&q=80'">
                <div class="flex-grow-1 text-center text-sm-start w-100">
                    <span class="badge bg-warning-subtle text-dark small mb-1">${item.category || 'PARTS'}</span>
                    <h5 class="fw-bold mb-1">${item.name}</h5>
                    <p class="text-muted small mb-2">${item.desc || ''}</p>
                    <div class="text-warning fw-bold">${formatCurrency(price)} <span class="text-muted fw-normal small">each</span></div>
                </div>
                <div class="d-flex flex-sm-column align-items-center align-items-sm-end justify-content-between w-100 w-sm-auto gap-3">
                    <div class="d-flex align-items-center gap-1 border rounded p-1 bg-light">
                        <button type="button" class="qty-btn" onclick="updateGuestQty('${idKey}', ${qty - 1})" title="Decrease"><i class="bi bi-dash"></i></button>
                        <span class="qty-display">${qty}</span>
                        <button type="button" class="qty-btn" onclick="updateGuestQty('${idKey}', ${qty + 1})" title="Increase"><i class="bi bi-plus"></i></button>
                    </div>
                    <div class="text-end">
                        <strong class="fs-5 text-dark">${formatCurrency(total)}</strong>
                        <div><button type="button" class="btn-remove-item mt-1" onclick="removeGuestItem('${idKey}')"><i class="bi bi-trash3"></i> Remove</button></div>
                    </div>
                </div>
            </div>
        </div>`;
    });

    // Login prompt banner
    html = `<div class="alert alert-warning mb-3"><i class="bi bi-exclamation-triangle me-2"></i>
        <strong>Guest cart — not saved to database.</strong> <a href="login.html" class="alert-link">Login or Register</a> to save your cart permanently.</div>` + html;

    container.innerHTML = html;
    const delivery = subtotal >= 3000 ? 0 : 99;
    updateSummary(cart.reduce((t,i)=>t+i.quantity,0), subtotal, delivery, 0);
}

/* ===================================================
   CART ITEM OPERATIONS (API)
   =================================================== */

async function updateApiQty(itemId, newQty) {
    if (newQty <= 0) {
        await removeApiItem(itemId);
        return;
    }
    try {
        const res = await apiFetch(`/api/cart/items/${itemId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ quantity: newQty })
        });
        if (res.ok) {
            await renderCartPage();
            await updateCartBadges();
        } else {
            const err = await res.json().catch(() => ({}));
            showToast(err.error || 'Could not update quantity.', 'error');
        }
    } catch(e) { showToast('Network error.', 'error'); }
}

async function removeApiItem(itemId) {
    try {
        const res = await apiFetch(`/api/cart/items/${itemId}/delete/`, { method: 'DELETE' });
        if (res.ok) {
            await renderCartPage();
            await updateCartBadges();
        } else {
            showToast('Could not remove item.', 'error');
        }
    } catch(e) { showToast('Network error.', 'error'); }
}

async function clearCart() {
    if (!confirm('Are you sure you want to remove all items from your cart?')) return;
    if (isLoggedIn()) {
        try {
            await apiFetch('/api/cart/clear/', { method: 'DELETE' });
        } catch(e) {}
    } else {
        saveGuestCart([]);
    }
    await renderCartPage();
    await updateCartBadges();
}

// Guest cart operations
function updateGuestQty(idKey, newQty) {
    if (newQty <= 0) { removeGuestItem(idKey); return; }
    const cart = getGuestCart();
    const item = cart.find(i => String(i.db_id || i.id || i.name) === idKey);
    if (item) item.quantity = newQty;
    saveGuestCart(cart);
    renderGuestCartPage();
}

function removeGuestItem(idKey) {
    const cart = getGuestCart().filter(i => String(i.db_id || i.id || i.name) !== idKey);
    saveGuestCart(cart);
    renderGuestCartPage();
}

/* ===================================================
   PROMO CODE (validates via API for logged-in users)
   =================================================== */

async function applyPromoCode() {
    const input = document.getElementById('couponInput');
    const msg = document.getElementById('couponMessage');
    if (!input || !msg) return;

    const code = input.value.trim().toUpperCase();
    if (!code) {
        msg.className = 'small mb-3 text-danger';
        msg.innerText = 'Please enter a promo code.';
        return;
    }

    if (isLoggedIn()) {
        try {
            const res = await apiFetch('/api/coupons/validate/', {
                method: 'POST',
                body: JSON.stringify({ code })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.valid) {
                localStorage.setItem(COUPON_STORAGE_KEY, code);
                msg.className = 'small mb-3 text-success fw-bold';
                const dv = data.discount_type === 'percent' ? data.discount_value + '% discount' : '₹' + data.discount_value + ' off';
                msg.innerHTML = '&#10003; Promo code ' + code + ' applied! ' + dv + ' added.';
                await renderCartPage();
            } else {
                msg.className = 'small mb-3 text-danger';
                msg.innerText = data.error || 'Invalid promo code.';
            }
        } catch(e) {
            msg.className = 'small mb-3 text-danger';
            msg.innerText = 'Could not validate coupon.';
        }
    } else {
        // Offline validation for guest
        if (code === 'CARCRAFT10' || code === 'WELCOME50') {
            localStorage.setItem(COUPON_STORAGE_KEY, code);
            msg.className = 'small mb-3 text-success fw-bold';
            msg.innerText = '&#10003; Promo code ' + code + ' applied!';
            renderGuestCartPage();
        } else {
            msg.className = 'small mb-3 text-danger';
            msg.innerText = 'Invalid promo code. Try CARCRAFT10';
        }
    }
}

/* ===================================================
   CHECKOUT FLOW
   =================================================== */

function openCheckoutModal() {
    if (!isLoggedIn()) {
        if (confirm('Please login to complete your order. Go to login page?')) {
            window.location.href = 'login.html';
        }
        return;
    }

    if (!currentCartData || !currentCartData.items || currentCartData.items.length === 0) {
        alert('Your cart is empty. Please add items before checking out.');
        return;
    }

    const user = getUser();
    if (user) {
        const nameField = document.getElementById('orderCustomerName');
        if (nameField && (user.first_name || user.username)) {
            nameField.value = (user.first_name + ' ' + (user.last_name || '')).trim() || user.username;
        }
    }

    const modalEl = document.getElementById('checkoutModal');
    if (modalEl && window.bootstrap) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

async function handleCheckoutSubmit(event) {
    if (event) event.preventDefault();

    const nameInput = document.getElementById('orderCustomerName');
    const phoneInput = document.getElementById('orderCustomerPhone');
    const addressInput = document.getElementById('orderCustomerAddress');
    const payUPI = document.getElementById('payUPI');

    const name = nameInput ? nameInput.value.trim() : 'Valued Customer';
    const phone = phoneInput ? phoneInput.value.trim() : '';
    const address = addressInput ? addressInput.value.trim() : '';
    const paymentMethod = payUPI && payUPI.checked ? 'upi' : 'cod';

    const couponCode = localStorage.getItem(COUPON_STORAGE_KEY) || '';

    try {
        const res = await apiFetch('/api/orders/', {
            method: 'POST',
            body: JSON.stringify({
                full_name: name,
                phone: phone,
                shipping_address: address,
                payment_method: paymentMethod,
                coupon_code: couponCode,
            })
        });

        const data = await res.json().catch(() => ({}));

        if (res.ok) {
            // Close checkout modal
            const checkoutModalEl = document.getElementById('checkoutModal');
            if (checkoutModalEl && window.bootstrap) {
                const m = bootstrap.Modal.getInstance(checkoutModalEl);
                if (m) m.hide();
            }

            localStorage.removeItem(COUPON_STORAGE_KEY);

            const orderId = data.order ? data.order.order_number : '#CC-' + Math.floor(10000 + Math.random() * 90000);
            const confirmedEl = document.getElementById('confirmedOrderId');
            const detailsEl = document.getElementById('orderSuccessDetails');
            if (confirmedEl) confirmedEl.innerText = orderId;
            if (detailsEl) detailsEl.innerText = `Thank you, ${name}! Your order has been placed and will be delivered shortly.`;

            const successModalEl = document.getElementById('orderSuccessModal');
            if (successModalEl && window.bootstrap) {
                const successModal = new bootstrap.Modal(successModalEl);
                successModal.show();
            }

            currentCartData = null;
            await renderCartPage();
            await updateCartBadges();
        } else {
            showToast(data.error || 'Order could not be placed. Please try again.', 'error');
        }
    } catch(e) {
        showToast('Network error. Please check the backend is running.', 'error');
    }
}

/* ===================================================
   VEHICLE SEARCH & FILTER (from DB-loaded items)
   =================================================== */

function searchCars() {
    const searchBox = document.getElementById('searchVehicle');
    const brandSelect = document.getElementById('filterBrand');
    const bodySelect = document.getElementById('filterBodyType');

    const search = searchBox ? searchBox.value.trim().toLowerCase() : '';
    const brand = brandSelect ? brandSelect.value.trim().toLowerCase() : '';
    const body = bodySelect ? bodySelect.value.trim().toLowerCase() : '';

    const cars = document.querySelectorAll('.car-item');
    cars.forEach(car => {
        const text = car.innerText.toLowerCase();
        const m = (search === '' || text.includes(search)) &&
                  (brand === '' || text.includes(brand)) &&
                  (body === '' || text.includes(body));
        car.style.display = m ? '' : 'none';
    });
}

/* ===================================================
   VEHICLE DETAILS
   =================================================== */

function viewDetails(car) {
    window.location.href = 'vehicle-details.html' + (car ? '?car=' + encodeURIComponent(car) : '');
}

/* ===================================================
   LOAD VEHICLES FROM API (for vehicles.html)
   =================================================== */

async function loadVehiclesPage() {
    const grid = document.getElementById('vehiclesGrid');
    if (!grid) return;

    grid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-warning"></div><p class="mt-2 text-muted">Loading vehicles...</p></div>';

    try {
        const res = await fetch(API_BASE + '/api/vehicles/');
        const vehicles = await res.json();

        if (!vehicles || vehicles.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center py-5 text-muted"><i class="bi bi-car-front" style="font-size:3rem;"></i><p class="mt-3">No vehicles found. Add vehicles via the Django admin panel.</p></div>';
            return;
        }

        grid.innerHTML = vehicles.map(v => {
            const img = v.image || `https://source.unsplash.com/400x250/?${encodeURIComponent((v.make + ' ' + v.name).trim())},car`;
            return `
            <div class="col-lg-4 col-md-6 car-item" data-make="${(v.make||'').toLowerCase()}" data-body="${(v.body_type||'').toLowerCase()}">
                <div class="vehicle-card">
                    <img src="${img}" alt="${v.make} ${v.name}" onerror="this.src='https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=400&q=80'">
                    <div class="p-4">
                        <span class="badge bg-success">Available</span>
                        <h4 class="mt-2">${v.make} ${v.name}</h4>
                        <p class="text-muted">${v.body_type} &bull; ${v.year_start}${v.year_end ? '-'+v.year_end : '+'}</p>
                        <a href="vehicle-details.html?id=${v.id}" class="btn btn-dark w-100 mt-2">View Details</a>
                    </div>
                </div>
            </div>`;
        }).join('');

        // Populate brand filter
        const brandSelect = document.getElementById('filterBrand');
        if (brandSelect) {
            const makes = [...new Set(vehicles.map(v => v.make).filter(Boolean))];
            makes.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.toLowerCase(); opt.textContent = m;
                brandSelect.appendChild(opt);
            });
        }

    } catch(e) {
        grid.innerHTML = '<div class="col-12"><div class="alert alert-warning">Could not load vehicles. Make sure the Django backend is running on <strong>port 8000</strong>.</div></div>';
    }
}

/* ===================================================
   LOAD PRODUCTS FROM API (for parts.html)
   =================================================== */

async function loadPartsPage() {
    const grid = document.getElementById('productsGrid');
    if (!grid) return;

    grid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-warning"></div><p class="mt-2 text-muted">Loading parts...</p></div>';

    try {
        const res = await fetch(API_BASE + '/api/products/');
        if (!res.ok) throw new Error('Failed');
        const products = await res.json();

        if (!products || products.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center py-5 text-muted"><p>No products found. Add products via the Django admin panel.</p></div>';
            return;
        }

        grid.innerHTML = products.map(p => {
            const img = p.main_image_url || 'https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=300&q=80';
            const price = parseFloat(p.effective_price || p.price);
            const badgeHtml = p.is_bestseller ? '<span class="badge bg-danger me-1">Bestseller</span>' : '';
            const featBadge = p.is_featured ? '<span class="badge bg-warning text-dark me-1">Featured</span>' : '';
            const discountBadge = p.discount_percent > 0 ? `<span class="badge bg-success">${p.discount_percent}% OFF</span>` : '';

            return `
            <div class="col-lg-3 col-md-6">
                <div class="product-card" data-db-id="${p.id}" data-name="${p.name}" data-price="${price}" data-category="${p.category_name || 'PARTS'}" data-desc="${p.short_description || ''}">
                    <img src="${img}" alt="${p.name}" onerror="this.src='https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=300&q=80'">
                    <div class="p-3">
                        <div class="mb-1">${badgeHtml}${featBadge}${discountBadge}</div>
                        <small class="text-warning fw-bold">${p.category_name || 'PARTS'}</small>
                        <h5>${p.name}</h5>
                        <p class="text-muted">${p.short_description || ''}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>₹${price.toLocaleString('en-IN')}</strong>
                                ${p.discount_price ? `<small class="text-muted text-decoration-line-through ms-1">₹${parseFloat(p.price).toLocaleString('en-IN')}</small>` : ''}
                            </div>
                            <button onclick="addToCart({db_id:${p.id}, name:'${p.name.replace(/'/g,"\\'")}', price:${price}, image:'${img}', category:'${p.category_name || "PARTS"}', desc:'${(p.short_description||'').replace(/'/g,"\\'")}'})"
                                class="btn btn-warning" title="Add to Cart">
                                <i class="bi bi-cart-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('');

        // Category filter
        const catFilter = document.getElementById('filterCategory');
        if (catFilter) {
            const cats = [...new Set(products.map(p => p.category_name).filter(Boolean))];
            cats.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c; opt.textContent = c;
                catFilter.appendChild(opt);
            });
            catFilter.addEventListener('change', function() {
                filterProducts(this.value);
            });
        }

    } catch(e) {
        grid.innerHTML = '<div class="col-12"><div class="alert alert-warning">Could not load products. Make sure the Django backend is running on <strong>port 8000</strong>.</div></div>';
    }
}

function filterProducts(category) {
    const cards = document.querySelectorAll('#partsContainer .col-lg-3, #productsGrid .col-lg-3');
    cards.forEach(card => {
        const cat = card.querySelector('.product-card')?.dataset?.category || '';
        card.style.display = (!category || cat.toUpperCase() === category.toUpperCase()) ? '' : 'none';
    });
}

/* ===================================================
   LOAD DASHBOARD DATA FROM API
   =================================================== */

async function loadDashboard() {
    const user = getUser();
    const nameEl = document.getElementById('dashboardUserName');
    const roleEl = document.getElementById('dashboardUserRole');
    if (nameEl && user) nameEl.textContent = (user.first_name || user.username || 'User');
    if (roleEl && user) roleEl.textContent = (user.role || 'Customer');

    try {
        const res = await apiFetch('/api/dashboard/stats/');
        if (!res.ok) return;
        const data = await res.json();

        const setEl = (id, val) => { const e = document.getElementById(id); if(e) e.textContent = val; };
        setEl('statTotalVehicles', data.total_vehicles || 0);
        setEl('statTotalOrders', data.total_orders || 0);
        setEl('statTotalCustomers', data.total_customers || 0);
        setEl('statTotalRevenue', '₹' + Number(data.total_revenue || 0).toLocaleString('en-IN'));
        setEl('statTotalProducts', data.total_products || 0);
        setEl('statPendingServices', data.pending_services || 0);

        // Recent orders table
        const tbody = document.getElementById('recentOrdersTable');
        if (tbody && data.recent_orders) {
            tbody.innerHTML = data.recent_orders.map(o => `
                <tr>
                    <td>${o.order_number}</td>
                    <td>${o.customer}</td>
                    <td>₹${Number(o.total).toLocaleString('en-IN')}</td>
                    <td><span class="badge bg-${o.status==='delivered'?'success':o.status==='cancelled'?'danger':'warning'} text-dark">${o.status}</span></td>
                    <td>${o.payment_status}</td>
                </tr>`).join('');
        }

        // Upcoming services table
        const svcTbody = document.getElementById('upcomingServicesTable');
        if (svcTbody && data.upcoming_services) {
            svcTbody.innerHTML = data.upcoming_services.map(s => `
                <tr>
                    <td>${s.booking_reference}</td>
                    <td>${s.customer}</td>
                    <td>${s.service}</td>
                    <td>${s.date}</td>
                    <td>${s.time_slot}</td>
                    <td><span class="badge bg-warning text-dark">${s.status}</span></td>
                </tr>`).join('');
        }

    } catch(e) {
        console.error('Dashboard load error:', e);
    }
}

/* ===================================================
   SERVICE BOOKING (submits to API)
   =================================================== */

async function bookService(event) {
    if (event) event.preventDefault();

    const form = event ? event.target : document.getElementById('serviceBookingForm');
    if (!form) return;

    const data = {
        service_id: form.querySelector('[name="service_id"]')?.value || form.querySelector('#serviceType')?.value || 1,
        vehicle_info: form.querySelector('[name="vehicle_info"]')?.value || form.querySelector('#vehicleInfo')?.value || '',
        registration_number: form.querySelector('[name="registration_number"]')?.value || form.querySelector('#regNumber')?.value || 'N/A',
        booking_date: form.querySelector('[name="booking_date"]')?.value || form.querySelector('#bookingDate')?.value || '',
        time_slot: form.querySelector('[name="time_slot"]')?.value || form.querySelector('#timeSlot')?.value || '',
        notes: form.querySelector('[name="notes"]')?.value || form.querySelector('#serviceNotes')?.value || '',
    };

    if (!data.booking_date || !data.time_slot) {
        showToast('Please select a booking date and time slot.', 'error');
        return;
    }

    try {
        const res = await apiFetch('/api/service-appointments/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        const result = await res.json().catch(() => ({}));

        if (res.ok) {
            showToast('Service booked! Reference: ' + result.booking_reference, 'success');
            form.reset();
            const successEl = document.getElementById('serviceBookingSuccess');
            if (successEl) {
                successEl.textContent = 'Booking confirmed! Reference: ' + result.booking_reference + '. Our service advisor will call you to confirm.';
                successEl.classList.remove('d-none');
            } else {
                alert('Booking confirmed! Reference: ' + result.booking_reference + '\nOur service advisor will call you to confirm.');
            }
        } else {
            showToast(result.error || (result.service_id ? 'Please select a valid service type.' : 'Booking failed. Please try again.'), 'error');
        }
    } catch(e) {
        showToast('Network error. Make sure the backend is running.', 'error');
    }
}

/* ===================================================
   LOGIN PAGE HANDLER
   =================================================== */

async function handleLogin(event) {
    if (event) event.preventDefault();

    const form = event ? event.target : document.getElementById('loginForm');
    const emailInput = form ? (form.querySelector('#loginEmail') || form.querySelector('#loginIdentifier') || form.querySelector('input[name="identifier"]') || form.querySelector('input[type="text"]') || form.querySelector('input[type="email"]')) : null;
    const passInput = form ? (form.querySelector('#loginPassword') || form.querySelector('[type="password"]')) : null;
    const errEl = document.getElementById('loginError');

    if (!emailInput || !passInput) return;

    const identifier = emailInput.value.trim();
    const password = passInput.value;

    if (!identifier || !password) {
        if (errEl) { errEl.textContent = 'Email, username, or phone and password are required.'; errEl.classList.remove('d-none'); }
        return;
    }

    const btn = form.querySelector('[type="submit"]');
    if (btn) { btn.disabled = true; btn.textContent = 'Logging in...'; }

    try {
        const res = await fetch(API_BASE + '/api/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: identifier, identifier: identifier, password })
        });
        const data = await res.json().catch(() => ({}));

        if (res.ok) {
            saveTokens(data.tokens.access, data.tokens.refresh);
            saveUser(data.user);

            // Merge guest cart into API cart
            const guestItems = getGuestCart();
            for (const item of guestItems) {
                const pid = item.db_id || item.product_id || item.id || item.sku || item.name;
                if (pid) {
                    await apiFetch('/api/cart/items/', {
                        method: 'POST',
                        body: JSON.stringify({
                            product_id: pid,
                            quantity: item.quantity || 1,
                            name: item.name,
                            price: item.price,
                            category: item.category,
                            image: item.image
                        })
                    }).catch(() => {});
                }
            }
            localStorage.removeItem(GUEST_CART_KEY);

            window.location.href = 'index.html';
        } else {
            const msg = data.error || 'Login failed. Please check your credentials.';
            if (errEl) { errEl.textContent = msg; errEl.classList.remove('d-none'); }
            else alert(msg);
        }
    } catch(e) {
        const msg = 'Connection error. Make sure the Django backend is running on port 8000.';
        if (errEl) { errEl.textContent = msg; errEl.classList.remove('d-none'); }
        else alert(msg);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Login'; }
    }
}

/* ===================================================
   REGISTER PAGE HANDLER
   =================================================== */

async function handleRegister(event) {
    if (event) event.preventDefault();

    const form = event ? event.target : document.getElementById('registerForm');
    const errEl = document.getElementById('registerError');
    const successEl = document.getElementById('registerSuccess');

    const fullName = (form.querySelector('#regFullName') || form.querySelector('[placeholder*="full name" i]') || { value: '' }).value.trim();
    const email = (form.querySelector('#regEmail') || form.querySelector('[type="email"]') || { value: '' }).value.trim();
    const phone = (form.querySelector('#regPhone') || form.querySelector('[type="tel"]') || { value: '' }).value.trim();
    const passwords = form.querySelectorAll('[type="password"]');
    const password = passwords[0] ? passwords[0].value : '';
    const password2 = passwords[1] ? passwords[1].value : '';

    if (!fullName || !email || !password || !password2) {
        if (errEl) { errEl.textContent = 'All fields are required.'; errEl.classList.remove('d-none'); }
        return;
    }

    if (password !== password2) {
        if (errEl) { errEl.textContent = 'Passwords do not match.'; errEl.classList.remove('d-none'); }
        return;
    }

    const nameParts = fullName.split(' ');
    const firstName = nameParts[0];
    const lastName = nameParts.slice(1).join(' ');

    const btn = form.querySelector('[type="submit"]');
    if (btn) { btn.disabled = true; btn.textContent = 'Creating account...'; }

    try {
        const res = await fetch(API_BASE + '/api/auth/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ first_name: firstName, last_name: lastName, email, phone, password, password2 })
        });
        const data = await res.json().catch(() => ({}));

        if (res.ok) {
            saveTokens(data.tokens.access, data.tokens.refresh);
            saveUser(data.user);
            if (successEl) {
                successEl.textContent = 'Account created! Redirecting...';
                successEl.classList.remove('d-none');
            }
            if (errEl) errEl.classList.add('d-none');
            setTimeout(() => window.location.href = 'index.html', 1200);
        } else {
            const msgs = [];
            if (data.email) msgs.push(data.email);
            if (data.password) msgs.push(Array.isArray(data.password) ? data.password.join(' ') : data.password);
            if (data.password2) msgs.push(data.password2);
            if (data.non_field_errors) msgs.push(data.non_field_errors);
            const msg = msgs.join(' ') || data.error || data.detail || 'Registration failed. Please try again.';
            if (errEl) { errEl.textContent = msg; errEl.classList.remove('d-none'); }
            else alert(msg);
        }
    } catch(e) {
        const msg = 'Connection error. Make sure the Django backend is running on port 8000.';
        if (errEl) { errEl.textContent = msg; errEl.classList.remove('d-none'); }
        else alert(msg);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Create Account'; }
    }
}

/* ===================================================
   LOGOUT
   =================================================== */

function logout() {
    clearTokens();
    localStorage.removeItem(COUPON_STORAGE_KEY);
    updateNavForAuth();
    window.location.href = 'login.html';
}

/* ===================================================
   INITIALIZATION ON DOM LOAD
   =================================================== */

document.addEventListener('DOMContentLoaded', async function () {
    // Add nav-login-link class to all login buttons for dynamic update
    document.querySelectorAll('a[href="login.html"].btn').forEach(el => {
        el.classList.add('nav-login-link');
    });

    // Auth state in nav
    updateNavForAuth();

    // If logged in, show logout button
    const user = getUser();
    if (user) {
        document.querySelectorAll('.nav-login-link').forEach(el => {
            el.href = 'dashboard.html';
            el.textContent = user.first_name || user.username || 'Account';
        });
    }

    // Cart badge
    await updateCartBadges();

    // Page-specific init
    if (document.getElementById('cartItemsContainer')) {
        await renderCartPage();
    }

    if (document.getElementById('vehiclesGrid')) {
        await loadVehiclesPage();
        const sb = document.getElementById('searchVehicle');
        const bf = document.getElementById('filterBrand');
        const btf = document.getElementById('filterBodyType');
        if (sb) sb.addEventListener('input', searchCars);
        if (bf) bf.addEventListener('change', searchCars);
        if (btf) btf.addEventListener('change', searchCars);
    } else if (document.getElementById('cars')) {
        const sb = document.getElementById('searchVehicle');
        const bf = document.getElementById('filterBrand');
        const btf = document.getElementById('filterBodyType');
        if (sb) sb.addEventListener('input', searchCars);
        if (bf) bf.addEventListener('change', searchCars);
        if (btf) btf.addEventListener('change', searchCars);
    }

    if (document.getElementById('productsGrid')) {
        await loadPartsPage();
    }

    // Category filter for parts.html static cards
    const partsContainer = document.getElementById('partsContainer');
    if (partsContainer) {
        const catFilter = document.getElementById('filterCategory');
        if (catFilter) {
            const cards = partsContainer.querySelectorAll('.product-card');
            const cats = [...new Set(Array.from(cards).map(c => c.dataset.category).filter(Boolean))];
            cats.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c; opt.textContent = c;
                catFilter.appendChild(opt);
            });
            catFilter.addEventListener('change', function() {
                filterProducts(this.value);
            });
        }
    }

    // Dashboard
    if (document.getElementById('statTotalVehicles')) {
        await loadDashboard();
    }

    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Service booking form
    const svcForm = document.getElementById('serviceBookingForm');
    if (svcForm) {
        svcForm.addEventListener('submit', bookService);
        // Load services dynamically
        loadServicesIntoForm();
    }

    // Logout button
    document.querySelectorAll('[onclick*="logout"], #logoutBtn, .logout-btn').forEach(el => {
        el.addEventListener('click', function(e) { e.preventDefault(); logout(); });
    });

    // Ensure hero background video autoplays smoothly
    const heroVid = document.querySelector('.hero-video');
    if (heroVid) {
        heroVid.muted = true;
        heroVid.play().catch(() => {});
    }
});

/* ===================================================
   LOAD SERVICES INTO BOOKING FORM
   =================================================== */

async function loadServicesIntoForm() {
    const select = document.getElementById('serviceType');
    if (!select) return;
    try {
        const res = await fetch(API_BASE + '/api/services/');
        if (!res.ok) return;
        const services = await res.json();
        // Keep existing options, add DB services
        select.innerHTML = '<option value="">Select Service Type...</option>';
        services.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.name + ' (from ₹' + Number(s.base_price).toLocaleString('en-IN') + ')';
            select.appendChild(opt);
        });
    } catch(e) {}
}
