/**
 * RECWAY HOME PAGE COMPONENT
 * Página de inicio completa auto-contenida para RecWay
 * Adaptada desde SmartEpi para monitoreo ambiental
 * 
 * FEATURES:
 * - Hero section con video y animaciones
 * - Sección de características/features
 * - Video promocional
 * - Proceso "How it Works"
 * - Perfiles del equipo
 * - Planes de precios
 * - Call to Action
 * - Sección de contacto
 * - Footer completo
 * - Responsive design
 * - Animaciones AOS
 * - TypeScript interfaces
 */

"use client"

import React, { useState, useEffect, useRef } from 'react';
import { useInView } from 'react-intersection-observer';

import { Database, BarChart2, Activity, Mail, Phone, MapPin, Check, Wifi,  Eye, TrendingUp } from 'lucide-react';
import colors from '../styles/colors';

// ===== INTERFACES =====
interface Feature {
  title: string
  description: string
  icon: React.ReactNode
  delay: number
}

interface HowItWorksItem {
  title: string
  description: string
  image: string
  animationDelay: number
  filterClass: string
}

interface TeamMember {
  name: string
  role: string
  description: string[]
  image: string
  linkedin: string
}

interface PricingPlan {
  name: string
  price: string
  description: string
  features: string[]
  cta: string
  popular: boolean
  delay: number
}

interface HowItWorksCardProps {
  title: string
  description: string
  image: string
  hoverImage: string
  filterClass?: string
}

interface VideoSectionProps {
  className?: string
}

interface RecWayHomePageProps {
  // Props de personalización
  logoSrc?: string
  companyName?: string
  heroTitle?: string
  heroSubtitle?: string
  contactEmail?: string
  contactPhone?: string
  contactAddress?: string
  mapSrc?: string
  onGetStarted?: () => void
  onContactSales?: () => void
  onLearnMore?: () => void
  // Props de contenido
  features?: Feature[]
  teamMembers?: TeamMember[]
  pricingPlans?: PricingPlan[]
  howItWorksItems?: HowItWorksItem[]
}

// ===== COMPONENTES INTERNOS =====
const HowItWorksCard: React.FC<HowItWorksCardProps> = ({ 
  title, 
  description
}) => {
  const [isHovered, setIsHovered] = useState(false)

  const renderIcon = (title: string) => {
    switch (title) {
      case "Recolección de Datos":
        return <Database className={`w-12 h-12 transition-colors duration-300 ${isHovered ? 'text-white' : 'text-green-500'}`} />
      case "Análisis y Modelado":
        return <BarChart2 className={`w-12 h-12 transition-colors duration-300 ${isHovered ? 'text-white' : 'text-green-500'}`} />
      case "Monitoreo y Alertas":
        return <Activity className={`w-12 h-12 transition-colors duration-300 ${isHovered ? 'text-white' : 'text-green-500'}`} />
      default:
        return <Database className={`w-12 h-12 transition-colors duration-300 ${isHovered ? 'text-white' : 'text-green-500'}`} />
    }
  }

  return (
    <div
      className="recway-how-it-works-card"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="recway-card-background"></div>
      
      <div 
        className="recway-card-image"
        style={{
          transform: isHovered ? 'translateX(0)' : 'translateX(-100%)'
        }}
      >
        <img
          src="/placeholder-env.svg"
          alt={title}
          className="recway-card-img"
        />
        <div className="recway-card-overlay"></div>
      </div>
      
      <div className="recway-card-content">
        <div className="recway-card-icon">
          {renderIcon(title)}
        </div>
        
        <h3 className={`recway-card-title ${isHovered ? 'text-white' : 'text-gray-800'}`}>
          {title}
        </h3>
        <p className={`recway-card-description ${isHovered ? 'text-gray-200' : 'text-gray-600'}`}>
          {description}
        </p>
      </div>
    </div>
  )
}

