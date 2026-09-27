import { Route, Routes } from "react-router-dom";
import { ChatWidget } from "./components/ChatWidget";
import { NavBar } from "./components/NavBar";
import { About } from "./pages/About";
import { Home } from "./pages/Home";
import { Login } from "./pages/Login";
import { ProductPage } from "./pages/ProductPage";
import { Products } from "./pages/Products";
import { Signup } from "./pages/Signup";

export default function App() {
  return (
    <div className="shell">
      <NavBar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductPage />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <footer className="foot">
        <p>Campus Customs &middot; 1 Broadway, New Haven &middot; help@campuscustoms.yale.edu</p>
        <p className="foot__fine">Student project for MGT 409. Prices and stock come from campus_customs.db.</p>
      </footer>
      <ChatWidget />
    </div>
  );
}
