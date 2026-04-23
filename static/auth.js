        const tabButtons = document.querySelectorAll(".tab-btn");
        const loginForm = document.getElementById("login-form");
        const registerForm = document.getElementById("register-form");
        const authMessage = document.getElementById("auth-message");

        function showMessage(text, isError = false) {
            authMessage.textContent = text;
            authMessage.classList.remove("hidden", "error", "success");
            authMessage.classList.add(isError ? "error" : "success");
        }

        tabButtons.forEach((button) => {
            button.addEventListener("click", () => {
                tabButtons.forEach((btn) => btn.classList.remove("active"));
                button.classList.add("active");

                if (button.dataset.tab === "login") {
                    loginForm.classList.remove("hidden");
                    loginForm.classList.add("active-form");
                    registerForm.classList.add("hidden");
                    registerForm.classList.remove("active-form");
                } else {
                    registerForm.classList.remove("hidden");
                    registerForm.classList.add("active-form");
                    loginForm.classList.add("hidden");
                    loginForm.classList.remove("active-form");
                }

                authMessage.classList.add("hidden");
            });
        });

        document.getElementById("register-form").addEventListener("submit", async (event) => {
            event.preventDefault();

            const username = document.getElementById("register-username").value.trim();
            const usernamePattern = /^[A-Za-z0-9_]+$/;
            const email = document.getElementById("register-email").value.trim();
            const password = document.getElementById("register-password").value;

            if(!usernamePattern.test(username)) {
                alert("username can only contain letters, numbers, and underscores.");
                return;
            }

            if (username.length < 3 || username.length > 20) {
                alert("username must be between 3 and 20 characters long.");
                return;
            }
            
            if (password.length < 8 || password.length > 64) {
                alert("password must be at least 8 characters long.");
                return;
            }

           const payload = {username, email, password};

            try {
                const response = await fetch("/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (!response.ok) {
                    showMessage(data.message || "Registration failed.", true);
                    return;
                }

                showMessage(data.message || "Registered successfully. Check your email.");
                event.target.reset();
            } catch {
                showMessage("Something went wrong while registering.", true);
            }
        });

        document.getElementById("login-form").addEventListener("submit", async (event) => {
            event.preventDefault();

            const payload = {
                email: document.getElementById("login-email").value.trim(),
                password: document.getElementById("login-password").value
            };

            try {
                const response = await fetch("/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (!response.ok) {
                    showMessage(data.message || "Login failed.", true);
                    return;
                }

                localStorage.setItem("access_token", data.access_token);
                localStorage.setItem("refresh_token", data.refresh_token);
                localStorage.setItem("username", data.username);
                window.location.href = "/dashboard";
            } catch {
                showMessage("Something went wrong while logging in.", true);
            }
        });