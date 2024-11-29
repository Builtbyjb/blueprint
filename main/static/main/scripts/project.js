import {
    textCounter,
    displayPopUp,
    sendDeleteRequests,
    sendGetRequests,
    sendPostRequests,
    sendPutRequests,
    handleNav,
    closePopUp
 } from "./utills.js";


// Handles navbar
handleNav();

const dropdownToggle = document.getElementById('dropdownToggle');
const dropdownContent = document.getElementById('dropdownContent');
const dropdownIcon = dropdownToggle.querySelector('svg');

dropdownToggle.addEventListener('click', () => {
    dropdownContent.classList.toggle('hidden');
    dropdownIcon.classList.toggle('rotate-180');
});

// Close the dropdown when clicking outside
document.addEventListener('click', (event) => {
    if (!dropdownToggle.contains(event.target) && !dropdownContent.contains(event.target)) {
        dropdownContent.classList.add('hidden');
        dropdownIcon.classList.remove('rotate-180');
    }
});

document.querySelector("#task-text").addEventListener("keyup", () => {
    textCounter("task-text", "task-text-count");
});

document.querySelector("#comment-text").addEventListener("keyup", () => {
    textCounter("comment-text", "comment-text-count");
});

document.querySelector("#add-task-btn").onclick = () => {
    document.querySelector("#task-text-count").textContent = "0";
    document.querySelector("#add-task-input").value = "Add Task";
    document.querySelector("#add-task-display-title").textContent = "Add Task";

    displayPopUp("add-task-main-div");
};

document.querySelector("#team-member-btn").onclick = () => {
    document.querySelector("#team-member-username").removeAttribute("disabled");
    document.querySelector("#add-team-member-header").textContent = "Add Team Member";
    document.querySelector("#add-team-member").value = "Add";
    displayPopUp("team-member-main-div");
};

// View comments
document.addEventListener("click", async (event) => {
    const element = event.target;

    if (element.id === "view-comment") {
        const taskId = element.dataset.taskid;

        const response = await sendGetRequests("comment", taskId);
        if (response.error) {
            console.error(response.error);
        } else {
            document.querySelector("#comment-task-display").innerText = response.taskText;
            document.querySelector("#task-id").value = response.taskId;
            document.querySelector("#comment-submit").dataset.taskId = response.taskId;
            document.querySelector("#comment-div-count").textContent = response.commentCount;
            if (response.comments.length > 0) {
                response.comments.forEach((comment) => {
                    generateComment(comment, response.username, response.taskId);
                });
            }
            document.querySelector("#comment-submit").value = "Comment";
            document.querySelector("#comment-text-count").textContent = "0";

            displayPopUp("comment-view-main-div");
        }
    }
})

document.querySelector("#close-task-pop-up").addEventListener("click", () => {
    closePopUp("add-task-main-div");
});

document.querySelector("#close-team-add-pop-up").addEventListener("click", () => {
    closePopUp("team-member-main-div");
    document.querySelector("#team-member-username").value = "";
});

document.querySelector("#close-comment-pop-up").addEventListener("click", () => {
    closePopUp("comment-view-main-div");
});

document.querySelector("#close-project-des-pop-up").addEventListener("click", () => {
    closePopUp("edit-project-des-main-div");
});

document.querySelector("#close-project-name-pop-up").addEventListener("click", () => {
    closePopUp("edit-project-name-main-div");
});

// Delete project
document.querySelector("#delete-project-exp").onclick = async () => {
    const id = document.querySelector("#delete-project-exp").dataset.id;

    const response = await sendDeleteRequests("project", id);
    if (response.error) {
        console.error(response.error);
    } else {
        window.location.replace("/");
    }
};

async function updateCommentCount(taskId, commentCount) {
    const formData = new FormData();
    formData.append("commentCount", commentCount);
    formData.append("taskId", taskId);

    const response = await sendPostRequests("comment_count", formData);
    if (response.error) {
        console.error(response.error);
    } else {
        document.querySelector("#comment-div-count").textContent = response.commentCount;
        document.querySelector(`#task-comment-count-${response.taskId}`)
            .textContent = response.commentCount;
    }
}