const VideoSection: React.FC<VideoSectionProps> = ({ className = "" }) => {
  const videoRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleScroll = () => {
      if (!videoRef.current) return

      const rect = videoRef.current.getBoundingClientRect()
      const isVisible = rect.top < window.innerHeight && rect.bottom >= 0

      if (isVisible) {
        const scrollPercentage = Math.min(1, Math.max(0, 1 - rect.top / window.innerHeight))

        if (videoRef.current) {
          videoRef.current.style.transform = `translateY(${scrollPercentage * 50}px)`
          videoRef.current.style.opacity = `${Math.min(1, scrollPercentage * 2)}`
        }
      }
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <section className={`recway-video-section ${className}`} data-aos="fade-up">
      <div className="recway-video-background">
        <div className="recway-video-container" ref={videoRef}>
          <video 
            className="recway-video-element"
            autoPlay 
            muted 
            loop 
            playsInline
          >
            <source
              src="https://assets.mixkit.co/videos/preview/mixkit-environmental-monitoring-stations-in-nature-44565-large.mp4"
              type="video/mp4"
            />
            Your browser does not support the video tag.
          </video>
        </div>
      </div>

      <div className="recway-video-content">
        <div className="recway-video-text" data-aos="fade-up">
          <h2 className="recway-video-title" style={{ color: '#fff' }}>Tecnología Avanzada para Monitoreo Ambiental</h2>
          <p className="recway-video-subtitle" style={{ color: '#fff' }}>
            Nuestra plataforma combina sensores IoT de última generación con inteligencia artificial
            para hacer el monitoreo ambiental más eficiente y preciso.
          </p>
          <button className="recway-btn-primary">Ver Demo Completa</button>
        </div>
      </div>
    </section>
  )
}

