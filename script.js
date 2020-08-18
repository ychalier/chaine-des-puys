let instance = panzoom(document.querySelector("#scene"));
instance.setTransformOrigin(null);
document.querySelector("#about_button").addEventListener("click", (event) => {
    let button = document.querySelector("#about_button");
    let content = document.querySelector("#about_content");
    if (content.classList.contains("show")) {
        content.classList.remove("show");
        button.innerHTML = "[à propos]";
    } else {
        content.classList.add("show");
        button.innerHTML = "[fermer]";
        let listContent = document.querySelector("#list_content");
        if (listContent.classList.contains("show")) {
            listContent.classList.remove("show");
            document.querySelector("#list_button").innerHTML = "[liste]";
        }
    }
});
document.querySelector("#list_button").addEventListener("click", (event) => {
    let button = document.querySelector("#list_button");
    let content = document.querySelector("#list_content");
    if (content.classList.contains("show")) {
        content.classList.remove("show");
        button.innerHTML = "[liste]";
    } else {
        content.classList.add("show");
        button.innerHTML = "[fermer]";
        let aboutContent = document.querySelector("#about_content");
        if (aboutContent.classList.contains("show")) {
            aboutContent.classList.remove("show");
            document.querySelector("#about_button").innerHTML = "[à propos]";
        }
    }
});