document.querySelector("#add-comment-form").onsubmit = async (event) => {
    event.preventDefault();

    const input = document.querySelector("#comment-submit");
    const comment = document.querySelector("#comment-text");

    if (input.value === "Comment") { // Add comment
        const taskId = document.querySelector("#task-id").value;

        const formData = new FormData();
        formData.append("comment", comment.value);
        formData.append("task-id", taskId);

        const response = await sendPostRequests("comment", formData);

        if (response.error) {
            alert(response.error);
        } else {
            generateComment(response.comment[0], response.username, response.taskId);
            const commentCount = document.querySelector("#comments-display-div").children.length;
            updateCommentCount(taskId, commentCount);
            comment.value = "";
            document.querySelector("#comment-text-count").textContent = "0";
        }
    } else {// Save edited comment
        const commentId = document.querySelector("#task-id").value;
        const data = { comment: comment.value };

        const response = await sendPutRequests("comment", commentId, data);
        if (response.error) {
            alert(response.error);
        } else {
            document.querySelector("#task-id").value = response.taskId;
            document.querySelector("#comment-submit").value = "comment";
            document.querySelector(`#comment-text-${response.commentId}`)
                .textContent = response.commentText;
            comment.value = "";
            document.querySelector("#comment-text-count").textContent = "0";
        }
    }
};

// delete and edit comment
document.addEventListener("click", async (event) => {
    const element = event.target;

    if (element.id === "delete-comment") { // Delete comment
        const commentCount =
            document.querySelector("#comments-display-div").children.length - 1;
        const response = await sendDeleteRequests("comment", element.dataset.id);
        if (response.error) {
            console.error(response.error);
        } else {
            deleteElement(`comment-${response.commentId}`);
            updateCommentCount(element.dataset.taskid, commentCount);
        }
    } else if (element.id === "edit-comment") {// Edit comment
        const commentText = document.querySelector(`#comment-text-${element.dataset.id}`).textContent;
        document.querySelector("#comment-text").value = commentText;
        document.querySelector("#comment-text-count").textContent = commentText.length;
        document.querySelector("#comment-submit").value = "Save";
        document.querySelector("#task-id").value = element.dataset.id;
    }
});

// Delete task or display edit task view
document.addEventListener("click", async (event) => {
    const element = event.target;
    const taskId = element.dataset.taskid;

    if (element.id === "delete-task") {// Deletes task
        const response = await sendDeleteRequests("task", taskId);
        if (response.error) {
            console.error(response.error);
        } else {
            deleteElement(`task-${taskId}`);
        }
    } else if (element.id === "edit-task") {// Edit task view
        const taskText = document.querySelector(`#task-text-${taskId}`).textContent;

        displayPopUp("add-task-main-div");

        document.querySelector("#task-text").value = taskText;
        document.querySelector("#task-text-count").textContent = taskText.length;
        document.querySelector("#add-task-input").value = "Save Task";
        document.querySelector("#add-task-display-title").textContent = "Edit Task";
        document.querySelector("#project-id").value = taskId;
    }
});

document.querySelector("#add-task-form").onsubmit = async (event) => {
    event.preventDefault();

    const input = document.querySelector("#add-task-input").value;

    if (input === "Add Task") { // Add task
        const projectId = document.querySelector("#project-id").value;
        const taskText = document.querySelector("#task-text").value;

        const formData = new FormData();
        formData.append("task-text", taskText);
        formData.append("project-id", projectId);

        const response = await sendPostRequests("task", formData);
        if (response.error) {
            alert(response.error);
        } else {
            generateTask(response);
        }
    } else {// Edit task
        const taskId = document.querySelector("#project-id").value;
        const task = document.querySelector("#task-text").value;
        const data = { task: task };

        const response = await sendPutRequests("task", taskId, data);
        if (response.error) {
            alert(response.error);
        } else {
            document.querySelector(`#task-text-${response.taskId}`).textContent =
                response.taskText;
            document.querySelector("#add-task-input").value = "Add Task";
            document.querySelector("#add-task-display-title").textContent =
                "Add Task";
            document.querySelector("#project-id").value = response.projectId;

            closePopUp("add-task-main-div");
        }
    }
};

