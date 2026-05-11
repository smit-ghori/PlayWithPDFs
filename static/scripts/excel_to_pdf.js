document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("mergeForm");

  form.addEventListener("submit", function (e) {
    // Extra Excel-specific validation

    const maxSize = 10 * 1024 * 1024; // 10 MB

    for (let file of selectedFiles) {
      if (file.size > maxSize) {
        e.preventDefault();

        alert(`${file.name} exceeds 10 MB limit.`);
        return;
      }
    }
  });
});