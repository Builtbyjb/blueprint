const form = document.querySelector("#task-form");
const textarea = document.querySelector("#task-textarea");
const sendbtn = document.querySelector("#task-textarea-btn");
const msg = document.querySelector("#msg");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const task = textarea.value;

    try {
        const response = await fetch("/api/v1/task", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ task: task }),
        });
        const data = await response.json();
        msg.innerText = data.message;
    } catch (error) {
        console.error(error);
    }
});
