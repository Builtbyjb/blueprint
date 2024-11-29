import {
    displayPopUp,
    setActive,
    closePopUp,
    textCounter,
    handleNav,
    sendDeleteRequests,
    sendPostRequests
} from "./utills.js";

// Set active page
setActive();

// Handle navbar
handleNav();

// Display text count
document.querySelector("#create-project-description").addEventListener("keyup", () => {
    textCounter("create-project-description", "pro-des-count");
});

// Display create-project pop-up
document.querySelector("#create-project-btn").onclick = () => {
    displayPopUp("create-project-main-div");
};

// Close create-project pop-up
document.querySelector("#close-project-pop-up").addEventListener("click", () => {
    closePopUp("create-project-main-div");
    document.querySelector("#pro-des-count").textContent = 0;
});

// Delete project
document.querySelectorAll("#delete-project").forEach((btn) => {
    btn.onclick = async (event) => {
        event.preventDefault()

        const projectId = btn.dataset.id;
        const response = await sendDeleteRequests("project", projectId);
        if (response.error) {
            console.alert(response.error);
        } else {
            deleteElement(`project-${response.projectId}`);
        }
    };
});

// Filter projects
const filterProject = document.querySelector("#filter-project")
filterProject.addEventListener("change", async () => {
    const select = filterProject.value;
    window.location.assign(`/?filter=${select}`);
});

// Search project name
const searchProject = document.querySelector("#search-project-name");
searchProject.addEventListener("keyup", () => {
    document.querySelectorAll("[data-filter]").forEach(div => {
        const input = searchProject.value.toLowerCase();
        const id = div.dataset.projectid;
        const projectName = document.querySelector(`#project-name-${id}`)
            .textContent
            .toLowerCase();

        if (projectName.includes(input)) {
            document.querySelector(`#project-${id}`).style.display = "";
        } else {
            document.querySelector(`#project-${id}`).style.display = "none";
        }

        if (input.length === 0) {
            document.querySelector(`#project-${id}`).style.display = "";
        }
    })
})

document.querySelector("#create-project-form").onsubmit = async (event) => {
    event.preventDefault();

    const name = document.querySelector("#create-project-name").value;
    const description = document.querySelector("#create-project-description").value;

    const formData = new FormData();
    formData.append("project-name", name);
    formData.append("project-description", description);

    const response = await sendPostRequests("project", formData);
    if (response.error) {
        alert(response.error);
    } else {
        closePopUp("create-project-div");
        window.location.assign(`/project/${response.projectId}`);
    }
};