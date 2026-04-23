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

async function editBook(bookId) {
    // Fetch current book data
    const response = await fetch(`/books/${bookId}`, { headers: getAuthHeaders() });
    if (!response.ok) {
        alert("Failed to fetch book info");
        return;
    }
    const book = await response.json();

    // Human-readable status map
    const statusMap = {
        "Want to Read": "want_to_read",
        "Currently Reading": "currently_reading",
        "Read": "read"
    };

    // Prompt user for new values, prefilled with current values
    const title = prompt("Edit title:", book.title)?.trim() || book.title;
    const author = prompt("Edit author:", book.author)?.trim() || book.author;
    
    const yearInput = prompt("Edit year:", book.year);
    const year = yearInput !== null && yearInput !== "" ? parseInt(yearInput, 10) : book.year;

    const humanStatusInput = prompt(
        "Edit status (Want to Read, Currently Reading, Read):",
        book.status.replace(/_/g, " ")
    );
    const humanStatus = humanStatusInput !== null && humanStatusInput !== "" ? humanStatusInput : book.status.replace(/_/g, " ");
    const status = statusMap[humanStatus] || book.status;

    const pagesTotalInput = prompt("Edit total pages:", book.pages_total || 0);
    const pages_total = pagesTotalInput !== null && pagesTotalInput !== "" ? parseInt(pagesTotalInput, 10) : book.pages_total;

    const pagesReadInput = prompt("Edit pages read:", book.pages_read || 0);
    const pages_read = pagesReadInput !== null && pagesReadInput !== "" ? parseInt(pagesReadInput, 10) : book.pages_read;

    const ratingInput = prompt("Edit rating (1-5):", book.rating || 0);
    const rating = ratingInput !== null && ratingInput !== "" ? parseInt(ratingInput, 10) : book.rating;

    const reviewInput = prompt("Edit review:", book.review || "");
    const review = reviewInput !== null && reviewInput !== "" ? reviewInput.trim() : book.review;

    // Build payload only with valid values
    const payload = {};
    if (title) payload.title = title;
    if (author) payload.author = author;
    if (!isNaN(year)) payload.year = year;
    if (["want_to_read","currently_reading","read"].includes(status)) payload.status = status;
    if (!isNaN(pages_total) && pages_total >= 0) payload.pages_total = pages_total;
    if (!isNaN(pages_read) && pages_read >= 0) payload.pages_read = pages_read;
    if (!isNaN(rating) && rating >= 1 && rating <= 5) payload.rating = rating;
    if (review) payload.review = review;

    // PATCH request to backend
    const updateResponse = await fetch(`/books/${bookId}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });

    const data = await updateResponse.json().catch(() => ({}));
    if (!updateResponse.ok) {
        console.log(data); // Shows exact backend validation errors
        alert(data.message || JSON.stringify(data) || "Failed to update book");
        return;
    }

    fetchBooks(); // Refresh the list after successful edit
}
function renderStats(books) {
    const bookArray = Array.isArray(books) ? books : [];
    document.getElementById("stat-total").textContent = bookArray.length;
    document.getElementById("stat-reading").textContent = bookArray.filter(
        (book) => book.status === "currently_reading"
    ).length;
    document.getElementById("stat-read").textContent = bookArray.filter(
        (book) => book.status === "read"
    ).length;
    document.getElementById("stat-want").textContent = bookArray.filter(
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

function renderBooks(books, inShelf = false, container = null) {
    const booksList = container || document.getElementById("books-list");
    
    const oldCards = booksList.querySelectorAll(".book-card");
    oldCards.forEach(card => card.remove());

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
        `;

        // Only add shelf select and buttons if not viewing inside a shelf
        if (!inShelf) {
            const actionsDiv = document.createElement("div");
            actionsDiv.className = "book-actions shelf-actions";

            actionsDiv.innerHTML = `
                <select class="shelf-select" data-book-id="${book.id}">
                    ${buildShelfOptions()}
                </select>
                <button class="btn-secondary btn-small add-to-shelf-btn" data-book-id="${book.id}">Add</button>
                <button class="btn-secondary btn-small edit-book-btn" data-book-id="${book.id}">Edit</button>
                <button class="btn-secondary btn-small delete-book-btn" data-id="${book.id}">Delete</button>
            `;

            const shelfSelect = actionsDiv.querySelector(".shelf-select");
            const addToShelfButton = actionsDiv.querySelector(".add-to-shelf-btn");
            const editButton = actionsDiv.querySelector(".edit-book-btn");
            const deleteButton = actionsDiv.querySelector(".delete-book-btn");

            addToShelfButton.addEventListener("click", async () => {
                const shelfId = shelfSelect.value;
                if (!shelfId) {
                    alert("Please select a shelf.");
                    return;
                }
                await addBookToShelf(shelfId, book.id);
            });

            editButton.addEventListener("click", () => editBook(book.id));
            deleteButton.addEventListener("click", () => deleteBook(book.id));

            card.appendChild(actionsDiv);
        }

        booksList.appendChild(card);
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

const sidebar = document.querySelector('.sidebar-nav');
const offset = 160; // initial offset from top

window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY;
    sidebar.style.transform = `translateY(${offset + scrollTop}px)`;
});

