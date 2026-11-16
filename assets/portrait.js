const img = document.querySelector('.portrait img');
if (img) {
  const names = ['assets/c0.txt', 'assets/c1.txt', 'assets/c2.txt', 'assets/c3.txt', 'assets/c4.txt', 'assets/c5.txt'];
  Promise.all(names.map((name) => fetch(name).then((r) => r.text()))).then((parts) => {
    img.src = 'data:image/jpeg;base64,' + parts.join('').replace(/\s/g, '');
  });
}
