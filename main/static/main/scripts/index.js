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
try {
    document.querySelector("#filter-project").addEventListener("change", async () => {
        const select = document.querySelector("#filter-project").value;
        window.location.assign(`/?filter=${select}`);
    });
} catch (TypeError) { }

/*
Displays all the projects, if the cancel icon on the input search
element is clicked
*/
document.addEventListener("click", (event) => {
    const element = event.target
    if (element.id === "search-project-name-input") {
        if (element.value.length > 0) {
            document.querySelectorAll("[data-filter]").forEach(div => {
                div.style.display = ""
            })
        }
    }
})

// Search project name
document.querySelector("#search-project-name-input").addEventListener("keyup", () => {
    document.querySelectorAll("[data-filter]").forEach(div => {
        const input = document.querySelector("#search-project-name-input").value.toLowerCase();
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
