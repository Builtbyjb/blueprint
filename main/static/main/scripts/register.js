import { setActive } from "./utills.js";

// Set active page
setActive()

// Ensure password and confirmation password match
const confirmPassword = document.querySelector("#confirm-password");
const alertText = document.querySelector("#alert-text");
const alert = document.querySelector("#alert");

confirmPassword.addEventListener("keyup", () => {
    const password = document.querySelector("#password").value;

    if (confirmPassword.value.length === password.length) {
        if (password !== confirmPassword.value) {
            alert.classList.remove('bg-blue-500');
            alert.classList.add('bg-red-500');
            alertText.textContent = "Passwords do not match";
        } else {
            alert.classList.remove('bg-red-500');
            alert.classList.add('bg-blue-500');
            alertText.textContent = 'Passwords match';
        }
    }
});