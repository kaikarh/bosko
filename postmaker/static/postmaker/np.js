var loadingBtn = document.createElement("button");
loadingBtn.type = "button";
loadingBtn.id = "loadingBtn";
loadingBtn.className = "btn btn-primary";
loadingBtn.setAttribute("disabled", "");
loadingBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> <span class="visually-hidden">Loading...</span>';

function swapBtn(cur, sub) {

}

document.getElementById("np-login").onclick = () => {
    var msg_box = document.getElementById("np-login-msg");
    msg_box.style.display = "none";
    msg_box.innerText = "";
    

    api_url = "/postmaker/api/np/login";
    data = {
        "username": document.getElementById("np-username").value,
        "password": document.getElementById("np-password").value
    }
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    var btn = document.getElementById("np-login");
    btn.parentElement.replaceChild(loadingBtn, btn);

    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken },
        body: JSON.stringify(data)
    })
    .then((response) => {
        loadingBtn.parentElement.replaceChild(btn, loadingBtn);
        // reset the form
        document.getElementById("np-username").value = "";
        document.getElementById("np-password").value = "";
        if (response.ok) {
            return response.json();
        } else {
            throw new Error("Login Failed");
        }
    })
    .then((content) => {
        opt = document.createElement("option");
        opt.value = content["cdb_auth"];
        opt.text = data["username"];
        document.getElementById("np-account-select").add(opt);
        document.getElementById("np-account-select").value = opt.value;
        bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
    })
    .catch((error) => {
        msg_box.innerText = error;
        msg_box.style.display = "block";
    });
}

document.getElementById("np-post-thread").onclick = () => {
    var msg_box = document.getElementById("np-message");
    msg_box.innerText = "";
    api_url = "/postmaker/api/np/post";
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // spin that button
    var btn = document.getElementById("np-post-thread");
    btn.parentElement.replaceChild(loadingBtn, btn);
    
    // need subject, message, forum_id, typeid

    data = {
        "cdb_auth": document.getElementById("np-account-select").value,
        "subject": document.querySelector("input[name='subject']").value,
        "message": document.querySelector("textarea").value,
        "forum_id": document.querySelector("select[name='forum_id']").value,
        "typeid": document.querySelector("select[name='typeid']").value
    }
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken },
        body: JSON.stringify(data)
    })
    .then((response) => {
        loadingBtn.parentElement.replaceChild(btn, loadingBtn);
        if (response.ok) {
            return response.json();
        } else {
            throw new Error("Post Failed")
        }
    })
    .then((content) => {
        var titleElm = document.createElement("a");
        titleElm.href = content["url"];
        titleElm.innerText = content["title"];
        set_posted();
        msg_box.appendChild(titleElm);
    })
    .catch((error) => {
        msg_box.innerText = error;
    });

}

function set_posted() {
    var pk = document.getElementById("pk").value;
    var posted_api_url = "/postmaker/api/set-posted"
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    data = {
        "pk": pk
    }
    fetch(posted_api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken },
        body: JSON.stringify(data)
    }).then((response) => {
        console.log(response);
    })
}
