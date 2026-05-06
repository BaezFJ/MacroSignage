(() => {
  const getPreferredTheme = () =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

  const setTheme = () => {
    document.documentElement.setAttribute("data-bs-theme", getPreferredTheme());
  };

  setTheme();
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", setTheme);
})();