// ===== COMPONENTE PRINCIPAL =====
const RecWayHomePage: React.FC<RecWayHomePageProps> = ({
  companyName = "RecWay",
  heroTitle = "La revolución del diagnóstico vial: RecWay",
  heroSubtitle = "¿Por qué nuestras vías están en tan mal estado? El diagnóstico tradicional es costoso, lento y poco eficiente. RecWay transforma los datos de los sensores de los celulares de miles de usuarios en información útil y georreferenciada sobre el estado real de la malla vial. Analizamos las señales de acelerómetros y giroscopios de los teléfonos, compensamos el efecto de la velocidad y generamos un índice propio (RQI) que mide el confort del usuario y la calidad de la vía en tiempo real. Así, cualquier persona, entidad o empresa puede acceder a diagnósticos actualizados, precisos y económicos para tomar mejores decisiones sobre el mantenimiento y uso de las vías.",
  contactEmail = "contacto@recway.com",
  contactPhone = "+57 (300) 123-4567",
  contactAddress = "Calle 123, Bogotá, Colombia",
  mapSrc = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3976.2616307132143!2d-74.0817318!3d4.6533268!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8e3f9a3b7f5c8b9d%3A0x8a3b7f5c8b9d3e2f!2sBogot%C3%A1%2C%20Colombia!5e0!3m2!1sen!2sus!4v1677838423075!5m2!1sen!2sus",
  onGetStarted = () => console.log("Get Started clicked"),
  onContactSales = () => console.log("Contact Sales clicked"),
  onLearnMore = () => console.log("Learn More clicked"),
  features,
  teamMembers,
  pricingPlans,
  howItWorksItems
}) => {
  const [aosInitialized, setAosInitialized] = useState(false)
  const { ref: logoRef, inView: logoInView } = useInView({
    triggerOnce: false,
    threshold: 0.1,
  })

  const [animationKey, setAnimationKey] = useState(0)

  useEffect(() => {
    if (logoInView) {
      setAnimationKey((prev) => prev + 1)
    }
  }, [logoInView])

  useEffect(() => {
    const initAOS = () => {
      if (typeof window !== "undefined" && typeof (window as any).AOS !== "undefined") {
        (window as any).AOS.init({
          duration: 800,
          once: false,
          mirror: true,
          offset: 100,
        })
        setAosInitialized(true)
      }
    }

    initAOS()
    if (!aosInitialized) {
      const timer = setTimeout(initAOS, 1000)
      return () => clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    if (aosInitialized && typeof window !== "undefined" && typeof (window as any).AOS !== "undefined") {
      (window as any).AOS.refresh()
    }
  }, [aosInitialized])

  // Datos por defecto para RecWay
  const defaultFeatures: Feature[] = [
    {
      title: "Diagnóstico vial colaborativo",
      description: "Miles de celulares con acelerómetros y giroscopios generan datos sobre el estado real de las vías cada vez que circulan por ellas. RecWay convierte esa información en mapas y reportes útiles para todos.",
      icon: <Wifi className="w-8 h-8" style={{ color: colors.primary }} />,
      delay: 100,
    },
    {
      title: "Índice de calidad de vía (RQI)",
      description: "Nuestro algoritmo propio analiza las señales de los sensores, compensa la velocidad y genera un índice que mide el confort del usuario y la calidad de la vía en tiempo real.",
      icon: <TrendingUp className="w-8 h-8" style={{ color: colors.primary }} />,
      delay: 200,
    },
    {
      title: "Ahorro y eficiencia para entidades",
      description: "Las entidades de mantenimiento vial y empresas de transporte pueden acceder a diagnósticos actualizados, precisos y económicos, optimizando recursos y priorizando intervenciones.",
      icon: <BarChart2 className="w-8 h-8" style={{ color: colors.primary }} />,
      delay: 300,
    },
    {
      title: "Información para todos",
      description: "Usuarios, aseguradoras, constructoras y cualquier persona pueden consultar el estado de las vías en tiempo real a través de mapas y aplicaciones de movilidad.",
      icon: <Eye className="w-8 h-8" style={{ color: colors.primary }} />,
      delay: 400,
    },
    {
      title: "Escalable y adaptable",
      description: "Funciona en cualquier tipo de vía y vehículo, desde patinetas hasta camiones. El sistema se adapta a diferentes regiones y necesidades.",
      icon: <Activity className="w-8 h-8" style={{ color: colors.secondary }} />,
      delay: 500,
    },
    {
      title: "Enfoque en el usuario",
      description: "No solo medimos el pavimento, sino el confort real del usuario. Democratizamos el diagnóstico vial y abrimos la puerta a una gestión de infraestructura más inteligente y participativa.",
      icon: <Check className="w-8 h-8" style={{ color: colors.secondary }} />,
      delay: 600,
    },
  ]

  const defaultHowItWorksItems: HowItWorksItem[] = [
    {
      title: "1. Captura colaborativa",
      description: "Cada vez que un vehículo circula con nuestra app, los sensores del celular registran vibraciones y movimientos de la vía.",
      image: "/assets/how_it_works_1.jpg",
      animationDelay: 100,
      filterClass: "",
    },
    {
      title: "2. Procesamiento inteligente",
      description: "La información se envía al servidor, donde se analiza, se compensa el efecto de la velocidad y se calcula el RQI (Road Quality Index).",
      image: "/assets/how_it_works_2.jpg",
      animationDelay: 300,
      filterClass: "",
    },
    {
      title: "3. Visualización y acción",
      description: "Los resultados se muestran en mapas y reportes. Entidades, empresas y usuarios pueden consultar el estado de las vías y tomar mejores decisiones.",
      image: "/assets/how_it_works_3.jpg",
      animationDelay: 500,
      filterClass: "",
    },
  ]

  const defaultTeamMembers: TeamMember[] = [
    {
      name: "Edward Nicolas Duarte Valencia",
      role: "Fundador & CEO",
      description: [
        "Ingeniero electrónico de la Pontificia Universidad Javeriana de Colombia, apasionado por la programación y especializado en IoT, automatización, robótica y procesamiento de señales. Edward es conocido por su adaptabilidad a las tendencias emergentes en TIC.",
        "Es una persona determinada con espíritu emprendedor y enfoque en sostenibilidad. Edward se compromete a liderar y colaborar en equipos, impulsando impactos positivos cuantitativos a través de soluciones tecnológicas innovadoras para el monitoreo ambiental."
      ],
      image: "/assets/founder_profile_image.png",
      linkedin: "https://www.linkedin.com/in/edward-nicolas-duarte-valencia-913653243/"
    },
    {
      name: "Nicolas Duarte",
      role: "Co-Fundador & CTO",
      description: [
        "Experto en desarrollo de software y arquitectura de sistemas, con amplia experiencia en el diseño de plataformas de monitoreo ambiental. Nicolas se especializa en la integración de sistemas IoT y desarrollo de interfaces de usuario intuitivas.",
        "Su visión técnica y enfoque en la experiencia del usuario han sido fundamentales para crear soluciones que no solo son potentes, sino también accesibles para investigadores y organizaciones ambientales de todos los niveles."
      ],
      image: "/assets/co-founder_profile_image.png",
      linkedin: "https://www.linkedin.com/in/nicolas-duarte/"
    }
  ]

  const defaultPricingPlans: PricingPlan[] = [
    {
      name: "Básico",
      price: "299",
      description: "Perfecto para proyectos pequeños de investigación",
      features: ["Hasta 5 sensores", "Dashboard básico", "Alertas por email", "Soporte por email", "Almacenamiento 1 año"],
      cta: "Comenzar",
      popular: false,
      delay: 100,
    },
    {
      name: "Profesional",
      price: "899",
      description: "Ideal para organizaciones e instituciones",
      features: [
        "Hasta 50 sensores",
        "Analytics avanzados",
        "Alertas en tiempo real",
        "API personalizada",
        "Soporte prioritario",
        "Almacenamiento ilimitado",
      ],
      cta: "Comenzar",
      popular: true,
      delay: 300,
    },
    {
      name: "Enterprise",
      price: "Personalizado",
      description: "Para grandes organizaciones con necesidades complejas",
      features: [
        "Sensores ilimitados",
        "IA personalizada",
        "Soporte 24/7 dedicado",
        "Integraciones custom",
        "Instalación on-premise",
        "SLA garantizado",
      ],
      cta: "Contactar Ventas",
      popular: false,
      delay: 500,
    },
  ]

  const featuresData = features || defaultFeatures
  const howItWorksData = howItWorksItems || defaultHowItWorksItems
  const teamData = teamMembers || defaultTeamMembers
  const pricingData = pricingPlans || defaultPricingPlans

  return (
    <div className="recway-home-page">
      <main className="recway-main">
        {/* Hero Section */}
        <section className="recway-hero-section">
          <div className="recway-hero-container">
            <div className="recway-hero-content">
              <div className="recway-hero-text" data-aos="fade-right" data-aos-delay="100">
                <div className="recway-hero-logo" ref={logoRef}>
                  <div className={`recway-logo-animation`} key={animationKey}>
                    <div className="flex h-20 w-20 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-green-500 mb-4">

                    </div>
                  </div>
                </div>
                
                <h1 className="recway-hero-title" style={{ color: colors.textLight }}>{heroTitle}</h1>
                <p className="recway-hero-subtitle" style={{ color: colors.textLight, maxWidth: 700, margin: '0 auto', fontSize: '1.25rem', lineHeight: 1.6 }}>
                  {heroSubtitle}
                </p>
                
                <div className="recway-hero-buttons">
                  <button 
                    onClick={onGetStarted} 
                    className="recway-btn-primary"
                    style={{ border: '2px solid #ffffff', color: '#ffffff' }}
                  >
                    Comenzar Ahora
                  </button>
                  <button 
                    onClick={onContactSales} 
                    className="recway-btn-secondary"
                    style={{ border: '2px solid #ffffff', color: '#ffffff' }}
                  >
                    Contactar Ventas
                  </button>
                </div>
              </div>
              
              <div className="recway-hero-video" data-aos="fade-left" data-aos-delay="300">
                <div className="recway-hero-video-container">
                    <video className="recway-hero-video-element" autoPlay muted loop playsInline>
                    <source
                      src="/assets/video1.mp4"
                      type="video/mp4"
                    />
                    Your browser does not support the video tag.
                    </video>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="recway-features-section">
          <div className="recway-section-container">
            <h2 className="recway-section-title" data-aos="fade-up">
              ¿Cómo RecWay revoluciona el diagnóstico vial?
            </h2>
            <div className="recway-features-grid">
              {featuresData.map((feature, index) => (
                <div
                  key={index}
                  className="recway-feature-card"
                  data-aos="fade-up"
                  data-aos-delay={feature.delay}
                >
                  <div className="recway-feature-icon">
                    {feature.icon}
                  </div>
                  <h3 className="recway-feature-title">{feature.title}</h3>
                  <p className="recway-feature-description">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Video Section */}
        <VideoSection />

        {/* How It Works Section */}
        <section id="how-it-works" className="recway-how-it-works-section">
          <div className="recway-section-container">
            <h2 className="recway-section-title" data-aos="fade-up">
              Cómo Funciona
            </h2>
            <div className="recway-how-it-works-grid">
              {howItWorksData.map((item, index) => (
                <HowItWorksCard
                  key={index}
                  title={item.title}
                  description={item.description}
                  image={item.image}
                  hoverImage={item.image}
                  filterClass={item.filterClass}
                />
              ))}
            </div>
            
            {/* Workflow Summary */}
            <div className="recway-workflow-summary" data-aos="fade-up">
              <h3 className="recway-workflow-title">Flujo de Trabajo Completo</h3>
              <div className="recway-workflow-image">
                <img 
                  src="/assets/recway_workflow.jpg"
                  alt={`${companyName} Diagrama de Flujo`}
                  className="recway-workflow-img"
                />
              </div>
              <div className="recway-workflow-content">
                <p className="recway-workflow-description">
                  Desde la recolección de datos hasta la toma de decisiones informadas, 
                  nuestro flujo de trabajo integrado garantiza resultados precisos y oportunos.
                </p>
            <button onClick={onLearnMore} className="recway-btn-primary">
              Conocer Más
            </button>
              </div>
            </div>
          </div>
        </section>

        {/* Team Section */}
        <section id="team" className="recway-team-section">
          <div className="recway-section-container">
            <h2 className="recway-section-title" data-aos="fade-up">
              Conoce Nuestro Equipo
            </h2>
            <div className="recway-team-grid">
              {teamData.map((member, index) => (
                <div
                  key={index}
                  className="recway-team-card"
                  data-aos="fade-up"
                  data-aos-delay={100 + index * 200}
                >
                  <div className="recway-team-header">
                    <div className="recway-team-avatar">
                      <img
                        src={member.image}
                        alt={member.name}
                        className="recway-team-img"
                      />
                    </div>
                    <h3 className="recway-team-name">{member.name}</h3>
                    <p className="recway-team-role">{member.role}</p>
                  </div>
                  
                  <div className="recway-team-description">
                    {member.description.map((paragraph, pIndex) => (
                      <p key={pIndex} className="mb-3">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                  
                  <div className="recway-team-footer">
                    <div className="recway-team-email">
                      <Mail className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="text-sm text-gray-600">{contactEmail}</span>
                    </div>
                    <a
                      href={member.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="recway-linkedin-btn"
                    >
                      LinkedIn
                    </a>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="recway-team-cta" data-aos="fade-up">
              <p className="recway-team-cta-text">
                ¿Quieres unirte a nuestro equipo y ayudar a construir el futuro del monitoreo ambiental?
              </p>
              <button onClick={onContactSales} className="recway-btn-primary">
                Ver Oportunidades
              </button>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="recway-pricing-section">
          <div className="recway-section-container">
            <h2 className="recway-section-title" data-aos="fade-up">
              Planes de Precios
            </h2>
            <div className="recway-pricing-grid">
              {pricingData.map((plan, index) => (
                <div
                  key={index}
                  className={`recway-pricing-card ${plan.popular ? 'recway-pricing-popular' : ''}`}
                  data-aos="fade-up"
                  data-aos-delay={plan.delay}
                >
                  <div className={`recway-pricing-header ${plan.popular ? 'recway-pricing-header-popular' : ''}`}>
                    <h3 className="recway-pricing-name">{plan.name}</h3>
                    <div className="recway-pricing-price">
                      ${plan.price}
                      {plan.price !== "Personalizado" && <span className="recway-pricing-period">/mes</span>}
                    </div>
                    <p className="recway-pricing-description">{plan.description}</p>
                  </div>
                  
                  <div className="recway-pricing-content">
                    <ul className="recway-pricing-features">
                      {plan.features.map((feature, fIndex) => (
                        <li key={fIndex} className="recway-pricing-feature">
                          <Check className="recway-pricing-check" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    
                    <button
                      onClick={plan.cta === "Contactar Ventas" ? onContactSales : onGetStarted}
                      className={`recway-pricing-button ${plan.popular ? 'recway-pricing-button-popular' : ''}`}
                    >
                      {plan.cta}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section id="cta" className="recway-cta-section">
          <div className="recway-section-container recway-cta-container" data-aos="zoom-in">
            <div className="recway-cta-logo">
              <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-white/20 backdrop-blur">
              </div>
            </div>
            <h2 className="recway-cta-title">¿Listo para Transformar tu Monitoreo Ambiental?</h2>
            <p className="recway-cta-subtitle">
              Únete a las organizaciones que ya están usando RecWay para mejorar sus estudios ambientales.
            </p>
            <div className="recway-cta-buttons">
              <button onClick={onGetStarted} className="recway-btn-white">
                Comenzar Gratis
              </button>
              <button onClick={onContactSales} className="recway-btn-outline-white">
                Hablar con Ventas
              </button>
            </div>
          </div>
        </section>

        {/* Contact Section */}
        <section id="contact" className="recway-contact-section">
          <div className="recway-section-container">
            <div className="recway-contact-grid">
              <div data-aos="fade-right">
                <h2 className="recway-contact-title">Contáctanos</h2>
                <p className="recway-contact-subtitle">
                  ¿Tienes preguntas sobre RecWay? Nuestro equipo está aquí para ayudarte.
                </p>
                
                <div className="recway-contact-details">
                  <div className="recway-contact-item">
                    <div className="recway-contact-icon">
                      <Mail className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="recway-contact-label">Email</div>
                      <div className="recway-contact-value">{contactEmail}</div>
                    </div>
                  </div>
                  
                  <div className="recway-contact-item">
                    <div className="recway-contact-icon">
                      <Phone className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="recway-contact-label">Teléfono</div>
                      <div className="recway-contact-value">{contactPhone}</div>
                    </div>
                  </div>
                  
                  <div className="recway-contact-item">
                    <div className="recway-contact-icon">
                      <MapPin className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="recway-contact-label">Dirección</div>
                      <div className="recway-contact-value">{contactAddress}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div data-aos="fade-left">
                <div className="recway-map-container">
                  <iframe
                    src={mapSrc}
                    width="100%"
                    height="300"
                    style={{ border: 0 }}
                    allowFullScreen
                    loading="lazy"
                    referrerPolicy="no-referrer-when-downgrade"
                    title="Ubicación de RecWay"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="recway-footer">
        <div className="recway-footer-container">
          <div className="recway-footer-content">
            <div className="recway-footer-logo">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-green-500 mr-3">

              </div>
            </div>
            <div className="recway-footer-text">
              <p className="recway-footer-copyright">
                © 2024 RecWay. Todos los derechos reservados.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default RecWayHomePage
