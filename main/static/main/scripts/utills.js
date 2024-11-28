// Get csrftoken
const cookie = document.cookie.split("=");
const csrftoken = cookie[1];

// Set active page
export function setActive() {
    window.onload = () => {
        const path = window.location.pathname;

        if (path === "/") {
            const link = document.querySelector(`#project-link`);
            link.classList.add("active");
        } else {
            const link = document.querySelector(`#${path.slice(1)}-link`);
            link.classList.add("active");
        }
    };

}

export async function sendGetRequests(url, id) {
    try {
        const res = await fetch(`/${url}/${id}`, {
            method: "GET",
            headers: { "X-CSRFToken": csrftoken },
            mode: "same-origin",
        });
        const response = await res.json();
        return response;
    } catch (error) {
        console.error(`GET request error: ${error}`);
    }
}

export async function sendDeleteRequests(url, id) {
    try {
        const res = await fetch(`/${url}/${id}`, {
            method: "DELETE",
            headers: { "X-CSRFToken": csrftoken },
            mode: "same-origin",
        });
        const response = await res.json();
        return response;
    } catch (error) {
        console.error(`DELETE request error: ${error}`);
    }
}

export async function sendPostRequests(url, formData) {
    try {
        const res = await fetch(`/${url}`, {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken },
            mode: "same-origin",
            body: formData,
        });
        const response = await res.json();
        return response;
    } catch (error) {
        console.error(`POST request error: ${error}`);
    }
}

export async function sendPutRequests(url, id, data) {
    try {
        const res = await fetch(`/${url}/${id}`, {
            method: "PUT",
            headers: { "X-CSRFToken": csrftoken },
            mode: "same-origin",
            body: JSON.stringify(data),
        });
        const response = await res.json();
        return response;
    } catch (error) {
        console.error(`PUT request error: ${error}`);
    }
}

// Text Counter
export function textCounter(textId, countId) {
    const text = document.querySelector(`#${textId}`).value;
    const count = document.querySelector(`#${countId}`);
    count.innerText = text.length;
}

// Handles delete animation
export function deleteElement(id) {
    const element = document.querySelector(`#${id}`);
    element.style.animationPlayState = "running";
    element.addEventListener("animationend", () => {
        element.remove();
    });
}

// Displays pop up view
export function displayPopUp(divId) {
    const div = document.querySelector(`#${divId}`);
    div.classList.remove("hidden");
}

// Close pop up view
export function closePopUp(id) {
    document.querySelectorAll(".clear-field").forEach((field) => {
        field.value = "";
    });
    const div = document.querySelector(`#${id}`);
    div.classList.add("hidden");

    // clear comment view
    try {
        document.querySelector("#comments-display-div").innerHTML = "";
        // document.querySelector("#no-comment-msg").innerText = "";
    } catch (TypeError) { }
}