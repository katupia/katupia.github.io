// "URL" buttons on the gallery tiles: copy the absolute image URL.
document.addEventListener("click", async (ev) => {
  const btn = ev.target.closest(".copy");
  if (!btn) return;
  try {
    await navigator.clipboard.writeText(btn.dataset.url);
    btn.classList.add("done");
    btn.textContent = "Copied";
    setTimeout(() => { btn.classList.remove("done"); btn.textContent = "URL"; }, 1400);
  } catch (e) {
    window.prompt("Image URL", btn.dataset.url);
  }
});
