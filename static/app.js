const API_BASE_URL = 'http://localhost:8000/api';

// Track current tab
let currentTab = 'all';
window.currentTab = currentTab;

// Update UI based on login status
function updateAddJokeSection() {
    const addJokeSection = document.getElementById('addJokeSection');
    const getJokesSection = document.getElementById('getJokesSection');
    if (window.currentUserToken) {
        addJokeSection.style.display = 'block';
        getJokesSection.style.display = 'block';
        // Show tabs for logged in users
        updateTabsVisibility();
    } else {
        addJokeSection.style.display = 'none';
        getJokesSection.style.display = 'none';
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
                age_range: []
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
            await displayJokes(data.jokes);
        } else {
            throw new Error('Failed to load jokes');
        }
    } catch (error) {
        jokesList.innerHTML = `<div class="error">Error loading jokes: ${error.message}</div>`;
    }
}

// Display Jokes
async function displayJokes(jokes, container = null) {
    const targetContainer = container || document.getElementById('jokesList');
    
    if (jokes.length === 0) {
        targetContainer.innerHTML = '<div class="no-jokes">No jokes yet. Be the first to add one!</div>';
        return;
    }
    
    // Get user's liked and disliked jokes if logged in
    let likedJokeIds = new Set();
    let dislikedJokeIds = new Set();
    let favoriteJokeIds = new Set();
    
    if (window.currentUserToken && window.firebaseAuth && window.firebaseAuth.currentUser) {
        try {
            const userId = window.firebaseAuth.currentUser.uid;
            const [likedResponse, dislikedResponse, favoritesResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/users/${userId}/liked-jokes`, {
                    headers: { 'Authorization': `Bearer ${window.currentUserToken}` }
                }).catch(() => null),
                fetch(`${API_BASE_URL}/users/${userId}/disliked-jokes`, {
                    headers: { 'Authorization': `Bearer ${window.currentUserToken}` }
                }).catch(() => null),
                fetch(`${API_BASE_URL}/users/${userId}/favorites`, {
                    headers: { 'Authorization': `Bearer ${window.currentUserToken}` }
                }).catch(() => null)
            ]);
            
            if (likedResponse && likedResponse.ok) {
                const likedData = await likedResponse.json();
                likedJokeIds = new Set(likedData.jokes.map(j => j.joke_id));
            }
            
            if (dislikedResponse && dislikedResponse.ok) {
                const dislikedData = await dislikedResponse.json();
                dislikedJokeIds = new Set(dislikedData.jokes.map(j => j.joke_id));
            }
            
            if (favoritesResponse && favoritesResponse.ok) {
                const favoritesData = await favoritesResponse.json();
                favoriteJokeIds = new Set(favoritesData.jokes.map(j => j.joke_id));
            }
        } catch (error) {
            console.error('Error fetching user preferences:', error);
        }
    }
    
    targetContainer.innerHTML = jokes.map(joke => {
        const isLiked = likedJokeIds.has(joke.joke_id);
        const isDisliked = dislikedJokeIds.has(joke.joke_id);
        const isFavorite = favoriteJokeIds.has(joke.joke_id);
        
        return `
        <div class="joke-card">
            <div class="joke-setup">${escapeHtml(joke.joke_setup || '')}</div>
            <div class="joke-punchline">${escapeHtml(joke.joke_punchline || '')}</div>
            ${joke.joke_content ? `<div class="joke-content">${escapeHtml(joke.joke_content)}</div>` : ''}
            <div class="joke-meta">
                <span class="joke-author">By: ${escapeHtml(joke.creator_id || 'Anonymous')}</span>
                ${joke.created_at ? `<span class="joke-date">${formatDate(joke.created_at)}</span>` : ''}
            </div>
            <div class="joke-actions">
                <button onclick="handlePlayAudio('${joke.joke_id}')" class="btn-play-audio" title="Play audio" id="play-audio-btn-${joke.joke_id}">
                    🔊 Play Audio
                </button>
            </div>
            ${window.currentUserToken ? `
                <div class="joke-actions">
                    <button onclick="handleAddToFavorites('${joke.joke_id}')" class="btn-favorite" title="Add to favorites" id="fav-btn-${joke.joke_id}" style="display: ${isFavorite ? 'none' : 'inline-block'};">
                        ⭐ Favorite
                    </button>
                    <button onclick="handleDeleteFromFavorites('${joke.joke_id}')" class="btn-unfavorite" title="Remove from favorites" id="unfav-btn-${joke.joke_id}" style="display: ${isFavorite ? 'inline-block' : 'none'};">
                        ❌ Unfavorite
                    </button>
                    <button onclick="handleLikeJoke('${joke.joke_id}')" class="btn-like ${isLiked ? '' : ''}" title="Like this joke" id="like-btn-${joke.joke_id}" style="display: ${isLiked ? 'none' : 'inline-block'};">
                        👍 Like
                    </button>
                    <button onclick="handleDeleteFromLikeJoke('${joke.joke_id}')" class="btn-unlike ${isLiked ? 'active' : ''}" title="Remove like" id="unlike-btn-${joke.joke_id}" style="display: ${isLiked ? 'inline-block' : 'none'};">
                        ❌ Unlike
                    </button>
                    <button onclick="handleDislikeJoke('${joke.joke_id}')" class="btn-dislike ${isDisliked ? '' : ''}" title="Dislike this joke" id="dislike-btn-${joke.joke_id}" style="display: ${isDisliked ? 'none' : 'inline-block'};">
                        👎 Dislike
                    </button>
                    <button onclick="handleDeleteFromDislikeJoke('${joke.joke_id}')" class="btn-undislike ${isDisliked ? 'active' : ''}" title="Remove dislike" id="undislike-btn-${joke.joke_id}" style="display: ${isDisliked ? 'inline-block' : 'none'};">
                        ❌ Undislike
                    </button>
                    ${joke.creator_id === (window.firebaseAuth?.currentUser?.uid || '') ? `
                        <button onclick="handleDeleteCreatedJoke('${joke.joke_id}')" class="btn-delete" title="Delete this joke">
                            🗑️ Delete
                        </button>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `;
    }).join('');
}

// Play Audio Handler
async function handlePlayAudio(jokeId) {
    const playBtn = document.getElementById(`play-audio-btn-${jokeId}`);
    
    // Disable button while loading
    if (playBtn) {
        playBtn.disabled = true;
        playBtn.textContent = '⏳ Loading...';
    }
    
    try {
        // Call backend API to get audio URL
        const response = await fetch(`${API_BASE_URL}/jokes/${jokeId}/audio`);
        
        if (!response.ok) {
            throw new Error(`Failed to get audio: ${response.statusText}`);
        }
        
        const data = await response.json();
        const audioUrl = data.audio_url;
        
        if (!audioUrl) {
            throw new Error('No audio URL returned');
        }
        
        // Create and play audio
        const audio = new Audio(audioUrl);
        
        // Handle audio events
        audio.onloadstart = () => {
            if (playBtn) {
                playBtn.textContent = '⏸️ Playing...';
            }
        };
        
        audio.onended = () => {
            if (playBtn) {
                playBtn.disabled = false;
                playBtn.textContent = '🔊 Play Audio';
            }
        };
        
        audio.onerror = (error) => {
            console.error('Error playing audio:', error);
            alert('Failed to play audio. Please try again.');
            if (playBtn) {
                playBtn.disabled = false;
                playBtn.textContent = '🔊 Play Audio';
            }
        };
        
        // Play the audio
        await audio.play();
        
    } catch (error) {
        console.error('Error getting/playing audio:', error);
        alert(`Failed to play audio: ${error.message}`);
        if (playBtn) {
            playBtn.disabled = false;
            playBtn.textContent = '🔊 Play Audio';
        }
    }
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
    const likeBtn = document.getElementById(`like-btn-${jokeId}`);
    const unlikeBtn = document.getElementById(`unlike-btn-${jokeId}`);
    const dislikeBtn = document.getElementById(`dislike-btn-${jokeId}`);
    const undislikeBtn = document.getElementById(`undislike-btn-${jokeId}`);
    
    // Update UI immediately for instant feedback - toggle buttons and add active class
    // When clicking Like: hide Like button, show Unlike button
    if (likeBtn) {
        likeBtn.removeAttribute('style');
        likeBtn.style.display = 'none';
        likeBtn.classList.remove('active');
    }
    if (unlikeBtn) {
        unlikeBtn.removeAttribute('style');
        unlikeBtn.style.display = 'inline-block';
        unlikeBtn.classList.add('active');
    }
    // Hide dislike buttons when liking (show normal dislike, hide undislike)
    if (dislikeBtn) {
        dislikeBtn.removeAttribute('style');
        dislikeBtn.style.display = 'inline-block';
        dislikeBtn.classList.remove('active');
    }
    if (undislikeBtn) {
        undislikeBtn.removeAttribute('style');
        undislikeBtn.style.display = 'none';
        undislikeBtn.classList.remove('active');
    }
    
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
                // Success - buttons already updated, no need to refresh
                // Only refresh if we're on a specific tab that needs updating
                if (currentTab === 'liked') {
                    loadLikedJokes();
                } else if (currentTab === 'disliked') {
                    loadDislikedJokes();
                }
            } else {
                // Revert on failure
                if (likeBtn) {
                    likeBtn.removeAttribute('style');
                    likeBtn.style.display = 'inline-block';
                    likeBtn.classList.remove('active');
                }
                if (unlikeBtn) {
                    unlikeBtn.removeAttribute('style');
                    unlikeBtn.style.display = 'none';
                    unlikeBtn.classList.remove('active');
                }
            }
        } else {
            const error = await response.json();
            // Revert on error
            if (likeBtn) {
                likeBtn.removeAttribute('style');
                likeBtn.style.display = 'inline-block';
                likeBtn.classList.remove('active');
            }
            if (unlikeBtn) {
                unlikeBtn.removeAttribute('style');
                unlikeBtn.style.display = 'none';
                unlikeBtn.classList.remove('active');
            }
            throw new Error(error.detail || 'Failed to like joke');
        }
    } catch (error) {
        // Revert on error
        if (likeBtn) {
            likeBtn.setAttribute('style', 'display: inline-block !important');
            likeBtn.classList.remove('active');
        }
        if (unlikeBtn) {
            unlikeBtn.setAttribute('style', 'display: none !important');
            unlikeBtn.classList.remove('active');
        }
        alert('Error: ' + error.message);
    }
}

// Handle Unlike Joke
async function handleDeleteFromLikeJoke(jokeId) {
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    const likeBtn = document.getElementById(`like-btn-${jokeId}`);
    const unlikeBtn = document.getElementById(`unlike-btn-${jokeId}`);
    
    // Update UI immediately for instant feedback - toggle buttons and remove active class
    if (likeBtn) {
        likeBtn.removeAttribute('style');
        likeBtn.style.display = 'inline-block';
        likeBtn.classList.remove('active');
    }
    if (unlikeBtn) {
        unlikeBtn.removeAttribute('style');
        unlikeBtn.style.display = 'none';
        unlikeBtn.classList.remove('active');
    }
    
    try {
        // Unlike is done by disliking (which removes from like history)
        const response = await fetch(`${API_BASE_URL}/users/${userId}/dislike-history/${jokeId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Success - buttons already updated
                // Only refresh if we're on a specific tab that needs updating
                if (currentTab === 'liked') {
                    loadLikedJokes();
                } else if (currentTab === 'disliked') {
                    loadDislikedJokes();
                }
            } else {
                // Revert on failure
                if (likeBtn) {
                    likeBtn.removeAttribute('style');
                    likeBtn.style.display = 'none';
                    likeBtn.classList.remove('active');
                }
                if (unlikeBtn) {
                    unlikeBtn.removeAttribute('style');
                    unlikeBtn.style.display = 'inline-block';
                    unlikeBtn.classList.add('active');
                }
            }
        } else {
            const error = await response.json();
            // Revert on error
            if (likeBtn) {
                likeBtn.removeAttribute('style');
                likeBtn.style.display = 'none';
                likeBtn.classList.remove('active');
            }
            if (unlikeBtn) {
                unlikeBtn.removeAttribute('style');
                unlikeBtn.style.display = 'inline-block';
                unlikeBtn.classList.add('active');
            }
            throw new Error(error.detail || 'Failed to unlike joke');
        }
    } catch (error) {
        // Revert on error
        if (likeBtn) {
            likeBtn.setAttribute('style', 'display: none !important');
            likeBtn.classList.remove('active');
        }
        if (unlikeBtn) {
            unlikeBtn.setAttribute('style', 'display: inline-block !important');
            unlikeBtn.classList.add('active');
        }
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
    const likeBtn = document.getElementById(`like-btn-${jokeId}`);
    const unlikeBtn = document.getElementById(`unlike-btn-${jokeId}`);
    const dislikeBtn = document.getElementById(`dislike-btn-${jokeId}`);
    const undislikeBtn = document.getElementById(`undislike-btn-${jokeId}`);
    
    // Update UI immediately for instant feedback - toggle buttons and add active class
    if (dislikeBtn) {
        dislikeBtn.removeAttribute('style');
        dislikeBtn.style.display = 'none';
        dislikeBtn.classList.remove('active');
    }
    if (undislikeBtn) {
        undislikeBtn.removeAttribute('style');
        undislikeBtn.style.display = 'inline-block';
        undislikeBtn.classList.add('active');
    }
    if (likeBtn) {
        likeBtn.removeAttribute('style');
        likeBtn.style.display = 'inline-block';
        likeBtn.classList.remove('active');
    }
    if (unlikeBtn) {
        unlikeBtn.removeAttribute('style');
        unlikeBtn.style.display = 'none';
        unlikeBtn.classList.remove('active');
    }
    
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
                // Success - buttons already updated, no need to refresh
                // Only refresh if we're on a specific tab that needs updating
                if (currentTab === 'liked') {
                    loadLikedJokes();
                } else if (currentTab === 'disliked') {
                    loadDislikedJokes();
                }
            } else {
                // Revert on failure
                if (dislikeBtn) {
                    dislikeBtn.removeAttribute('style');
                    dislikeBtn.style.display = 'inline-block';
                    dislikeBtn.classList.remove('active');
                }
                if (undislikeBtn) {
                    undislikeBtn.removeAttribute('style');
                    undislikeBtn.style.display = 'none';
                    undislikeBtn.classList.remove('active');
                }
            }
        } else {
            const error = await response.json();
            // Revert on error
            if (dislikeBtn) {
                dislikeBtn.removeAttribute('style');
                dislikeBtn.style.display = 'inline-block';
                dislikeBtn.classList.remove('active');
            }
            if (undislikeBtn) {
                undislikeBtn.removeAttribute('style');
                undislikeBtn.style.display = 'none';
                undislikeBtn.classList.remove('active');
            }
            throw new Error(error.detail || 'Failed to dislike joke');
        }
    } catch (error) {
        // Revert on error
        if (dislikeBtn) {
            dislikeBtn.setAttribute('style', 'display: inline-block !important');
            dislikeBtn.classList.remove('active');
        }
        if (undislikeBtn) {
            undislikeBtn.setAttribute('style', 'display: none !important');
            undislikeBtn.classList.remove('active');
        }
        alert('Error: ' + error.message);
    }
}

