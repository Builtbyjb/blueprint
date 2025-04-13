const form = document.querySelector("#task-form");
const textarea = document.querySelector("#task-textarea");
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
        if (response.status === 200) {
            const data = await response.json();
            alert(data.message);
            textarea.value = "";
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error(error);
    }
});