document.querySelector("#edit-project-name").onclick = () => {
    displayPopUp("edit-project-name-main-div");

    const projectName = document.querySelector("#project-name").textContent;
    document.querySelector("#name-text").value = projectName;
    document.querySelector("#name-text-count").textContent = projectName.length;
};

document.querySelector("#edit-project-name-form").onsubmit = async (event) => {
    event.preventDefault();

    const projectId = document.querySelector("#project-name").dataset.id;

    const project_name = document.querySelector("#name-text").value;

    const data = { project_name: project_name };
    const response = await sendPutRequests("project", projectId, data);
    if (response.error) {
        alert(response.error);
    } else {
        document.querySelector(`#${response.elementId}`).textContent =
            response.projectName;
        closePopUp("edit-project-name-main-div");
    }
};

document.querySelector("#edit-project-des").onclick = () => {
    displayPopUp("edit-project-des-main-div");

    const projectDescription = document.querySelector("#project-description").textContent;
    document.querySelector("#description-text").value = projectDescription;
    document.querySelector("#description-text-count").textContent = projectDescription.length;
};

document.querySelector("#edit-project-des-form").onsubmit = async (event) => {
    event.preventDefault();

    const projectId = document.querySelector("#project-name").dataset.id;

    const project_description = document.querySelector("#description-text").value;

    const data = { project_description: project_description };
    const response = await sendPutRequests("project", projectId, data);
    if (response.error) {
        alert(response.error);
    } else {
        document.querySelector(`#${response.elementId}`).textContent = response.projectDescription;
        closePopUp("edit-project-des-main-div");
    }
};

function generateComment(comment, username, taskId) {
    const mainDiv = document.querySelector("#comments-display-div");
    const div = document.createElement("div");
    div.setAttribute("id", `comment-${comment.id}`);
    div.classList.add("delete-item", "shadow", "bg-dark-100", "p-4", "rounded-lg", "w-full");
    div.innerHTML = `
        <div>
            <p><strong>${comment.creator}</strong></p>
            <p id="comment-text-${comment.id}">${comment.comment}</p>
        </div>
    `;
    const subDiv = document.createElement("div");

    const editBtn = document.createElement("button");
    editBtn.classList.add("me-4", "bg-blue-600", "hover:bg-blue-700", "me-3", "text-white", "font-bold", "py-2", "px-4", "rounded", "focus:outline-none", "focus:shadow-outline", "transition-colors");
    editBtn.setAttribute("id", "edit-comment");
    editBtn.setAttribute("data-id", comment.id);
    editBtn.setAttribute("data-taskid", taskId);
    editBtn.innerHTML = `
        <i id="edit-comment"
            data-id="${comment.id}" 
            data-taskid="${taskId}" 
            class="fa-solid fa-pen-to-square"
        ></i>
    `;

    const deleteBtn = document.createElement("button");
    deleteBtn.classList.add("me-4", "bg-red-600", "hover:bg-red-700", "text-white", "font-bold", "py-2", "px-4", "rounded", "focus:outline-none", "focus:shadow-outline", "transition-colors");
    deleteBtn.setAttribute("id", "delete-comment");
    deleteBtn.setAttribute("data-id", `${comment.id}`);
    deleteBtn.setAttribute("data-taskid", taskId);
    deleteBtn.innerHTML = `
        <i id="delete-comment"
            data-id="${comment.id}" 
            data-taskid="${taskId}" 
            class="fa-solid fa-trash-can"
        ></i>
    `;

    if (comment.creator === username) {
        subDiv.append(editBtn);
        subDiv.append(deleteBtn);
    }

    div.append(subDiv);
    mainDiv.prepend(div);
}

