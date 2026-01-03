const API_BASE_URL = 'http://localhost:8000/api';

// Update UI based on login status
function updateAddJokeSection() {
    const addJokeSection = document.getElementById('addJokeSection');
    if (window.currentUserToken) {
        addJokeSection.style.display = 'block';
    } else {
        addJokeSection.style.display = 'none';
    }
}

// Check auth state periodically
setInterval(() => {
    updateAddJokeSection();
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
                document.getElementById(`fav-btn-${jokeId}`).style.display = 'none';
                document.getElementById(`unfav-btn-${jokeId}`).style.display = 'inline-block';
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
                document.getElementById(`fav-btn-${jokeId}`).style.display = 'inline-block';
                document.getElementById(`unfav-btn-${jokeId}`).style.display = 'none';
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
                // Update button states - disable dislike if liked
                const likeBtn = document.getElementById(`like-btn-${jokeId}`);
                const dislikeBtn = document.getElementById(`dislike-btn-${jokeId}`);
                if (likeBtn) likeBtn.style.opacity = '0.6';
                if (dislikeBtn) dislikeBtn.style.opacity = '1';
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
                // Update button states - disable like if disliked
                const likeBtn = document.getElementById(`like-btn-${jokeId}`);
                const dislikeBtn = document.getElementById(`dislike-btn-${jokeId}`);
                if (dislikeBtn) dislikeBtn.style.opacity = '0.6';
                if (likeBtn) likeBtn.style.opacity = '1';
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
                loadJokes(); // Refresh the list
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

// Make loadJokes available globally for auth state changes
window.loadJokes = loadJokes;

// Load jokes on page load
window.addEventListener('load', () => {
    loadJokes();
});

