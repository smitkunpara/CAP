import './App.css'
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import Home from "./components/home.jsx";
import Analysis from "./components/analysis.jsx";
import Emails from "./components/emails.jsx";
import OAuthCallback from "./components/OAuthCallback.jsx";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  const router = createBrowserRouter([
    { path: '/', element: <Home /> },
    { path: '/emails', element: <Emails /> },
    { path: "/email/:emailId", element: <Analysis /> },
    { path: "/oauth/callback", element: <OAuthCallback /> },
  ]);
  return (
    <>
      <RouterProvider router={router} />
      <ToastContainer />
    </>
  )
}

export default App
