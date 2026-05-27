async function loadLatest() {
  const target = document.getElementById('latest');
  try {
    const response = await fetch('data/latest.json');
    if (!response.ok) throw new Error('latest.json niet gevonden');
    const data = await response.json();
    target.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    target.textContent = 'Nog geen gepubliceerde data beschikbaar.';
  }
}

loadLatest();
