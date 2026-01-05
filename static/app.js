const API_BASE_URL = 'http://localhost:8000/api';

// Track current tab
let currentTab = 'all';
window.currentTab = currentTab;

// Update UI based on login status
function updateAddJokeSection() {
    const addJokeSection = document.getElementById('addJokeSection');
    if (window.currentUserToken) {
        addJokeSection.style.display = 'block';
        // Show tabs for logged in users
        updateTabsVisibility();
    } else {
        addJokeSection.style.display = 'none';
        // Hide user-specific tabs
        updateTabsVisibility();
        // Switch to all jokes tab
        switchTab('all');
    }
}

// Update tabs visibility based on login status
function updateTabsVisibility() {
    const tabCreated = document.getElementById('tab-created');
    const tabFavorites = document.getElementById('tab-favorites');
    const tabLiked = document.getElementById('tab-liked');
    const tabDisliked = document.getElementById('tab-disliked');
    
    // Check if tabs exist
    if (!tabCreated || !tabFavorites || !tabLiked || !tabDisliked) {
        console.log('updateTabsVisibility: Tabs not found in DOM');
        return; // Tabs not loaded yet
    }
    
    console.log('updateTabsVisibility: currentUserToken =', !!window.currentUserToken);
    
    if (window.currentUserToken) {
        // Show tabs for logged in users
        tabCreated.style.display = 'inline-block';
        tabFavorites.style.display = 'inline-block';
        tabLiked.style.display = 'inline-block';
        tabDisliked.style.display = 'inline-block';
        console.log('updateTabsVisibility: Tabs should be visible now');
    } else {
        // Hide tabs for logged out users
        tabCreated.style.display = 'none';
        tabFavorites.style.display = 'none';
        tabLiked.style.display = 'none';
        tabDisliked.style.display = 'none';
        console.log('updateTabsVisibility: Tabs hidden');
    }
}

// Switch between tabs
function switchTab(tab) {
    // Prevent accessing user-specific tabs if not logged in
    const userSpecificTabs = ['created', 'favorites', 'liked', 'disliked'];
    if (userSpecificTabs.includes(tab) && !window.currentUserToken) {
        console.log('Cannot access user-specific tab without login');
        // Switch to 'all' tab instead
        tab = 'all';
    }
    
    currentTab = tab;
    window.currentTab = currentTab;
    
    // Update active tab button
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const tabBtn = document.getElementById(`tab-${tab}`);
    if (tabBtn) {
        tabBtn.classList.add('active');
    }
    
    // Update section title
    const titles = {
        'all': 'All Jokes',
        'created': 'My Created Jokes',
        'favorites': 'My Favorites',
        'liked': 'Liked History',
        'disliked': 'Disliked History'
    };
    const titleEl = document.getElementById('sectionTitle');
    if (titleEl) {
        titleEl.textContent = titles[tab] || 'All Jokes';
    }
    
    // Load appropriate jokes
    if (tab === 'all') {
        loadJokes();
    } else if (tab === 'created') {
        loadUserCreatedJokes();
    } else if (tab === 'favorites') {
        loadFavoriteJokes();
    } else if (tab === 'liked') {
        loadLikedJokes();
    } else if (tab === 'disliked') {
        loadDislikedJokes();
    }
}

// Refresh current tab
function refreshCurrentTab() {
    switchTab(currentTab);
}

// Check auth state periodically
setInterval(() => {
    updateAddJokeSection();
    // Also update tabs visibility
    updateTabsVisibility();
}, 500);

// Handle Login
async function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('authError');
    
    if (!email || !password) {
        errorDiv.textContent = 'Please enter email and password';
        return;
    }
    
    errorDiv.textContent = '';
    
    const result = await window.loginUser(email, password);
    if (result.success) {
        // Get token and verify with backend
        const token = await result.user.getIdToken();
        window.currentUserToken = token;
        
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: token })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Login successful:', data);
                document.getElementById('email').value = '';
                document.getElementById('password').value = '';
                // Update tabs visibility with a small delay to ensure DOM is ready
                setTimeout(() => {
                    updateTabsVisibility();
                }, 100);
            } else {
                throw new Error('Backend login failed');
            }
        } catch (error) {
            console.error('Backend login error:', error);
            errorDiv.textContent = 'Login failed: ' + error.message;
        }
    } else {
        errorDiv.textContent = 'Login failed: ' + result.error;
    }
}

