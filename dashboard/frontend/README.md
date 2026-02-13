# BookFlow Frontend Dashboard

This is the frontend dashboard for the BookFlow project, built with React, Tailwind CSS, and Firebase.

## Prerequisites

- Node.js (v18+ recommended)
- npm or yarn

## Getting Started

1.  **Install dependencies:**
    ```bash
    npm install
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the root of the `frontend` directory (if not already present). You need to define the backend API URL.
    ```env
    VITE_BACKEND_API_URL=http://localhost:8080 # Or your deployed backend URL
    ```
    *Note: Firebase configuration is currently in `src/firebaseConfig.js`.*

3.  **Run the development server:**
    ```bash
    npm run dev
    ```
    The app will be available at `http://localhost:5173`.

## Project Structure

-   `src/components`: React components (BookList, ImageUpload, Login, etc.)
-   `src/context`: React Context providers (AuthContext)
-   `src/hooks`: Custom React hooks (useBooks, useConditionAssessment)
-   `src/firebaseConfig.js`: Firebase initialization
-   `src/App.jsx`: Main application component with routing

## Features

-   **User Authentication:** Login and Registration via Firebase Auth.
-   **Book Management:** View, filter, and delete books in your inventory.
-   **Image Upload:** Upload book images for AI analysis.
-   **Condition Assessment:** Detailed view of book condition and grading.
-   **Real-time Updates:** UI updates automatically via Firestore listeners.

## Technologies

-   **React:** UI Library
-   **Vite:** Build tool
-   **Tailwind CSS:** Styling
-   **Firebase:** Authentication and Firestore Database
-   **React Router:** Navigation
-   **React Hot Toast:** Notifications

## Deployment

To deploy to Firebase Hosting:

```bash
npm run build
firebase deploy --only hosting
```
