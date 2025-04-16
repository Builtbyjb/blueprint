document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#task-form");
    const textarea = document.querySelector("#task-input");
    const taskList = document.querySelector("#task-list");
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
                msg.textContent = data.content;
                textarea.value = "";
                // const id = generateRandomString();
                // const newTask = generateTask(task, id);
                // taskList.appendChild(newTask);
            } else {
                msg.textContent = data.error;
            }
        } catch (error) {
            console.error(error);
        }
    });

    // Add event listeners to buttons
    document.addEventListener("click", (event) => {
        if (event.target.classList.contains("delete-btn")) {
            event.preventDefault();
            console.log("Delete button clicked");
            const id = event.target.id;
            console.log(id);
            // Send delete request to the backend
            // Select div with the id and set the display property to none
            document.querySelector(`#task-div-${id}`).style.display = "none";
        } else if (event.target.classList.contains("complete-btn")) {
            event.preventDefault();
            console.log("Complete button clicked");
            const id = event.target.id;
            console.log(id);
            // Send set a task is completed value to true
            // Select the div with the id and add the completed style
        } else if (event.target.classList.contains("stage-btn")) {
            event.preventDefault();
            console.log("Staging button clicked");
            const id = event.target.id;
            console.log(id);
            // Send set a task is staging value to true
            // Select the div with the id and add the staging style
        }
    });
});

function generateTask(task, id) {
    const div = document.createElement("div");
    div.classList.add("mb-4");
    div.setAttribute("id", `task-div-${id}`);
    div.innerHTML = `
        <p id="task-${id}" class="mb-2">${task}</p>
        <div class="flex gap-4">
            <a id=${id} class="delete-btn underline text-red-500 text-sm">Delete</a>
            <a id=${id} class="stage-btn underline text-blue-500 text-sm">Stage</a>
            <a id=${id} class="complete-btn underline text-green-500 text-sm">Completed</a>
        </div>
    `;
    return div;
}

function generateRandomString() {
    const length = 6;
    return Math.random()
        .toString(36)
        .slice(2, length + 2);
}