// Handle Register
async function handleRegister() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('authError');
    
    if (!email || !password) {
        errorDiv.textContent = 'Please enter email and password';
        return;
    }
    
    if (password.length < 6) {
        errorDiv.textContent = 'Password must be at least 6 characters';
        return;
    }
    
    errorDiv.textContent = '';
    
    const result = await window.registerUser(email, password);
    if (result.success) {
        // Get token and verify with backend
        const token = await result.user.getIdToken();
        window.currentUserToken = token;
        
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: token })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Registration successful:', data);
                document.getElementById('email').value = '';
                document.getElementById('password').value = '';
                errorDiv.textContent = 'Registration successful!';
                errorDiv.className = 'success-message';
                // Update tabs visibility with a small delay to ensure DOM is ready
                setTimeout(() => {
                    updateTabsVisibility();
                }, 100);
            } else {
                throw new Error('Backend registration failed');
            }
        } catch (error) {
            console.error('Backend registration error:', error);
            errorDiv.textContent = 'Registration failed: ' + error.message;
            errorDiv.className = 'error-message';
        }
    } else {
        errorDiv.textContent = 'Registration failed: ' + result.error;
        errorDiv.className = 'error-message';
    }
}

// Handle Logout
async function handleLogout() {
    const result = await window.logoutUser();
    if (result.success) {
        window.currentUserToken = null;
        loadJokes(); // Refresh jokes list
    } else {
        alert('Logout failed: ' + result.error);
    }
}

// Handle Google Login
async function handleGoogleLogin() {
    const errorDiv = document.getElementById('authError');
    errorDiv.textContent = '';
    errorDiv.className = 'error-message';
    
    const result = await window.loginWithGoogle();
    if (result.success) {
        // Get token and verify with backend
        const token = await result.user.getIdToken();
        window.currentUserToken = token;
        
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: token })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Google login successful:', data);
                document.getElementById('email').value = '';
                document.getElementById('password').value = '';
                // Update tabs visibility with a small delay to ensure DOM is ready
                setTimeout(() => {
                    updateTabsVisibility();
                }, 100);
            } else {
                throw new Error('Backend login failed');
            }
        } catch (error) {
            console.error('Backend login error:', error);
            errorDiv.textContent = 'Login failed: ' + error.message;
            errorDiv.className = 'error-message';
        }
    } else {
        errorDiv.textContent = 'Google login failed: ' + result.error;
        errorDiv.className = 'error-message';
    }
}

// Handle Add Joke
async function handleAddJoke(event) {
    event.preventDefault();
    
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    const jokeSetup = document.getElementById('jokeSetup').value.trim();
    const jokePunchline = document.getElementById('jokePunchline').value.trim();
    const errorDiv = document.getElementById('addJokeError');
    const successDiv = document.getElementById('addJokeSuccess');
    
    errorDiv.textContent = '';
    successDiv.textContent = '';
    
    if (!jokeSetup || !jokePunchline) {
        errorDiv.textContent = 'Please fill in both setup and punchline';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/jokes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.currentUserToken}`
            },
            body: JSON.stringify({
                joke_setup: jokeSetup,
                joke_punchline: jokePunchline,
                joke_content: "",
                default_audio_id: "",
                scenarios: [],
                ages: []
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            successDiv.textContent = 'Joke added successfully!';
            document.getElementById('addJokeForm').reset();
            loadJokes(); // Refresh jokes list
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add joke');
        }
    } catch (error) {
        errorDiv.textContent = 'Error: ' + error.message;
    }
}

// Load All Jokes
async function loadJokes() {
    const jokesList = document.getElementById('jokesList');
    jokesList.innerHTML = '<div class="loading">Loading jokes...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/jokes`);
        
        if (response.ok) {
            const data = await response.json();
            displayJokes(data.jokes);
        } else {
            throw new Error('Failed to load jokes');
        }
    } catch (error) {
        jokesList.innerHTML = `<div class="error">Error loading jokes: ${error.message}</div>`;
    }
}

