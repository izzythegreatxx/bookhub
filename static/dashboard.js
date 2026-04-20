let accessToken = localStorage.getItem("accessToken");

if (!accessToken) {
    window.location.href = "/";
}

async function loadBooks() {
    const res = await fetch("/books", {
        headers: { "Authorization": "Bearer " + accessToken }
    });

    const data = await res.json();

    if (!res.ok) {
        alert("Error loading books: " + JSON.stringify(data));
        return;
    }

    const container = document.getElementById("books");
    container.innerHTML = "";

    data.forEach(book => {
        const div = document.createElement("div");
        div.className = "book";
        div.innerHTML = `
            <strong>${book.title}</strong> by ${book.author} (${book.year})<br>
            Status: ${book.status}<br>
            Rating: ${book.rating || "N/A"}<br>
            <button onclick="deleteBook(${book.id})">Delete</button>
        `;
        container.appendChild(div);
    });
}

async function addBook() {
    const res = await fetch("/books", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + accessToken
        },
        body: JSON.stringify({
            title: document.getElementById("title").value,
            author: document.getElementById("author").value,
            year: parseInt(document.getElementById("year").value),
            status: document.getElementById("status").value
        })
    });

    const data = await res.json();

    if (!res.ok) {
        alert("Error adding book: " + JSON.stringify(data));
        return;
    }

    loadBooks();
}

async function deleteBook(id) {
    const res = await fetch(`/books/${id}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + accessToken }
    });

    loadBooks();
}

function logout() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    window.location.href = "/";
}

loadBooks();
