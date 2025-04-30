import './App.css'
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import Home from "./components/home.jsx";
import Analysis from "./components/analysis.jsx";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  const router = createBrowserRouter([
    { path: '/', element: <Home /> },
    { path: "/email/:emailId", element: <Analysis /> },
  ]);
  return (
    <>
      <RouterProvider router={router} />
      <ToastContainer />
    </>
  )
}

export default App