// Handle Undislike Joke
async function handleDeleteFromDislikeJoke(jokeId) {
    if (!window.currentUserToken) {
        alert('Please login first');
        return;
    }
    
    if (!window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    const dislikeBtn = document.getElementById(`dislike-btn-${jokeId}`);
    const undislikeBtn = document.getElementById(`undislike-btn-${jokeId}`);
    
    // Update UI immediately for instant feedback - toggle buttons and remove active class
    if (dislikeBtn) {
        dislikeBtn.removeAttribute('style');
        dislikeBtn.style.display = 'inline-block';
        dislikeBtn.classList.remove('active');
    }
    if (undislikeBtn) {
        undislikeBtn.removeAttribute('style');
        undislikeBtn.style.display = 'none';
        undislikeBtn.classList.remove('active');
    }
    
    try {
        // Undislike is done by liking (which removes from dislike history)
        const response = await fetch(`${API_BASE_URL}/users/${userId}/like-history/${jokeId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.currentUserToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Success - buttons already updated
                // Only refresh if we're on a specific tab that needs updating
                if (currentTab === 'liked') {
                    loadLikedJokes();
                } else if (currentTab === 'disliked') {
                    loadDislikedJokes();
                }
            } else {
                // Revert on failure
                if (dislikeBtn) {
                    dislikeBtn.removeAttribute('style');
                    dislikeBtn.style.display = 'none';
                    dislikeBtn.classList.remove('active');
                }
                if (undislikeBtn) {
                    undislikeBtn.removeAttribute('style');
                    undislikeBtn.style.display = 'inline-block';
                    undislikeBtn.classList.add('active');
                }
            }
        } else {
            const error = await response.json();
            // Revert on error
            if (dislikeBtn) {
                dislikeBtn.removeAttribute('style');
                dislikeBtn.style.display = 'none';
                dislikeBtn.classList.remove('active');
            }
            if (undislikeBtn) {
                undislikeBtn.removeAttribute('style');
                undislikeBtn.style.display = 'inline-block';
                undislikeBtn.classList.add('active');
            }
            throw new Error(error.detail || 'Failed to undislike joke');
        }
    } catch (error) {
        // Revert on error
        if (dislikeBtn) {
            dislikeBtn.setAttribute('style', 'display: none !important');
            dislikeBtn.classList.remove('active');
        }
        if (undislikeBtn) {
            undislikeBtn.setAttribute('style', 'display: inline-block !important');
            undislikeBtn.classList.add('active');
        }
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
            await displayJokes(data.jokes);
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
            await displayJokes(data.jokes);
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
            await displayJokes(data.jokes);
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
            await displayJokes(data.jokes);
        } else {
            throw new Error('Failed to load disliked jokes');
        }
    } catch (error) {
        jokesList.innerHTML = `<div class="error">Error loading disliked jokes: ${error.message}</div>`;
    }
}

// Handle Get Jokes
async function handleGetJokes(event) {
    event.preventDefault();
    
    if (!window.currentUserToken || !window.firebaseAuth || !window.firebaseAuth.currentUser) {
        alert('Please login first');
        return;
    }
    
    const ageRange = document.getElementById('ageRange').value.trim();
    const scenario = document.getElementById('scenario').value.trim();
    const errorDiv = document.getElementById('getJokesError');
    const successDiv = document.getElementById('getJokesSuccess');
    const resultsDiv = document.getElementById('getJokesResults');
    const jokesListDiv = document.getElementById('getJokesList');
    
    errorDiv.textContent = '';
    successDiv.textContent = '';
    resultsDiv.style.display = 'none';
    jokesListDiv.innerHTML = '<div class="loading">Getting personalized jokes...</div>';
    
    if (!ageRange || !scenario) {
        errorDiv.textContent = 'Please enter both age range and scenario';
        return;
    }
    
    const userId = window.firebaseAuth.currentUser.uid;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/jokes/get`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.currentUserToken}`
            },
            body: JSON.stringify({
                age_range: ageRange,
                scenario: scenario
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            successDiv.textContent = `Found ${data.jokes.length} personalized jokes!`;
            resultsDiv.style.display = 'block';
            
            // Display the jokes
            if (data.jokes && data.jokes.length > 0) {
                await displayJokes(data.jokes, jokesListDiv);
            } else {
                jokesListDiv.innerHTML = '<div class="no-jokes">No jokes found. Try different age range or scenario.</div>';
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get jokes');
        }
    } catch (error) {
        console.error('Get jokes error:', error);
        errorDiv.textContent = 'Error: ' + error.message;
        resultsDiv.style.display = 'none';
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
window.handleGetJokes = handleGetJokes;
window.handlePlayAudio = handlePlayAudio;

// Note: loadJokes() is called by onAuthStateChanged in index.html
// which handles both initial load and auth state changes