// Display Jokes
function displayJokes(jokes) {
    const jokesList = document.getElementById('jokesList');
    
    if (jokes.length === 0) {
        jokesList.innerHTML = '<div class="no-jokes">No jokes yet. Be the first to add one!</div>';
        return;
    }
    
    jokesList.innerHTML = jokes.map(joke => `
        <div class="joke-card">
            <div class="joke-setup">${escapeHtml(joke.joke_setup || '')}</div>
            <div class="joke-punchline">${escapeHtml(joke.joke_punchline || '')}</div>
            ${joke.joke_content ? `<div class="joke-content">${escapeHtml(joke.joke_content)}</div>` : ''}
            <div class="joke-meta">
                <span class="joke-author">By: ${escapeHtml(joke.creator_id || 'Anonymous')}</span>
                ${joke.created_at ? `<span class="joke-date">${formatDate(joke.created_at)}</span>` : ''}
            </div>
            ${window.currentUserToken ? `
                <div class="joke-actions">
                    <button onclick="handleAddToFavorites('${joke.joke_id}')" class="btn-favorite" title="Add to favorites" id="fav-btn-${joke.joke_id}">
                        ⭐ Favorite
                    </button>
                    <button onclick="handleDeleteFromFavorites('${joke.joke_id}')" class="btn-unfavorite" title="Remove from favorites" id="unfav-btn-${joke.joke_id}" style="display: none;">
                        ❌ Unfavorite
                    </button>
                    <button onclick="handleLikeJoke('${joke.joke_id}')" class="btn-like" title="Like this joke" id="like-btn-${joke.joke_id}">
                        👍 Like
                    </button>
                    <button onclick="handleDislikeJoke('${joke.joke_id}')" class="btn-dislike" title="Dislike this joke" id="dislike-btn-${joke.joke_id}">
                        👎 Dislike
                    </button>
                    ${joke.creator_id === (window.firebaseAuth?.currentUser?.uid || '') ? `
                        <button onclick="handleDeleteCreatedJoke('${joke.joke_id}')" class="btn-delete" title="Delete this joke">
                            🗑️ Delete
                        </button>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Helper Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Handle Add to Favorites
async function handleAddToFavorites(jokeId) {
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    // Get current user ID from Firebase Auth
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/favorites`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.currentUserToken}`
            },
            body: JSON.stringify({
                joke_id: jokeId
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Toggle button visibility
                const favBtn = document.getElementById(`fav-btn-${jokeId}`);
                const unfavBtn = document.getElementById(`unfav-btn-${jokeId}`);
                if (favBtn) favBtn.style.display = 'none';
                if (unfavBtn) unfavBtn.style.display = 'inline-block';
                // Refresh favorites tab if active
                if (currentTab === 'favorites') {
                    loadFavoriteJokes();
                }
            } else {
                alert('Joke is already in your favorites');
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add to favorites');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Handle Delete from Favorites
async function handleDeleteFromFavorites(jokeId) {
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/favorites/${jokeId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Toggle button visibility
                const favBtn = document.getElementById(`fav-btn-${jokeId}`);
                const unfavBtn = document.getElementById(`unfav-btn-${jokeId}`);
                if (favBtn) favBtn.style.display = 'inline-block';
                if (unfavBtn) unfavBtn.style.display = 'none';
                // Refresh favorites tab if active
                if (currentTab === 'favorites') {
                    loadFavoriteJokes();
                }
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to remove from favorites');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Handle Like Joke
async function handleLikeJoke(jokeId) {
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/like-history/${jokeId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Refresh current tab
                if (currentTab === 'all') {
                    loadJokes();
                } else if (currentTab === 'created') {
                    loadUserCreatedJokes();
                } else if (currentTab === 'favorites') {
                    loadFavoriteJokes();
                } else if (currentTab === 'liked') {
                    loadLikedJokes();
                } else if (currentTab === 'disliked') {
                    loadDislikedJokes();
                }
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to like joke');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Handle Dislike Joke
async function handleDislikeJoke(jokeId) {
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/dislike-history/${jokeId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Refresh current tab
                if (currentTab === 'all') {
                    loadJokes();
                } else if (currentTab === 'created') {
                    loadUserCreatedJokes();
                } else if (currentTab === 'favorites') {
                    loadFavoriteJokes();
                } else if (currentTab === 'liked') {
                    loadLikedJokes();
                } else if (currentTab === 'disliked') {
                    loadDislikedJokes();
                }
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to dislike joke');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Handle Delete Created Joke
async function handleDeleteCreatedJoke(jokeId) {
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this joke from your created jokes?')) {
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/created-jokes/${jokeId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('Joke removed from your created jokes');
                // Refresh current tab
                if (currentTab === 'all') {
                    loadJokes();
                } else if (currentTab === 'created') {
                    loadUserCreatedJokes();
                } else if (currentTab === 'favorites') {
                    loadFavoriteJokes();
                }
            } else {
                alert('Joke was not in your created jokes list');
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete joke');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Load User Created Jokes
async function loadUserCreatedJokes() {
    if (!window.currentUserToken) {
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    const jokesList = document.getElementById('jokesList');
    jokesList.innerHTML = '<div class="loading">Loading your created jokes...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/created-jokes`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayJokes(data.jokes);
        } else {
            throw new Error('Failed to load created jokes');
        }
    } catch (error) {
        jokesList.innerHTML = `<div class="error">Error loading created jokes: ${error.message}</div>`;
    }
}

