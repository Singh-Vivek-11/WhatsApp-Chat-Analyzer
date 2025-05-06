document.getElementById("chatForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const fileInput = document.getElementById("chatFile");
    const file = fileInput.files[0];
    if (!file) return;
  
    document.getElementById("loading").style.display = "block";
    document.getElementById("results-section").style.display = "none";
  
    const reader = new FileReader();
    reader.onload = function (event) {
      const text = event.target.result;
      const stats = analyzeChat(text);
      renderStats(stats);
      document.getElementById("loading").style.display = "none";
      document.getElementById("results-section").style.display = "block";
    };
    reader.readAsText(file);
  });
  
  function analyzeChat(text) {
    const lines = text.split("\n");
    let totalMessages = 0, totalWords = 0, mediaShared = 0, linksShared = 0;
    const participants = {}, words = {}, emojis = {};
  
    for (let line of lines) {
      const parts = line.split(" - ");
      if (parts.length < 2) continue;
      const msgParts = parts[1].split(": ");
      if (msgParts.length < 2) continue;
  
      const sender = msgParts[0];
      const message = msgParts.slice(1).join(": ");
  
      totalMessages++;
      participants[sender] = (participants[sender] || 0) + 1;
  
      const wordList = message.split(/\s+/).filter(w => w.length > 0);
      totalWords += wordList.length;
  
      wordList.forEach(word => {
        const cleanWord = word.toLowerCase().replace(/[.,!?]/g, '');
        words[cleanWord] = (words[cleanWord] || 0) + 1;
  
        if (/https?:\/\/\S+/.test(cleanWord)) linksShared++;
      });
  
      if (message.includes("<Media omitted>")) mediaShared++;
  
      const emojiMatch = message.match(/([\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}])/gu);
      if (emojiMatch) {
        emojiMatch.forEach(e => emojis[e] = (emojis[e] || 0) + 1);
      }
    }
  
    return { totalMessages, totalWords, mediaShared, linksShared, participants, words, emojis };
  }
  
  function renderStats(data) {
    document.getElementById("totalMessages").textContent = data.totalMessages;
    document.getElementById("totalWords").textContent = data.totalWords;
    document.getElementById("mediaShared").textContent = data.mediaShared;
    document.getElementById("linksShared").textContent = data.linksShared;
  
    const topParticipants = Object.entries(data.participants)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    const container = document.getElementById("participantsContainer");
    container.innerHTML = "";
    topParticipants.forEach(([name, count]) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      li.innerHTML = `<span>${name}</span><span class="badge bg-primary">${count}</span>`;
      container.appendChild(li);
    });
  
    const topWords = Object.entries(data.words)
      .filter(([word]) => word.length > 3 && !["media", "omitted"].includes(word))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    const wordCtx = document.getElementById("wordsChart").getContext("2d");
    new Chart(wordCtx, {
      type: 'bar',
      data: {
        labels: topWords.map(w => w[0]),
        datasets: [{
          label: "Top Words",
          data: topWords.map(w => w[1]),
          backgroundColor: "#28a745"
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    });
  
    const topEmojis = Object.entries(data.emojis)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);
    const emojiCtx = document.getElementById("emojiChart").getContext("2d");
    new Chart(emojiCtx, {
      type: 'pie',
      data: {
        labels: topEmojis.map(e => e[0]),
        datasets: [{
          label: "Emoji Usage",
          data: topEmojis.map(e => e[1]),
          backgroundColor: ["#ff6384", "#36a2eb", "#ffce56", "#4bc0c0", "#9966ff", "#ff9f40", "#8e44ad", "#2ecc71"]
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }
  
  document.getElementById("resetBtn").addEventListener("click", () => {
    document.getElementById("chatFile").value = "";
    document.getElementById("fileNameDisplay").textContent = "";
    document.getElementById("results-section").style.display = "none";
    document.getElementById("upload-section").style.display = "block";
  });
  