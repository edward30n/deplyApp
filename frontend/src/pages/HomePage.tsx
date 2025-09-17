import React, { useEffect, useState } from 'react';
import RecWayHomePage from '../components/RecWayHomePage';
import RecWayNavigation from '../components/layout/RecWayNavigation';
import '../components/RecWayHomePage.css';
import '../components/layout/RecWayNavigation.css';
import AOS from 'aos';
import 'aos/dist/aos.css';

const HomePage: React.FC = () => {
  const [isOnHero, setIsOnHero] = useState(true);

  useEffect(() => {
    AOS.init({
      duration: 800,
      once: false,
      mirror: true,
      offset: 100,
    });

    // Función para detectar si estamos sobre el hero
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const heroHeight = 70; // Altura aproximada del hero
      setIsOnHero(scrollY < heroHeight);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleGetStarted = () => {
    // Navegar al dashboard
    window.location.href = '/';
  };

  const handleContactSales = () => {
    // Scroll a la sección de contacto
    const contactSection = document.getElementById('contact');
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLearnMore = () => {
    // Scroll a la sección how it works
    const howItWorksSection = document.getElementById('how-it-works');
    if (howItWorksSection) {
      howItWorksSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Fondo negro con opacidad cuando estamos sobre el hero */}
      {isOnHero && (
        <div 
          className="fixed top-0 left-0 right-0 h-16 bg-black z-40"
          style={{ 
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            height: '64px',
            backgroundColor: '#000000',
            zIndex: 40,
            opacity: 0.75, // Reducir opacidad
            transition: 'opacity 0.3s ease'
          }}
        ></div>
      )}
      
      {/* Navbar con efecto glassmorphism */}
      <RecWayNavigation 
        logoText="RecWay"
        homeUrl="/home"
        accountUrl="/login"
        onAccountClick={() => window.location.href = '/login'}
      />
      
      {/* Homepage Content */}
      <RecWayHomePage 
        companyName="RecWay"
        heroTitle="Transformando Datos Ambientales en Información Accionable"
        heroSubtitle="RecWay es una plataforma avanzada de monitoreo ambiental que convierte datos complejos de sensores en resultados significativos en tiempo real. Nuestra tecnología permite análisis instantáneo, resultados transparentes y manejo seguro de datos para investigadores y organizaciones ambientales."
        contactEmail="contacto@recway.com"
        contactPhone="+57 (300) 123-4567"
        contactAddress="Calle 123, Bogotá, Colombia"
        onGetStarted={handleGetStarted}
        onContactSales={handleContactSales}
        onLearnMore={handleLearnMore}
      />
    </div>
  );
};

export default HomePage;
