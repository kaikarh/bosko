const applemusicGetBtn = document.getElementById("id_apple_music_url-btn");
const bdShareParseBtn = document.getElementById("id_baidu_share-btn");

const spinner = document.createElement("span");
spinner.classList.add("spinner-border", "spinner-border-sm");

function spinBtn(button) {
  button.textContent = "";
  button.appendChild(spinner);
}

function unspinBtn(button, originalText) {
  button.removeChild(button.firstChild);
  button.textContent = originalText;
}

applemusicGetBtn.onclick = () => {
  let api_url = "/postmaker/api/am";
  let amurl = document.getElementById("id_apple_music_url").value;
  let data = {
    'amurl': amurl
  };

  csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  spinBtn(applemusicGetBtn);

  fetch(api_url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken },
    body: JSON.stringify(data)
  })
    .then(response => {
      unspinBtn(applemusicGetBtn, 'Get');
      return response.json();
    })
    .then((content) => {
      document.querySelector("input[name=artist_name]").value = content['artist'];
      document.querySelector("input[name=collection_name]").value = content['title'];
      document.querySelector("input[name=genre_name]").value = content['meta'][0];
      document.querySelector("input[name=release_date]").value = content['meta'][1];
      document.querySelector("input[name=artwork_url]").value = content['art'];
      document.querySelector("textarea[name=tracks]").value = trackArrToDictList(content['tracklist']);
    });
}

function trackArrToDictList(arr) {
  let result = Array();
  arr.forEach(element => {
    result.push({"name": element});
  });
  
  return JSON.stringify(result);
}

bdShareParseBtn.onclick = () => {
  let du = document.getElementById("id_baidu_share");
  let re = /(https:\/\/.+)\ .+\ (\w{1,4})/;
  let result = du.value.match(re);
  let linksField = document.querySelector("textarea[name=download_links]");
  let linkObj = {"url": result[1], "passcode": result[2]};
  let links = []
  try {
    links = JSON.parse(linksField.value);
  } catch {}
  if (Array.isArray(links)) {
    links.push(linkObj);
    linksField.value = JSON.stringify(links);
  }
}