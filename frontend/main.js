// =====================================================
// CONFIGURATION
// =====================================================

const BACKEND_URL = "https://sandeep-enterprises.onrender.com";

// =====================================================
// DOM ELEMENTS
// =====================================================

const inquiryForm = document.getElementById("inquiryForm");
const sendButton = document.getElementById("sendInquiry");
const previewGallery = document.getElementById("previewGallery");
const cadInput = document.getElementById("cadFile");
const imageInput = document.getElementById("productImages");
const uploadTypeInputs = document.querySelectorAll('input[name="upload_type"]');
const cadSection = document.getElementById("cadUploadSection");
const imageSection = document.getElementById("imageUploadSection");

// =====================================================
// APPLICATION STATE
// =====================================================

let currentUploadType = "CAD";
let selectedCAD = null;
let selectedImages = [];

// =====================================================
// PREVIEW HELPERS
// =====================================================

function clearGallery() {
    if (previewGallery) {
        previewGallery.innerHTML = "";
    }
}

function createImageCard(imageSrc, title) {
    if (!previewGallery) return;

    const card = document.createElement("div");
    card.className = "bg-white border rounded-xl shadow-sm overflow-hidden";
    card.innerHTML = `
        <img
            src="${imageSrc}"
            alt="${title}"
            class="w-full h-44 object-contain bg-gray-100"
        >
        <div class="p-3 text-center font-semibold text-sm text-gray-700 truncate" title="${title}">
            ${title}
        </div>
    `;
    previewGallery.appendChild(card);
}

function createCADCard(file) {
    if (!previewGallery || !file) return;

    const extension = file.name.split(".").pop().toUpperCase();
    const card = document.createElement("div");
    card.className = "col-span-full bg-white border rounded-xl shadow-sm p-8 text-center";
    card.innerHTML = `
        <div class="text-5xl mb-3">
            📐
        </div>
        <h3 class="text-xl font-bold text-gray-900">
            CAD File Selected
        </h3>
        <p class="mt-3 text-gray-600 font-medium break-all">
            ${file.name}
        </p>
        <span class="inline-block mt-3 px-4 py-1.5 rounded-full bg-blue-100 text-blue-700 font-semibold text-sm">
            ${extension}
        </span>
        <p class="mt-4 text-sm text-gray-500">
            The CAD model will be rendered automatically after you submit your inquiry.
        </p>
    `;
    previewGallery.appendChild(card);
}

// =====================================================
// UPLOAD AREA TOGGLE
// =====================================================

function updateUploadVisibility() {
    const activeRadio = document.querySelector('input[name="upload_type"]:checked');
    if (activeRadio) {
        currentUploadType = activeRadio.value.toUpperCase();
    }

    if (cadSection && imageSection) {
        if (currentUploadType === "CAD") {
            cadSection.classList.remove("hidden");
            imageSection.classList.add("hidden");
        } else {
            imageSection.classList.remove("hidden");
            cadSection.classList.add("hidden");
        }
    }
}

// =====================================================
// EVENT LISTENERS: FILE INPUTS
// =====================================================

if (cadInput) {
    cadInput.addEventListener("change", function () {
        clearGallery();
        selectedCAD = null;

        if (!this.files || !this.files.length) return;

        selectedCAD = this.files[0];
        createCADCard(selectedCAD);
    });
}

if (imageInput) {
    imageInput.addEventListener("change", function () {
        clearGallery();
        selectedImages = [];

        if (!this.files || !this.files.length) return;

        Array.from(this.files).forEach(file => {
            selectedImages.push(file);

            const reader = new FileReader();
            reader.onload = function (e) {
                createImageCard(e.target.result, file.name);
            };
            reader.readAsDataURL(file);
        });
    });
}

// =====================================================
// EVENT LISTENERS: RADIO BUTTONS
// =====================================================

uploadTypeInputs.forEach(radio => {
    radio.addEventListener("change", function () {
        currentUploadType = this.value.toUpperCase();
        selectedCAD = null;
        selectedImages = [];

        if (cadInput) cadInput.value = "";
        if (imageInput) imageInput.value = "";

        clearGallery();
        updateUploadVisibility();
    });
});

// =====================================================
// SUBMIT INQUIRY
// =====================================================

async function submitInquiry() {
    const nameInput = document.getElementById("name");
    const companyInput = document.getElementById("company");
    const emailInput = document.getElementById("email");
    const phoneInput = document.getElementById("phone");
    const cityInput = document.getElementById("city");
    const stateInput = document.getElementById("state");
    const messageInput = document.getElementById("message");

    const name = nameInput ? nameInput.value.trim() : "";
    const company = companyInput ? companyInput.value.trim() : "";
    const email = emailInput ? emailInput.value.trim() : "";
    const phone = phoneInput ? phoneInput.value.trim() : "";
    const city = cityInput ? cityInput.value.trim() : "";
    const state = stateInput ? stateInput.value.trim() : "";
    const message = messageInput ? messageInput.value.trim() : "";

    // Client-side field validations
    if (!name) {
        throw new Error("Please enter your full name.");
    }
    if (!email) {
        throw new Error("Please enter your email address.");
    }
    if (!phone) {
        throw new Error("Please enter your phone number.");
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("company", company);
    formData.append("email", email);
    formData.append("phone", phone);
    formData.append("city", city);
    formData.append("state", state);
    formData.append("message", message);
    formData.append("upload_type", currentUploadType);

    // Attach Files
    if (currentUploadType === "CAD") {
        const fileToUpload = selectedCAD || (cadInput && cadInput.files && cadInput.files[0]);
        if (!fileToUpload) {
            throw new Error("Please select a CAD file.");
        }
        formData.append("cad_file", fileToUpload);
    } else {
        const imagesToUpload = selectedImages.length > 0 ? selectedImages : (imageInput && imageInput.files ? Array.from(imageInput.files) : []);
        if (imagesToUpload.length === 0) {
            throw new Error("Please upload at least one product image.");
        }
        imagesToUpload.forEach(image => {
            formData.append("product_images", image);
        });
    }

    if (sendButton) {
        sendButton.disabled = true;
        sendButton.innerText = "Submitting Inquiry...";
    }

    try {
        const response = await fetch(`${BACKEND_URL}/submit-inquiry`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "Submission failed.");
        }

        return result;
    } finally {
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerText = "SEND MANUFACTURING INQUIRY";
        }
    }
}

// =====================================================
// FORM SUBMIT EVENT
// =====================================================

if (inquiryForm) {
    inquiryForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        try {
            const result = await submitInquiry();

            if (result && result.inquiry_id) {
                alert(`Inquiry submitted successfully.\n\nReference ID: ${result.inquiry_id}`);

                inquiryForm.reset();
                selectedCAD = null;
                selectedImages = [];
                currentUploadType = "CAD";

                const cadRadio = document.getElementById("cadOption");
                if (cadRadio) cadRadio.checked = true;

                clearGallery();
                updateUploadVisibility();
            }
        } catch (error) {
            console.error("Inquiry Error:", error);
            alert("Unable to submit inquiry.\n\n" + (error.message || "An unexpected error occurred."));
        }
    });
}

// =====================================================
// INITIAL PAGE LOAD
// =====================================================

document.addEventListener("DOMContentLoaded", function () {
    updateUploadVisibility();
});
