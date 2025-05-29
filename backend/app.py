<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <title>Smart Radio Search</title>
  <script src="twemoji.min.js"></script>
  <style>
    /* Tiny Twemoji flags */
    .emoji {
      display:inline-block;height:1em!important;width:auto!important;
      vertical-align:-.1em!important;margin:0 .1em .0 .05em!important;
    }
    body { margin:0; font-family:sans-serif; background:#b7b7b7; color:#111;
      padding:1rem; transition:background .3s,color .3s }
    body.dark { background:#444; color:#eee }
    #description { margin:0 0 1rem }
    .controls {
      display:flex; flex-wrap:wrap; gap:.5rem; margin-bottom:1rem; align-items:center;
    }
    .controls input { flex:1 1 250px; padding:.5rem }
    .controls select, .controls button { padding:.5rem 1rem; white-space:nowrap }
    #results {
      display:grid;
      grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
      gap:1rem;
    }
    .card {
      background:#fff; border-radius:.5rem; box-shadow:0 2px 4px rgba(0,0,0,.1);
      padding:1rem; display:flex; flex-direction:column;
      transition:background .3s,color .3s;
    }
    body.dark .card {
      background:#333; color:#eee; box-shadow:0 2px 4px rgba(0,0,0,.5);
    }
    .card h3 { margin:0 0 .5rem; font-size:1.1rem }
    .card .meta { font-size:.9rem; margin:.25rem 0 }
    .card audio { margin:.5rem 0; width:100% }
    .card .now-playing { font-size:.9rem; font-style:italic; margin-bottom:.5rem }
    .tag { color:#06c; text-decoration:none; cursor:pointer; margin-right:.25rem }
    .tag:hover { text-decoration:underline }
    .loading { font-style:italic }
  </style>
</head>
<body>
  <h1>Smart Radio Search</h1>
  <p id="description">
    Discover, preview, and play streaming radio stations from around the world —
    with AI-powered genre tagging, live filtering, and one-at-a-time playback.
  </p>

  <div class="controls">
    <input id="query" placeholder="Search for genre, location, etc." autocomplete="off" />
    <button id="searchBtn">Search</button>
    <select id="countryFilter"><option value="">All Countries</option></select>
    <select id="genreFilter"><option value="">All Genres</option></select>
    <select id="sortBy">
      <option value="votes">Votes ↓</option>
      <option value="clickcount">Clicks ↓</option>
      <option value="bitrate">Bitrate ↓</option>
    </select>
    <button onclick="toggleDark()">Toggle Dark Mode</button>
  </div>

  <p id="aiResult"></p>
  <div id="results"></div>

  <script>
    // Top-20 curated genres
    const COMMON_GENRES = [
      "pop","rock","jazz","classical","hip hop",
      "electronic","dance","country","blues","reggae",
      "metal","folk","soul","funk","disco",
      "r&b","indie","alternative","punk","latin"
    ];

    function countryCodeToFlag(cc) {
      return cc
        ? cc.toUpperCase().split("")
            .map(c=>String.fromCodePoint(0x1F1E6 + c.charCodeAt(0)-65))
            .join("")
        : "";
    }
    function toggleDark(){ document.body.classList.toggle("dark"); }

    // wire up search
    document.getElementById("searchBtn").onclick = search;
    document.getElementById("query")
      .addEventListener("keydown", e=>{
        if(e.key==="Enter"){ e.preventDefault(); search(); }
      });
    document.getElementById("results")
      .addEventListener("click", e=>{
        if(e.target.classList.contains("tag")){
          document.getElementById("query").value = e.target.textContent;
          search();
        }
      });

    window.addEventListener("DOMContentLoaded", ()=>{
      initFilters();
      loadAndRender({ top: true });
    });

    // populate country & genre dropdowns
    async function initFilters(){
      // now proxy through your own backend
      try {
        const r = await fetch("https://simple-naomi-joewilcom-71ae2211.koyeb.app/countries");
        const countries = await r.json();
        countries.sort((a,b)=>a.name.localeCompare(b.name))
          .forEach(c=>{
            const o = document.createElement("option");
            o.value = c.code.toLowerCase();
            o.textContent = `${countryCodeToFlag(c.code)} ${c.name}`;
            document.getElementById("countryFilter").appendChild(o);
          });
      } catch(e){
        console.warn("Could not fetch countries", e);
      }

      // static genre list
      COMMON_GENRES.sort().forEach(g=>{
        const o = document.createElement("option");
        o.value = g; o.textContent = g;
        document.getElementById("genreFilter").appendChild(o);
      });

      // trigger on change
      document.getElementById("genreFilter")
        .addEventListener("change", ()=> {
          const g = document.getElementById("genreFilter").value;
          if(g){
            document.getElementById("aiResult").textContent="";
            loadAndRender({ query: g, field: "tag" });
          } else {
            loadAndRender({ top: true });
          }
        });
      document.getElementById("countryFilter")
        .addEventListener("change", ()=> {
          // reapply last criterion
          const g = document.getElementById("genreFilter").value;
          if(g) loadAndRender({ query: g, field: "tag" });
          else loadAndRender({ top: true });
        });
      document.getElementById("sortBy")
        .addEventListener("change", ()=> {
          const g = document.getElementById("genreFilter").value;
          if(g) loadAndRender({ query: g, field: "tag" });
          else loadAndRender({ top: true });
        });
    }

    // generic loader
    async function loadAndRender(opts){
      document.getElementById("aiResult").textContent="";
      const resDiv = document.getElementById("results");
      resDiv.innerHTML = "<p class='loading'>Loading…</p>";

      const payload = {
        filter_dead: true,
        sort_by:     document.getElementById("sortBy").value,
        ...opts
      };

      try {
        const r = await fetch("https://simple-naomi-joewilcom-71ae2211.koyeb.app/search", {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body: JSON.stringify(payload)
        });
        if(!r.ok) throw "";
        let stations = await r.json();

        // country filter
        const cc = document.getElementById("countryFilter").value;
        if(cc) stations = stations.filter(s=>s.countrycode===cc);

        stations.sort((a,b)=>(b.votes||0)-(a.votes||0));
        renderStations(stations);
      } catch {
        resDiv.innerHTML = "<p class='loading'>Failed to load stations.</p>";
      }
    }

    // search w/ AI fallback
    async function search(){
      const raw = document.getElementById("query").value.trim();
      if(!raw) return;
      const sortBy = document.getElementById("sortBy").value;
      const aiEl   = document.getElementById("aiResult");

      document.getElementById("results").innerHTML = "<p class='loading'>Thinking…</p>";
      aiEl.textContent = "";

      let finalQuery = raw, field = "name";
      try {
        const r = await fetch("https://simple-naomi-joewilcom-71ae2211.koyeb.app/ai-query", {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({ query: raw })
        });
        const data = await r.json();
        if(data.tags){
          finalQuery = data.tags.trim();
          field = "tag";
          aiEl.innerHTML = `AI suggested tags: <strong>${finalQuery}</strong>`;
        }
      } catch {
        console.warn("AI refine failed");
      }

      let stations = await fetchStations(finalQuery, field, sortBy);
      if(field==="tag" && stations.length===0){
        aiEl.innerHTML = `No tag matches; searching names for: <strong>${raw}</strong>`;
        stations = await fetchStations(raw, "name", sortBy);
      }
      renderStations(stations);
    }

    // helper to call /search
    async function fetchStations(query, field, sortBy){
      const terms = field==="tag"
        ? query.split(",").map(s=>s.trim()).filter(Boolean)
        : query.split(/\s+/).filter(Boolean);

      const batches = await Promise.all(terms.map(term=>
        fetch("https://simple-naomi-joewilcom-71ae2211.koyeb.app/search", {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body: JSON.stringify({ query: term, field, sort_by: sortBy, filter_dead:true })
        }).then(r=>r.ok?r.json():[])
      ));

      const seen = new Map();
      batches.flat().forEach(s=>{
        const k = s.stationuuid||s.url_resolved;
        if(!seen.has(k)) seen.set(k,s);
      });

      return Array.from(seen.values())
                  .sort((a,b)=>(b.votes||0)-(a.votes||0))
                  .slice(0,50);
    }

    // render
    function renderStations(stations){
      const c = document.getElementById("results");
      c.innerHTML = "";
      if(!stations.length){
        c.innerHTML = "<p>No stations found. Try a broader search.</p>";
        return;
      }
      stations.forEach((s,i)=>{
        let url = s.url_resolved||"";
        if(url.startsWith("http://")) url=url.replace("http://","https://");
        if(!url.startsWith("https://")) return;

        const flag = countryCodeToFlag(s.countrycode);
        let card = document.createElement("div");
        card.className="card";
        const tagsArr = (s.tags||"").split(",").map(t=>t.trim()).filter(Boolean);
        const disp = tagsArr.slice(0,5);
        let tagsHTML = disp.map(t=>`<a class="tag">${t}</a>`).join(", ");
        if(tagsArr.length>5) tagsHTML += ", …";

        card.innerHTML = `
          <h3>#${i+1} ${s.name}</h3>
          <p class="meta">${flag} ${s.country||"Unknown country"}</p>
          <audio controls src="${url}"></audio>
          <p class="now-playing">Now playing: —</p>
          <p class="meta"><strong>Clicks:</strong> ${s.clickcount||0} | <strong>Votes:</strong> ${s.votes||0}</p>
          <p class="meta"><strong>Bitrate:</strong> ${s.bitrate||"?"} kbps | <strong>Codec:</strong> ${s.codec||"n/a"}</p>
          <p class="meta"><strong>Tags:</strong> ${tagsHTML||"—"}</p>
        `;
        c.appendChild(card);
      });

      twemoji.parse(document.body,{
        base:"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/",
        folder:"svg", ext:".svg"
      });

      document.querySelectorAll("audio").forEach(a=>
        a.addEventListener("play", ()=>document.querySelectorAll("audio").forEach(o=>{if(o!==a)o.pause();}))
      );
    }
  </script>
</body>
</html>