const dashboardButton = document.getElementById("dashboard-btn");

dashboardButton.addEventListener("click", async () => {
    try {
        // Reset the main page header
        const pageHeader = document.querySelector("main .topbar h1");
        if (pageHeader) {
            pageHeader.textContent = "BookHub Dashboard";
        }

        // Container for description
        const main = document.getElementById("books-list");
        main.innerHTML = "";

        // Description section at the top of the dashboard
        const description = document.createElement("p");
        description.className = "dashboard-description";
        description.textContent = "Welcome to BookHub! Keep track of your books, manage your reading shelves, and review your favorites.";

        // Separate div for books so renderBooks doesn't overwrite description
        const booksContainer = document.createElement("div");
        booksContainer.id = "books-container";

        main.appendChild(description);

    } catch (err) {
        console.error(err);
        alert("Failed to load dashboard");
    }
});



const booksButton = document.getElementById("books-btn");

booksButton.addEventListener("click", async () => {
    try {
        const response = await fetch("/books", { headers: getAuthHeaders() });
        if (!response.ok) {
            alert("Failed to fetch books");
            return;
        }

        setPageDescription("Here are your books! You can edit details, add them to shelves, or review your reading progress.");

        const books = await response.json();

        // Reset the main page header to default
        const pageHeader = document.querySelector("main .topbar h1");
        if (pageHeader) {
            pageHeader.textContent = "Your Books";
        }

        // Render all books in the main container
        renderBooks(books, false, document.getElementById("books-list")); 
    } catch (err) {
        console.error(err);
        alert("Failed to fetch books");
    }
});

// Sidebar Shelves button
const shelvesButton = document.querySelector("#shelves-btn"); // adjust selector if needed

shelvesButton.addEventListener("click", async () => {
    // Reset the main page header to Shelves view
    const pageHeader = document.querySelector("main .topbar h1");
    if (pageHeader) {
        pageHeader.textContent = "Your Shelves";
    }

    // Set a description for the Shelves page
    setPageDescription("Here are your book shelves! Click a shelf to view the books inside.");

    try {
        // Fetch all shelves
        const response = await fetch("/shelves", { headers: getAuthHeaders() });
        if (!response.ok) {
            alert("Failed to fetch shelves");
            return;
        }
        const shelves = await response.json();

        // Render shelves
        renderShelves(shelves);
    } catch (err) {
        console.error(err);
        alert("An error occurred while fetching shelves.");
    }
});

// Function to render shelves list in main panel
function renderShelves(shelves) {
    const main = document.getElementById("books-list");

    if (!shelves.length) {
        main.innerHTML = '<div class="empty-state">No shelves found.</div>';
        return;
    }

    shelves.forEach(shelf => {
        const div = document.createElement("div");
        div.className = "shelf-card";
        div.textContent = shelf.name;
        div.style.cursor = "pointer";
        div.style.padding = "10px";
        div.style.border = "1px solid #ddd";
        div.style.borderRadius = "8px";
        div.style.marginBottom = "8px";
        div.style.backgroundColor = "#fff";
        div.style.boxShadow = "0 2px 5px rgba(0,0,0,0.05)";

        // Click to load books in this shelf
        div.addEventListener("click", async () => {
            try {
                const res = await fetch(`/shelves/${shelf.id}`, { headers: getAuthHeaders() });
                if (!res.ok) {
                    alert("Failed to fetch books for this shelf");
                    return;
                }
                const books = await res.json();

                // Update the main page header to the shelf name
                const pageHeader = document.querySelector("main .topbar h1");
                if (pageHeader) {
                    pageHeader.textContent = shelf.name;
                }

                // Clear previous books below header
                const booksList = document.getElementById("books-list");
                booksList.innerHTML = "";

                // Render books below the header
                renderBooks(books, true); // 'true' hides Add to Shelf dropdown
            } catch (err) {
                console.error(err);
                alert("Error fetching books for shelf");
            }
        });

        main.appendChild(div);
    });
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

function setPageDescription(text) {
    const main = document.getElementById("books-list");

    // Clear previous content
    main.innerHTML = "";

    // Create and append description
    const description = document.createElement("p");
    description.className = "page-description"; 
    description.textContent = text;
    main.appendChild(description);
}

async function initializeDashboard() {
    // Set the main header
    const pageHeader = document.querySelector("main .topbar h1");
    if (pageHeader) {
        pageHeader.textContent = "BookHub Dashboard";
    }

    // Main content container
    const main = document.getElementById("books-list");
    main.innerHTML = "";

    // Add welcome description
    const description = document.createElement("p");
    description.className = "page-description";
    description.textContent = "Welcome to BookHub! Keep track of your books, manage your reading shelves, and review your favorites.";
    main.appendChild(description);
}

initializeDashboard();