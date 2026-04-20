let accessToken = null;
let refreshToken = null;

async function register() {
    const res = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            email: document.getElementById("regEmail").value,
            password: document.getElementById("regPassword").value
        })
    });

    const data = await res.json();

    if (!res.ok) {
        alert("Registration failed: " + JSON.stringify(data));
        return;
    }

    alert("Registration successful. You can now log in.");
}

async function login() {
    const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            email: document.getElementById("email").value,
            password: document.getElementById("password").value
        })
    });

    const data = await res.json();

    if (!res.ok) {
        alert("Login failed: " + JSON.stringify(data));
        return;
    }

    // Save tokens to localStorage so dashboard.js can use them
    localStorage.setItem("accessToken", data.access_token);
    localStorage.setItem("refreshToken", data.refresh_token);

    window.location.href = "/dashboard";
}
