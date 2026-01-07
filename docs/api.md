# QR Code Genius API Documentation

Welcome to the official API documentation for QR Code Genius. This API allows programmatic interaction with the platform to generate, manage, and download QR codes. It is designed for secure, efficient, and reliable integration.

## Base URL

All API requests should be prefixed with the base URL of your deployed application.
Example: `https://api.qrcodegenius.com` (replace with your actual domain)

## Authentication

The QR Code Genius API uses session-based authentication managed by Flask-Login. After a successful login, the server sets a secure HTTP-only cookie (`session`) in the user's browser. Subsequent API requests from the same client will automatically include this session cookie, authenticating the user.

**Important Considerations:**
*   This API is primarily designed for browser-based clients that handle cookies automatically.
*   For non-browser clients (e.g., mobile apps, server-to-server integrations), you would typically need to manage the session cookie manually after the initial login, or implement a token-based authentication system (e.g., JWT) which is not currently specified but could be a future enhancement.
*   All authenticated endpoints require an active session. If a request is made without a valid session, a `401 Unauthorized` response will be returned.

## Error Handling

The API returns standard HTTP status codes to indicate the success or failure of a request.
Error responses are typically JSON formatted and include a `message` field describing the error, and sometimes an `errors` field for validation issues.

**Common Error Codes:**
*   `200 OK`: The request was successful.
*   `201 Created`: A new resource was successfully created.
*   `400 Bad Request`: The request was malformed or invalid.
*   `401 Unauthorized`: Authentication is required or has failed.
*   `403 Forbidden`: The authenticated user does not have permission to access the resource.
*   `404 Not Found`: The requested resource could not be found.
*   `405 Method Not Allowed`: The HTTP method used is not supported for this endpoint.
*   `409 Conflict`: The request could not be completed due to a conflict with the current state of the resource (e.g., user already exists).
*   `500 Internal Server Error`: An unexpected error occurred on the server.

---

## API Endpoints

### 1. User Authentication

#### 1.1 Register a new user

*   **Endpoint:** `/api/register`
*   **Method:** `POST`
*   **Description:** Creates a new user account.
*   **Authentication:** None (public endpoint)

*   **Request Body (JSON):**
    
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    
    *   `email` (string, required): The user's email address. Must be a valid email format and unique.
    *   `password` (string, required): The user's desired password. Minimum length requirements may apply.

*   **Response (Success - 201 Created):**
    
    {
        "message": "User registered successfully",
        "user_id": 123,
        "email": "user@example.com"
    }
    

*   **Response (Error - 400 Bad Request / 409 Conflict):**
    
    {
        "message": "Validation error",
        "errors": {
            "email": "Invalid email format",
            "password": "Password must be at least 8 characters long"
        }
    }
    
    
    {
        "message": "User with this email already exists."
    }
    

*   **Example (cURL):**
    bash
    curl -X POST -H "Content-Type: application/json" \
         -d '{"email": "testuser@example.com", "password": "MyStrongPassword123"}' \
         https://api.qrcodegenius.com/api/register
    

#### 1.2 Log in a user

*   **Endpoint:** `/api/login`
*   **Method:** `POST`
*   **Description:** Authenticates a user and establishes a session.
*   **Authentication:** None (public endpoint)

*   **Request Body (JSON):**
    
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    
    *   `email` (string, required): The user's email address.
    *   `password` (string, required): The user's password.

*   **Response (Success - 200 OK):**
    
    {
        "message": "Login successful",
        "user_id": 123,
        "email": "user@example.com"
    }
    
    *(Note: A `Set-Cookie` header will be included in the response to establish the session.)*

*   **Response (Error - 401 Unauthorized):**
    
    {
        "message": "Invalid email or password"
    }
    

*   **Example (cURL):**
    bash
    curl -X POST -H "Content-Type: application/json" \
         -d '{"email": "testuser@example.com", "password": "MyStrongPassword123"}' \
         -c cookiejar.txt \
         https://api.qrcodegenius.com/api/login
    
    *(The `-c cookiejar.txt` option saves the session cookie for subsequent requests.)*

#### 1.3 Log out a user

*   **Endpoint:** `/api/logout`
*   **Method:** `POST`
*   **Description:** Logs out the current user, ending their session.
*   **Authentication:** Required (active session)

*   **Request Body:** None

*   **Response (Success - 200 OK):**
    
    {
        "message": "Logged out successfully"
    }
    
    *(Note: The session cookie will be invalidated.)*

*   **Response (Error - 401 Unauthorized):**
    
    {
        "message": "Authentication required"
    }
    

*   **Example (cURL):**
    bash
    curl -X POST -H "Content-Type: application/json" \
         -b cookiejar.txt \
         https://api.qrcodegenius.com/api/logout
    
    *(The `-b cookiejar.txt` option sends the previously saved session cookie.)*

---

### 2. QR Code Generation

#### 2.1 Generate a new QR Code

*   **Endpoint:** `/api/generate_qr`
*   **Method:** `POST`
*   **Description:** Generates a new QR code for a given URL.
*   **Authentication:** Required (active session)