function generateTask(response) {
    const mainDiv = document.querySelector("#tasks-div");
    const subDiv = document.createElement("div");

    subDiv.setAttribute("id", `task-${response.taskId}`);
    subDiv.setAttribute("data-id", response.taskId);
    subDiv.classList.add("delete-item", "shadow", "bg-dark-100", "p-4", "rounded-lg", "md:w-fit", "lg:w-fit");
    subDiv.innerHTML = `
        <div class="mb-4">
            <p id="task-text-${response.taskId}">${response.task}</p>
        </div>
    `;

    const div = document.createElement("div");

    const assignedDiv = document.createElement("div");
    assignedDiv.classList.add("mb-3");

    /* Displays the assign team members option if the current user 
        is the project creator or team leader */
    if (response.projectCreator === response.user || response.projectTeamLeader === response.user) {
        const select = document.createElement("select");
        select.className = "px-2 w-full py-1 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        select.setAttribute("data-id", response.taskId);
        select.setAttribute("id", "assign-team-member");
        select.innerHTML = `
            <option selected data-assign> ${response.assigned_to}</option>
        `;

        // Populates the "select" element with projects team members
        for (const i in response.teams) {
            if (response.assigned_to !== response.teams[i].member) {
                const option = document.createElement("option");
                option.setAttribute("value", response.teams[i].member);
                option.setAttribute("data-remove", response.teams[i].id);
                option.textContent = `${response.teams[i].member}`;
                select.append(option);
            }
        }

        // Appends an "unassigned" option if the task is assigned to a team member
        if (response.assigned_to !== "unassigned") {
            const option = document.createElement("option");
            option.setAttribute("value", "unsassigned");
            option.innerHTML = "unassigned";

            select.append(option);
        }

        assignedDiv.append(select);
    } else {
        const p = document.createElement("p");
        p.textContent = response.assigned_to;
        assignedDiv.append(p);
    }
    div.append(assignedDiv);

    // Tasks stage select
    const select = document.createElement("select");
    select.className ="mb-4 w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
    select.setAttribute("id", "task-stage-change");
    select.setAttribute("data-taskid", response.taskId);

    const toDoOption = document.createElement("option");
    toDoOption.setAttribute("value", "to-do");
    if (response.taskStage === "to-do") {
        toDoOption.setAttribute("selected", "");
    }
    toDoOption.textContent = "To-Do";

    const inProgressOption = document.createElement("option");
    inProgressOption.setAttribute("value", "in-progress");
    if (response.taskStage === "in-progress") {
        inProgressOption.setAttribute("selected", "");
    }
    inProgressOption.textContent = "In Progress";

    const completedOption = document.createElement("option");
    completedOption.setAttribute("value", "completed");
    if (response.taskStage === "completed") {
        completedOption.setAttribute("selected", "");
    }
    completedOption.textContent = "Completed";

    select.append(toDoOption);
    select.append(inProgressOption);
    select.append(completedOption);

    div.append(select);

    // Delete and Edit buttons
    const delDiv = document.createElement("div");
    delDiv.classList.add("d-flex", "align-items-center");
    delDiv.innerHTML = `
        <button id="view-comment" data-taskid="${response.taskId}"
            class="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded me-4 relative"
            <i id="view-comment" data-taskid="${response.taskId}" class="fa-solid fa-comment"></i>
            <span id="task-comment-count-${response.taskId}" class="absolute top-0 right-1">
              ${response.commentNumber}
              <span class="visually-hidden">number of comments</span>
            </span>
          </button>
        </button>
        <button id="edit-task"
            class="me-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition-colors"
            data-taskid="${response.taskId}"
        >
            <i id="edit-task"
                data-taskid="${response.taskId}" 
                class="fa-solid fa-pen-to-square"
            ></i>
        </button>
    `;

    if (response.projectCreator === response.user || response.projectTeamLeader === response.user) {
        const btn = document.createElement("button");
        btn.className = "bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition-colors me-4"
        btn.setAttribute("id", "delete-task");
        btn.setAttribute("data-taskid", response.taskId);
        btn.innerHTML = `
            <i id="delete-task" data-taskid="${response.taskId}" class="fa-solid fa-trash-can"></i>
        `;
        delDiv.append(btn);
    }

    div.append(delDiv);
    subDiv.append(div);
    mainDiv.prepend(subDiv);

    closePopUp("add-task-main-div");
}

