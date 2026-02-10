document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  
  // Modal elements
  const signupModal = document.getElementById("signup-modal");
  const confirmModal = document.getElementById("confirm-modal");
  const alertModal = document.getElementById("alert-modal");
  const fab = document.getElementById("fab");

  // Modal state
  let confirmCallback = null;

  // Custom confirm dialog
  function showConfirm(message, title = "Confirm Action") {
    return new Promise((resolve) => {
      const confirmTitle = document.getElementById("confirm-title");
      const confirmMessage = document.getElementById("confirm-message");
      
      confirmTitle.textContent = title;
      confirmMessage.textContent = message;
      confirmModal.classList.remove("hidden");
      
      confirmCallback = resolve;
    });
  }

  // Custom alert dialog
  function showAlert(message, title = "Notification") {
    return new Promise((resolve) => {
      const alertTitle = document.getElementById("alert-title");
      const alertMessage = document.getElementById("alert-message");
      
      alertTitle.textContent = title;
      alertMessage.textContent = message;
      alertModal.classList.remove("hidden");
      
      const okBtn = document.getElementById("alert-ok");
      const closeBtn = document.getElementById("close-alert-modal");
      
      const cleanup = () => {
        alertModal.classList.add("hidden");
        okBtn.removeEventListener("click", handleOk);
        closeBtn.removeEventListener("click", handleOk);
        resolve();
      };
      
      const handleOk = () => cleanup();
      
      okBtn.addEventListener("click", handleOk);
      closeBtn.addEventListener("click", handleOk);
    });
  }

  // Confirm modal handlers
  document.getElementById("confirm-ok").addEventListener("click", () => {
    confirmModal.classList.add("hidden");
    if (confirmCallback) {
      confirmCallback(true);
      confirmCallback = null;
    }
  });

  document.getElementById("confirm-cancel").addEventListener("click", () => {
    confirmModal.classList.add("hidden");
    if (confirmCallback) {
      confirmCallback(false);
      confirmCallback = null;
    }
  });

  document.getElementById("close-confirm-modal").addEventListener("click", () => {
    confirmModal.classList.add("hidden");
    if (confirmCallback) {
      confirmCallback(false);
      confirmCallback = null;
    }
  });

  // Close modals on backdrop click
  [signupModal, confirmModal, alertModal].forEach(modal => {
    modal.querySelector(".modal-backdrop").addEventListener("click", () => {
      modal.classList.add("hidden");
      if (modal === confirmModal && confirmCallback) {
        confirmCallback(false);
        confirmCallback = null;
      }
    });
  });

  // FAB button handler
  fab.addEventListener("click", () => {
    signupModal.classList.remove("hidden");
  });

  // Close signup modal handlers
  document.getElementById("close-signup-modal").addEventListener("click", () => {
    signupModal.classList.add("hidden");
  });

  document.getElementById("cancel-signup").addEventListener("click", () => {
    signupModal.classList.add("hidden");
  });

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Create participants list HTML
        let participantsList = '';
        if (details.participants.length > 0) {
          participantsList = `
            <div class="participants-section">
              <strong>Participants (${details.participants.length})</strong>
              <ul class="participants-list">
                ${details.participants.map(email => `
                  <li>
                    <span class="participant-email">${email}</span>
                    <button class="delete-btn" data-activity="${name}" data-email="${email}" title="Remove participant">Remove</button>
                  </li>
                `).join('')}
              </ul>
            </div>
          `;
        } else {
          participantsList = `
            <div class="participants-section">
              <strong>Participants</strong>
              <p class="no-participants">No participants yet. Be the first to sign up!</p>
            </div>
          `;
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spot${spotsLeft !== 1 ? 's' : ''} left</p>
          ${participantsList}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to all delete buttons
      document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', handleDeleteParticipant);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle delete participant
  async function handleDeleteParticipant(event) {
    const button = event.target;
    const activity = button.dataset.activity;
    const email = button.dataset.email;

    const confirmed = await showConfirm(
      `Are you sure you want to remove ${email} from ${activity}?`,
      "Remove Participant"
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        // Refresh the activities list
        activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
        await fetchActivities();
        
        await showAlert(result.message, "Success");
      } else {
        await showAlert(result.detail || "An error occurred", "Error");
      }
    } catch (error) {
      await showAlert("Failed to unregister. Please try again.", "Error");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        signupForm.reset();
        signupModal.classList.add("hidden");
        
        // Refresh the activities list
        activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
        await fetchActivities();
        
        await showAlert(result.message, "Success");
      } else {
        await showAlert(result.detail || "An error occurred", "Error");
      }
    } catch (error) {
      await showAlert("Failed to sign up. Please try again.", "Error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
