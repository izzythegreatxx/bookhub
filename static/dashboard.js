// static/dashboard.js
const accessToken = localStorage.getItem("access_token");

if (!accessToken) {
    window.location.href = "/";
}

const booksList = document.getElementById("books-list");
const shelvesList = document.getElementById("shelves-list");
const showAllBooksButton = document.getElementById("show-all-books");

let currentShelfId = null;
let allShelves = [];

function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
    };
}

function handleUnauthorized(response) {
    if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/";
        return true;
    }
    return false;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function fetchBooks() {
    currentShelfId = null;

    const response = await fetch("/books", {
        headers: getAuthHeaders()
    });

    if (handleUnauthorized(response)) {
        return;
    }

    if (!response.ok) {
        console.error("Failed to fetch books");
        return;
    }

    const books = await response.json();
    renderBooks(books);
    renderStats(books);
}

async function fetchShelfBooks(shelfId) {
    currentShelfId = shelfId;

    const response = await fetch(`/shelves/${shelfId}`, {
        headers: getAuthHeaders()
    });

    if (handleUnauthorized(response)) {
        return;
    }

    if (!response.ok) {
        console.error("Failed to fetch shelf books");
        return;
    }

    const books = await response.json();
    renderBooks(books);
    renderStats(books);
}

async function fetchShelves() {
    const response = await fetch("/shelves", {
        headers: getAuthHeaders()
    });

    if (handleUnauthorized(response)) {
        return;
    }

    if (!response.ok) {
        console.error("Failed to fetch shelves");
        return;
    }

    const shelves = await response.json();
    allShelves = shelves;
    renderShelves(shelves);
}

function renderStats(books) {
    document.getElementById("stat-total").textContent = books.length;
    document.getElementById("stat-reading").textContent = books.filter(
        (book) => book.status === "currently_reading"
    ).length;
    document.getElementById("stat-read").textContent = books.filter(
        (book) => book.status === "read"
    ).length;
    document.getElementById("stat-want").textContent = books.filter(
        (book) => book.status === "want_to_read"
    ).length;
}

function buildShelfOptions() {
    if (!allShelves.length) {
        return '<option value="">No shelves yet</option>';
    }

    return `
        <option value="">Select shelf</option>
        ${allShelves
            .map(
                (shelf) =>
                    `<option value="${shelf.id}">${escapeHtml(shelf.name)}</option>`
            )
            .join("")}
    `;
}

function renderBooks(books) {
    booksList.innerHTML = "";

    if (!books.length) {
        booksList.innerHTML = '<div class="empty-state">No books found.</div>';
        return;
    }

    for (const book of books) {
        const card = document.createElement("article");
        card.className = "book-card";

        card.innerHTML = `
            <div class="book-card-top">
                <div>
                    <h3>${escapeHtml(book.title)}</h3>
                    <p>${escapeHtml(book.author)}</p>
                </div>
                <span class="status-pill">${formatStatus(book.status)}</span>
            </div>
            <div class="book-meta">
                <span>Year: ${book.year}</span>
                <span>Rating: ${book.rating ?? "-"}</span>
            </div>
            <div class="progress-row">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${getProgress(book)}%"></div>
                </div>
                <span>${book.pages_read ?? 0}/${book.pages_total ?? 0} pages</span>
            </div>
            <p class="review-text">${escapeHtml(book.review || "No review yet.")}</p>
            <div class="book-actions shelf-actions">
                <select class="shelf-select" data-book-id="${book.id}">
                    ${buildShelfOptions()}
                </select>
                <button class="btn-secondary btn-small add-to-shelf-btn" data-book-id="${book.id}">
                    Add
                </button>
                <button class="btn-secondary btn-small delete-book-btn" data-id="${book.id}">
                    Delete
                </button>
            </div>
        `;

        const shelfSelect = card.querySelector(".shelf-select");
        const addToShelfButton = card.querySelector(".add-to-shelf-btn");
        const deleteButton = card.querySelector(".delete-book-btn");

        addToShelfButton.addEventListener("click", async () => {
            const shelfId = shelfSelect.value;

            if (!shelfId) {
                alert("Please select a shelf.");
                return;
            }

            await addBookToShelf(shelfId, book.id);
        });

        deleteButton.addEventListener("click", () => deleteBook(book.id));

        booksList.appendChild(card);
    }
}

