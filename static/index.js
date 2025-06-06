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
      const data = await response.json();
      if (response.status === 200) {
        if (data.taskID !== "") {
          const newTask = generateTask(task, data.taskID);
          taskList.appendChild(newTask);
        }
        msg.textContent = data.message;
        textarea.value = "";
      } else {
        msg.textContent = data.error;
      }
    } catch (error) {
      console.error(error);
    }
  });

  // Add event listeners to buttons
  document.addEventListener("click", async (event) => {
    if (event.target.classList.contains("delete-btn")) {
      // Delete tasks
      event.preventDefault();
      const id = event.target.id;
      try {
        const response = await fetch(`/api/v1/tasks/${id}`, {
          method: "DELETE",
        });
        const data = await response.json();
        if (response.status === 200) {
          document.querySelector(`#task-div-${id}`).style.display = "none";
          msg.textContent = data.message;
        } else {
          msg.textContent = data.error;
        }
      } catch (error) {
        console.error(error);
      }
    } else if (event.target.classList.contains("complete-btn")) {
      // Mark tasks as completed
      event.preventDefault();
      const id = event.target.id;
      try {
        const response = await fetch(`/api/v1/tasks/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_completed: 1 }),
        });
        const data = await response.json();
        if (response.status === 200) {
          document.querySelector(`#task-${id}`).style.textDecoration =
            "line-through";
        } else {
          msg.textContent = data.error;
        }
      } catch (error) {
        console.error(error);
      }
    } else if (event.target.classList.contains("stage-btn")) {
      // Add task to the staging area
      event.preventDefault();
      console.log("Staging button clicked");
      const id = event.target.id;
      const value = document.querySelector(`#task-${id}`).textContent;
      /* Send a delete to the server and set the text area value to the task */
      try {
        const response = await fetch(`/api/v1/tasks/${id}`, {
          method: "DELETE",
        });
        const data = await response.json();
        if (response.status === 200) {
          textarea.value = value;
          document.querySelector(`#task-div-${id}`).style.display = "none";
        }
      } catch (error) {
        console.error(error);
      }
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

// function generateRandomString() {
//     const length = 6;
//     return Math.random()
//         .toString(36)
//         .slice(2, length + 2);
// }