function generateTeamMember(response) {

    // Add new team member to the team member drop down
    const teamDisplay = document.querySelector("#team-member-display");

    const li = document.createElement("li");
    li.classList.add("m-2", "shadow", "p-3");
    li.setAttribute("data-remove", response.team[0].id)

    const roleDiv = document.createElement("div");
    roleDiv.classList.add("flex", "items-center", "justify-between");
    roleDiv.innerHTML = `
        <div>
            <h3 id="member-username-${response.team[0].id}" 
                data-teamid="${response.team[0].id}"
                class="text-lg font-semibold"
            >${response.team[0].member}</h3>
            <p id="team-member-${response.team[0].member}"
                class="text-sm text-gray-400"
            >${response.team[0].role}</p>
        </div>
    `;

    const btnDiv = document.createElement("div");
    btnDiv.classList.add("flex", "space-x-2");

    if (response.projectCreator === response.username) {
        if (response.team[0].role !== "Admin") {
            const editbtn = document.createElement("button");
            editbtn.className = "bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            editbtn.setAttribute("id", "team-role-edit");
            editbtn.setAttribute("data-remove", response.team[0].id);
            editbtn.setAttribute("data-teamid", response.team[0].id);
            editbtn.setAttribute("data-teamrole", response.team[0].role);
            editbtn.setAttribute("data-teammember", response.team[0].member);

            editbtn.innerHTML = `
                <i id="team-role-edit"
                    data-remove="${response.team[0].id}"
                    data-teamid="${response.team[0].id}"
                    data-teamrole="${response.team[0].role}"
                    data-teammember="${response.team[0].member}"
                    class="fa-solid fa-pen-to-square"
                ></i>
            `;

            btnDiv.append(editbtn);
        }
    }

    const delbtn = document.createElement("button");
    delbtn.className = "bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
    delbtn.setAttribute("id", "team-member-delete");
    delbtn.setAttribute("data-teamid", response.team[0].id);
    delbtn.innerHTML = `
        <i id="team-member-delete"
            data-teamid=${response.team[0].id} 
            class="fa-solid fa-trash-can"
        ></i>
    `;

    if (response.team[0].role !== "Admin") {
        if (response.projectLeader === response.username || response.projectCreator === response.username) {
            btnDiv.append(delbtn);
        }

        if (response.team[0].role === "Team member" && response.team[0].member === response.username) {
            btnDiv.append(delbtn);
        }
    }

    roleDiv.append(btnDiv)
    li.append(roleDiv)
    teamDisplay.append(li);

    // Add new team member to the team member filter list
    const teamFilter = document.querySelector("#team-filter");

    const option = document.createElement("option");
    option.setAttribute("value", `${response.team[0].member}`);
    option.setAttribute("data-remove", `${response.team[0].id}`);
    option.textContent = `${response.team[0].member}`;

    teamFilter.append(option);

    // Add new team member to all the tasks assign section
    document.querySelectorAll("#assign-team-member").forEach(select => {
        const option = document.createElement("option")
        option.setAttribute("value", `${response.team[0].member}`)
        option.setAttribute("data-remove", `${response.team[0].id}`)
        option.textContent = `${response.team[0].member}`;

        select.append(option);
    })
}

// Assign tasks
document.addEventListener("change", async (event) => {
    const element = event.target;
    const taskId = element.dataset.id;

    if (element.id === "assign-team-member") {
        data = { assign: element.value };

        const response = await sendPutRequests("assign", taskId, data);
        if (response.error) {
            alert(response.error);
        }
    }
});

// Filter tasks based on team members
const teamSelect = document.querySelector("#team-filter");
const taskSelect = document.querySelector("#task-filter");
teamSelect.addEventListener("change", () => {
    const projectId = document.querySelector("#project-name").dataset.id;
    window.location.assign(
        `/project/${projectId}?assigned=${teamSelect.value}&stage=${taskSelect.value}`
    );
});

