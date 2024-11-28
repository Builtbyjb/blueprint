import { displayPopUp, setActive } from "./utills.js";

// Set active page
setActive()

// Display text count
document.querySelector("#project-description-create").addEventListener("keyup", () => {
    textCounter("project-description-create", "pro-des-count");
});

document.querySelector("#create-project-btn").onclick = () => {
    displayPopUp("create-project-main-div");
};

document.querySelector("#close-project-pop-up").addEventListener("click", () => {
    closePopUp("create-project-main-div");
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