function renderShelves(shelves) {
    shelvesList.innerHTML = "";

    if (!shelves.length) {
        shelvesList.innerHTML = '<li class="empty-line">No shelves created yet.</li>';
        return;
    }

    for (const shelf of shelves) {
        const item = document.createElement("li");
        item.className = "simple-list-item";

        const button = document.createElement("button");
        button.className = "shelf-button";
        button.dataset.id = shelf.id;
        button.textContent = shelf.name;
        button.addEventListener("click", () => fetchShelfBooks(shelf.id));

        item.appendChild(button);
        shelvesList.appendChild(item);
    }
}

function formatStatus(status) {
    if (status === "want_to_read") return "Want to Read";
    if (status === "currently_reading") return "Currently Reading";
    return "Read";
}

function getProgress(book) {
    if (!book.pages_total || book.pages_total <= 0) {
        return 0;
    }

    return Math.min(100, Math.round((book.pages_read / book.pages_total) * 100));
}

async function addBookToShelf(shelfId, bookId) {
    const response = await fetch(`/shelves/${shelfId}/books/${bookId}`, {
        method: "POST",
        headers: getAuthHeaders()
    });

    const data = await response.json().catch(() => ({}));

    if (handleUnauthorized(response)) {
        return;
    }

    if (!response.ok) {
        alert(data.message || data.error || "Failed to add book to shelf");
        return;
    }

    alert("Book added to shelf");

    if (currentShelfId && Number(currentShelfId) === Number(shelfId)) {
        fetchShelfBooks(shelfId);
    }
}

async function deleteBook(bookId) {
    const response = await fetch(`/books/${bookId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
    });

    if (handleUnauthorized(response)) {
        return;
    }

    if (!response.ok) {
        console.error("Failed to delete book");
        return;
    }

    if (currentShelfId) {
        fetchShelfBooks(currentShelfId);
    } else {
        fetchBooks();
    }
}

document.getElementById("add-book-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(event.target);

    const payload = {
        title: formData.get("title").trim(),
        author: formData.get("author").trim(),
        year: Number(formData.get("year")),
        status: formData.get("status"),
        pages_read: formData.get("pages_read") ? Number(formData.get("pages_read")) : 0
    };

    const pagesTotal = formData.get("pages_total");
    const rating = formData.get("rating");
    const review = formData.get("review");

    if (pagesTotal) {
        payload.pages_total = Number(pagesTotal);
    }

    if (rating) {
        payload.rating = Number(rating);
    }

    if (review && review.trim()) {
        payload.review = review.trim();
    }

    const response = await fetch("/books", {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));

    if (handleUnauthorized(response)) {
        return;
    }

    if (!response.ok) {
        console.error("Add book failed:", data);
        alert(data.message || JSON.stringify(data));
        return;
    }

    event.target.reset();
    fetchBooks();
});

document.getElementById("create-shelf-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(event.target);
    const payload = { name: formData.get("name").trim() };

    const response = await fetch("/shelves", {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));

    if (handleUnauthorized(response)) {
        return;
    }

    if (!response.ok) {
        alert(data.message || JSON.stringify(data));
        return;
    }

    event.target.reset();
    await fetchShelves();
    fetchBooks();
});

if (showAllBooksButton) {
    showAllBooksButton.addEventListener("click", fetchBooks);
}

document.getElementById("logout-btn").addEventListener("click", async () => {
    await fetch("/auth/logout", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${localStorage.getItem("access_token")}`
        }
    });

    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/";
});

async function initializeDashboard() {
    await fetchShelves();
    await fetchBooks();
}

initializeDashboard();