*   **Request Body (JSON):**
    
    {
        "target_url": "https://www.example.com",
        "format": "PNG"
    }
    
    *   `target_url` (string, required): The URL that the QR code should point to. Must be a valid HTTP/HTTPS URL.
    *   `format` (string, optional): The desired image format for the QR code.
        *   `"PNG"` (default): High-resolution PNG image.
        *   `"SVG"`: Scalable Vector Graphics.
        *   *Note: Other formats might be supported in future versions.*

*   **Response (Success - 201 Created):**
    
    {
        "message": "QR code generated successfully",
        "qr_code": {
            "id": 12345,
            "target_url": "https://www.example.com",
            "generated_at": "2023-10-27T10:30:00Z",
            "download_url": "https://api.qrcodegenius.com/download_qr/12345",
            "image_filename": "qr_code_1678886400_123_example.png"
        }
    }
    

*   **Response (Error - 400 Bad Request):**
    
    {
        "message": "Validation error",
        "errors": {
            "target_url": "Invalid URL format or unsupported protocol."
        }
    }
    
    
    {
        "message": "Invalid image format specified."
    }
    

*   **Response (Error - 401 Unauthorized):**
    
    {
        "message": "Authentication required"
    }
    

*   **Example (cURL):**
    bash
    curl -X POST -H "Content-Type: application/json" \
         -b cookiejar.txt \
         -d '{"target_url": "https://www.google.com", "format": "PNG"}' \
         https://api.qrcodegenius.com/api/generate_qr
    

---

### 3. QR Code Management

#### 3.1 Get all generated QR codes for the current user

*   **Endpoint:** `/api/my_qrs`
*   **Method:** `GET`
*   **Description:** Retrieves a list of all QR codes generated by the authenticated user.
*   **Authentication:** Required (active session)

*   **Request Parameters:** None

*   **Response (Success - 200 OK):**
    
    {
        "message": "QR codes retrieved successfully",
        "qr_codes": [
            {
                "id": 12345,
                "target_url": "https://www.example.com",
                "generated_at": "2023-10-27T10:30:00Z",
                "download_url": "https://api.qrcodegenius.com/download_qr/12345",
                "image_filename": "qr_code_1678886400_123_example.png"
            },
            {
                "id": 12346,
                "target_url": "https://www.another-site.org",
                "generated_at": "2023-10-27T11:00:00Z",
                "download_url": "https://api.qrcodegenius.com/download_qr/12346",
                "image_filename": "qr_code_1678888200_123_anothersite.svg"
            }
        ]
    }
    
    *(Note: The list will be empty if the user has not generated any QR codes.)*

*   **Response (Error - 401 Unauthorized):**
    
    {
        "message": "Authentication required"
    }
    

*   **Example (cURL):**
    bash
    curl -X GET -H "Content-Type: application/json" \
         -b cookiejar.txt \
         https://api.qrcodegenius.com/api/my_qrs
    

#### 3.2 Delete a specific QR code

*   **Endpoint:** `/api/delete_qr/<qr_id>`
*   **Method:** `DELETE`
*   **Description:** Deletes a QR code owned by the authenticated user.
*   **Authentication:** Required (active session)

*   **URL Parameters:**
    *   `qr_id` (integer, required): The unique identifier of the QR code to be deleted.

*   **Request Body:** None

*   **Response (Success - 200 OK):**
    
    {
        "message": "QR code 12345 deleted successfully"
    }
    

*   **Response (Error - 401 Unauthorized):**
    
    {
        "message": "Authentication required"
    }
    

*   **Response (Error - 403 Forbidden):**
    
    {
        "message": "You do not have permission to delete this QR code."
    }
    
    *(This occurs if the `qr_id` belongs to another user.)*

*   **Response (Error - 404 Not Found):**
    
    {
        "message": "QR code with ID 99999 not found."
    }
    

*   **Example (cURL):**
    bash
    curl -X DELETE -H "Content-Type: application/json" \
         -b cookiejar.txt \
         https://api.qrcodegenius.com/api/delete_qr/12345
    

---

### 4. QR Code Download

#### 4.1 Download a specific QR code image

*   **Endpoint:** `/download_qr/<qr_id>`
*   **Method:** `GET`
*   **Description:** Serves the generated QR code image file for download.
*   **Authentication:** Required (active session)

*   **URL Parameters:**
    *   `qr_id` (integer, required): The unique identifier of the QR code to download.

*   **Request Parameters:** None

*   **Response (Success - 200 OK):**
    *   Returns the QR code image file directly.
    *   `Content-Type` header will be `image/png` or `image/svg+xml` depending on the format.
    *   `Content-Disposition` header will typically suggest a filename for download.

*   **Response (Error - 401 Unauthorized):**
    
    {
        "message": "Authentication required"
    }
    

*   **Response (Error - 403 Forbidden):**
    
    {
        "message": "You do not have permission to download this QR code."
    }
    
    *(This occurs if the `qr_id` belongs to another user.)*

*   **Response (Error - 404 Not Found):**
    
    {
        "message": "QR code with ID 99999 not found."
    }
    
    *(This can also occur if the QR code exists but its associated file is missing on the server.)*

*   **Example (cURL):**
    bash
    curl -X GET -b cookiejar.txt \
         -o qr_code_12345.png \
         https://api.qrcodegenius.com/download_qr/12345
    
    *(The `-o` option saves the downloaded file.)*