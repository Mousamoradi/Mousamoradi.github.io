const papers = JSON.parse(document.getElementById("papers").textContent);
const list = document.getElementById("list");
const count = document.getElementById("count");
const search = document.getElementById("q");
const buttons = [...document.querySelectorAll("#filters button")];
const labels = { journal: "Journal", conference: "Conference", preprint: "Preprint", thesis: "Thesis", book: "Book" };
let kind = "all";

function esc(value) {
  return String(value ?? "").replaceAll("\u0026", "\u0026amp;").replaceAll("<", "\u0026lt;").replaceAll(">", "\u0026gt;").replaceAll('"', "\u0026quot;");
}

function render() {
  const q = search.value.trim().toLowerCase();
  const visible = papers.filter((paper) => {
    if (kind !== "all" && paper.kind !== kind) return false;
    if (!q) return true;
    return (paper.title + " " + paper.authors + " " + paper.venue).toLowerCase().includes(q);
  });
  count.textContent = "Showing " + visible.length + " of " + papers.length;
  list.innerHTML = visible.length
    ? visible.map((paper) => {
        const title = paper.href
          ? '<a href="' + esc(paper.href) + '" target="_blank" rel="noopener noreferrer">' + esc(paper.title) + ' <span aria-hidden="true">↗</span></a>'
          : esc(paper.title);
        const cites = paper.citations ? '<p class="cites">' + paper.citations + " citation" + (paper.citations === 1 ? "" : "s") + "</p>" : "";
        return '<article class="pub"><p class="year">' + paper.year + '</p><div><h3>' + title + '</h3><p class="muted">' + esc(paper.authors) + '</p><p class="soft">' + esc(paper.venue) + '</p></div><div class="pub-meta"><span class="kind">' + (labels[paper.kind] || esc(paper.kind)) + "</span>" + cites + "</div></article>";
      }).join("")
    : '<p class="empty">No records match that filter.</p>';
}

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    kind = button.dataset.kind;
    buttons.forEach((item) => item.setAttribute("aria-selected", item === button ? "true" : "false"));
    render();
  });
});
search.addEventListener("input", render);
render();