// Filter tasks based on tasks stage
try {
    const taskSelect = document.querySelector("#task-filter");
    const teamSelect = document.querySelector("#team-filter");
    taskSelect.addEventListener("change", () => {
        const projectId = document.querySelector("#project-name").dataset.id;
        window.location.assign(
            `/project/${projectId}?assigned=${teamSelect.value}&stage=${taskSelect.value}`
        );
    });
} catch (TypeError) { }

// Project isCompleted
try {
    document.querySelector("#project-completed").onclick = async () => {
        const isCompleted = document.querySelector("#project-completed").checked;
        const projectId = document.querySelector("#project-completed").dataset.projectid;
        const data = { isCompleted: isCompleted };
        const response = await sendPutRequests("project", projectId, data);
        if (response.error) {
            console.error(error);
        }
    };
} catch (TypeError) { }

// Edit team role
document.addEventListener("click", (event) => {
    const element = event.target;

    if (element.id === "team-role-edit") {
        const teamid = element.dataset.teamid;

        const teamMember = document.querySelector(`#member-username-${teamid}`).textContent;

        displayPopUp("team-member-main-div");
        document.querySelector("#team-member-username").value = teamMember;
        document.querySelector("#team-member-username").setAttribute("disabled", "");
        document.querySelector("#add-team-member").value = "Save";
        document.querySelector("#add-team-member-header").textContent = "Edit Team Member Role";

    }
})

// Add team member
try {
    document.querySelector("#add-team-member").onclick = async (event) => {
        event.preventDefault();

        const input = document.querySelector("#add-team-member");
        const username = document.querySelector("#team-member-username").value;
        const projectId = document.querySelector("#add-team-member").dataset.id;
        const role = document.querySelector("#role-select").value;

        if (input.value == "Add") {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("project_id", projectId);
            formData.append("role", role);

            const response = await sendPostRequests("team", formData);
            if (response.error) {
                alert(response.error);
            } else {
                generateTeamMember(response);
                alert(response.success)
                closePopUp("team-member-main-div")
            }
        } else { // Input.value === "Save"
            const data = { project_id: projectId, role: role, username: username };
            const response = await sendPutRequests("team", projectId, data);
            if (response.error) {
                alert(response.error);
            } else {
                document.querySelector("#add-team-member-header").textContent = "Add Team Member";
                document.querySelector("#add-team-member").value = "Add";
                updateRole(username, role);
                closePopUp("team-member-main-div");
                alert(response.success);
            }
        }
    };
} catch (TypeError) { }

/*
Allows newly created team member html elements 
to be updated without reloading the page  
*/
function updateRole(username, role) {
    document.querySelector(`#team-member-${username}`).textContent = role;
}

// Remove team member
document.addEventListener("click", async (event) => {
    const element = event.target;

    if (element.id === "team-member-delete") {
        const teamId = element.dataset.teamid;
        let canDelete = true;

        const username = document.querySelector(`#member-username-${teamId}`).textContent;
        document.querySelectorAll("[data-assign]").forEach(element => {
            if (username === element.textContent.trim()) {
                canDelete = false;
            }
        })

        if (canDelete) {
            const response = await sendDeleteRequests("team", teamId);
            if (response.error) {
                console.log(response.error);
            } else {
                document.querySelectorAll(`[data-remove="${response.teamId}"`).forEach(element => {
                    element.style.display = "none";
                })
                alert(`${username} as been removed from the team`)
            }
        } else {
            alert("Unable to remove team members still assigned to tasks")
        }
    }
})

// Change task stage
document.addEventListener("change", async (event) => {
    const element = event.target;

    if (element.id === "task-stage-change") {
        const taskId = element.dataset.taskid;
        const stage = element.value;

        const data = { "taskStage": stage };
        const response = await sendPutRequests("stage", taskId, data)
        if (response.error) {
            alert(response.error)
        }
    }
})