// Load Favorite Jokes
async function loadFavoriteJokes() {
    if (!window.currentUserToken) {
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    const jokesList = document.getElementById('jokesList');
    jokesList.innerHTML = '<div class="loading">Loading your favorite jokes...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/favorites`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayJokes(data.jokes);
        } else {
            throw new Error('Failed to load favorite jokes');
        }
    } catch (error) {
        jokesList.innerHTML = `<div class="error">Error loading favorite jokes: ${error.message}</div>`;
    }
}

// Load Liked Jokes
async function loadLikedJokes() {
    if (!window.currentUserToken) {
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    const jokesList = document.getElementById('jokesList');
    jokesList.innerHTML = '<div class="loading">Loading your liked jokes...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/liked-jokes`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayJokes(data.jokes);
        } else {
            throw new Error('Failed to load liked jokes');
        }
    } catch (error) {
        jokesList.innerHTML = `<div class="error">Error loading liked jokes: ${error.message}</div>`;
    }
}

// Load Disliked Jokes
async function loadDislikedJokes() {
    if (!window.currentUserToken) {
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    const jokesList = document.getElementById('jokesList');
    jokesList.innerHTML = '<div class="loading">Loading your disliked jokes...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/disliked-jokes`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayJokes(data.jokes);
        } else {
            throw new Error('Failed to load disliked jokes');
        }
    } catch (error) {
        jokesList.innerHTML = `<div class="error">Error loading disliked jokes: ${error.message}</div>`;
    }
}

// Make functions available globally for auth state changes
window.loadJokes = loadJokes;
window.loadUserCreatedJokes = loadUserCreatedJokes;
window.loadFavoriteJokes = loadFavoriteJokes;
window.loadLikedJokes = loadLikedJokes;
window.loadDislikedJokes = loadDislikedJokes;
window.switchTab = switchTab;
window.refreshCurrentTab = refreshCurrentTab;
window.updateTabsVisibility = updateTabsVisibility;

// Load jokes on page load
window.addEventListener('load', () => {
    loadJokes();
    updateTabsVisibility();
});

