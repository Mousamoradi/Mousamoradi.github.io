const img = document.querySelector(".portrait img");
if (img) {
  const names = ['assets/p0.txt', 'assets/p1.txt', 'assets/p2.txt', 'assets/p3.txt', 'assets/p4.txt', 'assets/p5.txt', 'assets/p6.txt', 'assets/p7.txt'];
  Promise.all(names.map((name) => fetch(name).then((r) => r.text()))).then((parts) => {
    img.src = "data:image/jpeg;base64," + parts.join("").replace(/\s/g, "");
  });
}
