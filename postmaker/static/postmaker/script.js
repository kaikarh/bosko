document.getElementById("id_apple_music_url-btn").onclick = () => {
  api_url = "/postmaker/api/am";
  amurl = document.getElementById("id_apple_music_url").value;
  data = {
    'amurl': amurl
  }

  csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  fetch(api_url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken },
    body: JSON.stringify(data)
  })
    .then(response => response.json())
    .then((content) => {
      document.querySelector("input[name=artist]").value = content['artist'];
      document.querySelector("input[name=title]").value = content['title'];
      document.querySelector("input[name=genre]").value = content['meta'][0];
      document.querySelector("input[name=year]").value = content['meta'][1];
      document.querySelector("input[name=artwork]").value = content['art'];
      document.querySelector("textarea[name=apple_tracks]").readOnly=false;
      document.querySelector("textarea[name=apple_tracks]").value = content['tracklist'];
      document.querySelector("textarea[name=apple_tracks]").readOnly=true;
      document.querySelector("textarea[name=tracks]").readOnly=true;
    });
}

document.getElementById("id_baidu_share-btn").onclick = () => {
  let du = document.getElementById("id_baidu_share");
  let re = /(https:\/\/.+)\ .+\ (\w{1,4})/;
  let result = du.value.match(re);
  document.querySelector("input[name=download_link]").value = result[1];
  document.querySelector("input[name=download_passcode]").value = result[2];
}
