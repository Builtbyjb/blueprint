// Ensure password and confirmation password match
const confirmation = document.querySelector("#confirmation");
const msg = document.querySelector("#regMsg");

confirmation.addEventListener("keyup", () => {
    const password = document.querySelector("#passwordReg").value;

    if (password !== confirmation.value) {
        msg.classList.add("alert", "alert-danger");
        msg.innerText = "Passwords do not match";
    } else {
        msg.classList.remove("alert", "alert-danger");
        msg.classList.add("alert", "alert-success");
        msg.innerText = "Passwords Match";
    }
});