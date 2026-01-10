const BASE_URL =
  import.meta.env.VITE_API_URL ||
  "https://careflownexusbackend.onrender.com/api/v1";

class ApiClient {
  constructor() {
    this.baseUrl = BASE_URL;
    console.log(`API Client initialized with base URL: ${this.baseUrl}`);
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    console.log(`[ApiClient] Requesting: ${url}`); // DEBUG: Trace URL
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage =
          typeof errorData.detail === "object"
            ? JSON.stringify(errorData.detail)
            : errorData.detail ||
            `Request failed with status ${response.status}`;
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // ==================== AUTH ====================
  async login(username, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  // ==================== PATIENTS ====================
  async createPatient(patientData) {
    // patientData: { user_id, name, age, gender, medical_history, special_needs }
    return this.request("/patients", {
      method: "POST",
      body: JSON.stringify(patientData),
    });
  }

  async getPatients(userId) {
    return this.request(`/patients?user_id=${userId}`);
  }

  async getPendingConfirmations(userId) {
    // For receptionists: patients waiting for bed confirmation
    return this.request(`/patients/pending-confirmation?user_id=${userId}`);
  }

  // ==================== ADMISSION ====================
  async admitPatient(patientId, admissionData) {
    // admissionData: { user_id, diagnosis, special_instructions }
    return this.request(`/patients/${patientId}/admission`, {
      method: "POST",
      body: JSON.stringify(admissionData),
    });
  }

  async confirmBed(patientId, confirmationData) {
    // confirmationData: { user_id, bed_id }
    return this.request(`/patients/${patientId}/confirm-bed`, {
      method: "POST",
      body: JSON.stringify(confirmationData),
    });
  }

  async dischargePatient(patientId, userId) {
    // Request discharge for a patient
    return this.request(`/patients/${patientId}/discharge`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    });
  }

  // ==================== TASKS ====================
  async getTasks(userId) {
    console.log(`[ApiClient] Fetching tasks for User: ${userId}`);
    return this.request(`/tasks?user_id=${userId}`);
  }

  async acceptTask(taskId, userId) {
    console.log(`[ApiClient] Accepting Task ${taskId} for User: ${userId}`);
    return this.request(`/tasks/${taskId}/accept`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    });
  }

  async completeTask(taskId, userId, notes = "") {
    console.log(`[ApiClient] Completing Task ${taskId} for User: ${userId}`);
    return this.request(`/tasks/${taskId}/complete`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, notes }),
    });
  }

  // ==================== ADMIN ====================
  async getAdminBeds(userId) {
    return this.request(`/admin/beds?user_id=${userId}`);
  }

  async getAdminTasks(userId) {
    return this.request(`/admin/tasks?user_id=${userId}`);
  }

  async getAdminNurses(userId) {
    return this.request(`/admin/nurses?user_id=${userId}`);
  }

  async getAdminCleaners(userId) {
    return this.request(`/admin/cleaners?user_id=${userId}`);
  }
}

export const api = new ApiClient();
