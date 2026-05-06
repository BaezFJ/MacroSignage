(() => {
  const getPreferredTheme = () =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

  const setTheme = () => {
    document.documentElement.setAttribute("data-bs-theme", getPreferredTheme());
  };

  setTheme();
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", setTheme);

  const databaseSettings = document.querySelector("[data-database-settings]");
  if (databaseSettings) {
    const typeSelect = databaseSettings.querySelector("[data-database-type]");
    const driverMessage = databaseSettings.querySelector("[data-database-driver-message]");
    const installButton = databaseSettings.querySelector("[data-database-install-button]");
    const installCommand = databaseSettings.querySelector("[data-database-install-command]");
    const sections = Array.from(databaseSettings.querySelectorAll("[data-database-section]"));
    const portInput = databaseSettings.querySelector("#databasePort");

    const copyInstallCommand = () => {
      const command = installButton.dataset.command || "";
      if (!command) return;

      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(command).then(() => {
          installButton.textContent = "Copied";
          window.setTimeout(() => {
            installButton.textContent = "Copy install command";
          }, 2000);
        });
      } else {
        window.prompt("Copy this install command:", command);
      }
    };

    const syncDatabaseFields = () => {
      const selectedOption = typeSelect.options[typeSelect.selectedIndex];
      const databaseType = typeSelect.value;
      const sectionName = databaseType === "sqlite" || databaseType === "advanced" ? databaseType : "server";
      const command = selectedOption ? selectedOption.dataset.installCommand || "" : "";

      sections.forEach((section) => {
        const isVisible = section.dataset.databaseSection === sectionName;
        section.classList.toggle("d-none", !isVisible);
        section.querySelectorAll("input, select, textarea").forEach((field) => {
          field.disabled = !isVisible;
        });
      });

      if (driverMessage && selectedOption) {
        driverMessage.textContent = selectedOption.dataset.driverHelp || "";
      }
      if (installCommand) {
        installCommand.textContent = command;
        installCommand.classList.toggle("d-none", !command);
      }
      if (installButton) {
        installButton.dataset.command = command;
        installButton.classList.toggle("d-none", !command);
        installButton.textContent = "Copy install command";
      }
      if (portInput && selectedOption && sectionName === "server" && !portInput.value) {
        portInput.value = selectedOption.dataset.defaultPort || "";
      }
    };

    if (installButton) {
      installButton.addEventListener("click", copyInstallCommand);
    }
    typeSelect.addEventListener("change", syncDatabaseFields);
    syncDatabaseFields();
  }
})();
