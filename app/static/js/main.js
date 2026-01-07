/**
 * Main JavaScript file for client-side interactivity, dynamic elements, and form validation
 * for the QR Code Genius application.
 *
 * This script handles:
 * - QR Code generation form submission via AJAX.
 * - Client-side validation for URLs, email, and passwords.
 * - Displaying dynamic content like generated QR codes and error messages.
 * - User authentication form submissions (login, registration).
 * - QR code deletion from the user dashboard.
 * - General UI enhancements like navigation toggles and toast notifications.
 *
 * It assumes the presence of a CSRF token in a meta tag: `<meta name="csrf-token" content="{{ csrf_token() }}">`
 * and a toast container element: `<div id="toast-container" class="fixed top-4 right-4 z-50 w-full max-w-xs"></div>`
 * in the base HTML template for proper functionality.
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Utility Functions ---

    /**
     * Displays a toast notification to the user.
     * @param {string} message - The message to display.
     * @param {'success'|'error'|'info'} type - The type of toast (determines styling).
     * @param {number} duration - How long the toast should be visible in milliseconds. Default is 5000ms.
     */
    function showToast(message, type = 'info', duration = 5000) {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.error('Toast container not found. Please add <div id="toast-container"></div> to your HTML.');
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast-notification p-3 rounded-md shadow-lg mb-3 flex items-center justify-between transition-opacity duration-300 ease-out opacity-0 transform translate-y-2`;

        let bgColor = '';
        let textColor = 'text-white';
        let iconHtml = '';

        switch (type) {
            case 'success':
                bgColor = 'bg-green-500';
                iconHtml = `<svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
                break;
            case 'error':
                bgColor = 'bg-red-600';
                iconHtml = `<svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
                break;
            case 'info':
            default:
                bgColor = 'bg-blue-500';
                iconHtml = `<svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
                break;
        }

        toast.innerHTML = `
            <div class="flex items-center">
                ${iconHtml}
                <span class="${textColor}">${message}</span>
            </div>
            <button class="ml-4 text-white hover:text-gray-200 close-toast-btn">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        `;
        toast.classList.add(bgColor);
        toastContainer.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.remove('opacity-0', 'translate-y-2');
            toast.classList.add('opacity-100', 'translate-y-0');
        }, 10); // Small delay for CSS transition to apply

        const dismissToast = () => {
            toast.classList.remove('opacity-100', 'translate-y-0');
            toast.classList.add('opacity-0', 'translate-y-2');
            toast.addEventListener('transitionend', () => toast.remove());
        };

        // Auto-dismiss
        const timeoutId = setTimeout(dismissToast, duration);

        // Manual dismiss
        toast.querySelector('.close-toast-btn').addEventListener('click', () => {
            clearTimeout(timeoutId); // Prevent auto-dismiss if manually closed
            dismissToast();
        });
    }

    /**
     * Shows a loading indicator on a given button or element.
     * It stores the original text in a dataset attribute and replaces the content with a spinner.
     * @param {HTMLElement} element - The button or element to show loading on.
     * @returns {string|undefined} The original text of the button/element, or undefined if element is null.
     */
    function showLoading(element) {
        if (!element) return;
        const originalText = element.textContent;
        element.dataset.originalText = originalText; // Store original text
        element.disabled = true;
        element.classList.add('relative'); // For spinner positioning
        element.innerHTML = `<span class="opacity-0">${originalText}</span><span class="absolute inset-0 flex items-center justify-center"><svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></span>`;
        return originalText;
    }

    /**
     * Hides the loading indicator and restores the original text of the element.
     * @param {HTMLElement} element - The button or element to hide loading from.
     */
    function hideLoading(element) {
        if (!element) return;
        element.disabled = false;
        element.innerHTML = element.dataset.originalText || 'Submit'; // Restore original text
        element.classList.remove('relative');
        delete element.dataset.originalText; // Clean up
    }

    /**
     * Basic client-side URL validation.
     * Uses the URL constructor to validate the format and checks for http/https protocols.
     * @param {string} urlString - The URL string to validate.
     * @returns {boolean} True if the URL is valid, false otherwise.
     */
    function isValidUrl(urlString) {
        try {
            const url = new URL(urlString);
            // Check for http/https protocols and a non-empty hostname
            return (url.protocol === 'http:' || url.protocol === 'https:') && url.hostname.length > 0;
        } catch (e) {
            return false;
        }
    }

    /**
     * Displays a server-side error message to the user within a specific HTML element.
     * If the element is not provided, it falls back to showing a toast notification.
     * @param {HTMLElement} errorElement - The HTML element to display the error in.
     * @param {string} message - The error message.
     */
    function displayErrorMessage(errorElement, message) {
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        } else {
            showToast(message, 'error');
        }
    }

    /**
     * Clears a displayed error message from an HTML element.
     * @param {HTMLElement} errorElement - The HTML element containing the error message.
     */
    function clearErrorMessage(errorElement) {
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.classList.add('hidden');
        }
    }

    // --- Navigation Toggle (for mobile responsiveness) ---
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('hidden');
        });
    }

    // --- QR Code Generation Form Handler ---
    const qrForm = document.getElementById('qr-generation-form');
    if (qrForm) {
        const urlInput =