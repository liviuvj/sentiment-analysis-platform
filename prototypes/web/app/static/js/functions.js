function toggleNavbar() {
    // Function used to toggle the responsive navigation bar
    var x = document.getElementById("top-nav");
    if (x.className === "container navigation-menu") {
        x.className += " responsive";
    } else {
        x.className = "container navigation-menu";
    }
}

function platformRedirect(id) {
    // Function to redirect to the correspondig platform urls
    if (id == "orchestration") {window.open("http://localhost:8080", "_blank");}
    else if (id == "ingestion") {window.open("http://localhost:8000", "_blank");}
    else if (id == "processing") {window.open("http://localhost:4040", "_blank");}
    else if (id == "storage") {window.open("http://localhost:8123/play", "_blank");}
    else if (id == "visualization") {window.open("http://localhost:8088", "_blank");}
}