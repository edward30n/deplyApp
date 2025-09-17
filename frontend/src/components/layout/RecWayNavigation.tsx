/**
 * RECWAY NAVIGATION BAR
 * Basado en SmartEpiNavigation - Adaptado para RecWay
 */

"use client" // Si usas Next.js 13+

import React, { useState } from "react"
import { ChevronDown, Menu, X } from "lucide-react"

// ===== INTERFACES =====
interface NavigationItem {
  name: string
  href: string
  hasDropdown?: boolean
  dropdownItems?: { name: string; href: string }[]
  badge?: string
}

interface RecWayNavProps {
  logoText?: string
  homeUrl?: string
  accountUrl?: string
  className?: string
  items?: NavigationItem[]
  onAccountClick?: () => void
}

// ===== CONFIGURACIÓN POR DEFECTO =====
const defaultItems: NavigationItem[] = [
  {
    name: "Dashboard",
    href: "/"
  },
  {
    name: "Sensores",
    href: "/sensores",
    hasDropdown: true,
    dropdownItems: [
      { name: "Todos los Sensores", href: "/sensores" },
      { name: "Sensores Activos", href: "/sensores/activos" },
      { name: "Configuración", href: "/sensores/config" },
      { name: "Mantenimiento", href: "/sensores/mantenimiento" }
    ]
  },
  {
    name: "Segmentos",
    href: "/segmentos"
  },
  {
    name: "Muestras",
    href: "/muestras"
  },
  {
    name: "Análisis",
    href: "/analisis",
    hasDropdown: true,
    dropdownItems: [
      { name: "Reportes", href: "/analisis/reportes" },
      { name: "Tendencias", href: "/analisis/tendencias" },
      { name: "Alertas", href: "/analisis/alertas" }
    ]
  },
  {
    name: "Configuración",
    href: "/configuracion"
  }
]

// ===== COMPONENTE PRINCIPAL =====
const RecWayNavigation: React.FC<RecWayNavProps> = ({
  logoText = "RecWay",
  homeUrl = "/",
  accountUrl = "/login",
  className = "",
  items = defaultItems,
  onAccountClick
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [openDropdown, setOpenDropdown] = useState<string | null>(null)

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  const handleAccountClick = () => {
    if (onAccountClick) {
      onAccountClick()
    } else {
      window.location.href = accountUrl
    }
  }

  const handleDropdownToggle = (itemName: string) => {
    setOpenDropdown(openDropdown === itemName ? null : itemName)
  }

  return (
    <>
      {/* ===== HEADER PRINCIPAL ===== */}
      <header className={`recway-nav-header ${className}`}>
        <div className="recway-nav-container">
          
          {/* ===== LOGO ===== */}
          <div className="recway-nav-logo">
            <a href={homeUrl} className="recway-nav-logo-link">
              <div className="recway-nav-logo-icon">
                <span className="recway-nav-logo-letter">R</span>
              </div>
              <div className="recway-nav-logo-text-container">
                <span className="recway-nav-logo-text">{logoText}</span>
                <span className="recway-nav-logo-subtitle">Monitoreo Ambiental</span>
              </div>
            </a>
          </div>
          
          {/* ===== NAVEGACIÓN DESKTOP ===== */}
          <nav className="recway-nav-desktop">
            {items.map((item) => (
              <div key={item.name} className="recway-nav-item">
                {item.hasDropdown ? (
                  <div className="recway-nav-dropdown">
                    <button
                      className="recway-nav-dropdown-trigger"
                      onClick={() => handleDropdownToggle(item.name)}
                    >
                      {item.name} <ChevronDown className="recway-nav-icon" />
                    </button>
                    {openDropdown === item.name && (
                      <div className="recway-nav-dropdown-content">
                        {item.dropdownItems?.map((dropdownItem) => (
                          <a
                            key={dropdownItem.name}
                            href={dropdownItem.href}
                            className="recway-nav-dropdown-item"
                            onClick={() => setOpenDropdown(null)}
                          >
                            {dropdownItem.name}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <a
                    href={item.href}
                    className="recway-nav-link"
                  >
                    <span>{item.name}</span>
                    {item.badge && (
                      <span className="recway-nav-badge">
                        {item.badge}
                      </span>
                    )}
                  </a>
                )}
                <div className="recway-nav-underline"></div>
              </div>
            ))}
          </nav>
          
          {/* ===== BOTONES DERECHA ===== */}
          <div className="recway-nav-actions">
            <div className="recway-nav-account-desktop">
              <button
                className="recway-nav-account-btn"
                onClick={handleAccountClick}
              >
                Mi Cuenta
              </button>
            </div>
            <button 
              className="recway-nav-mobile-toggle"
              onClick={toggleMobileMenu}
            >
              {isMobileMenuOpen ? 
                <X className="recway-nav-icon" /> : 
                <Menu className="recway-nav-icon" />
              }
            </button>
          </div>
        </div>
      </header>

      {/* ===== MENÚ MÓVIL ===== */}
      {isMobileMenuOpen && (
        <div className="recway-nav-mobile-overlay">
          <div className="recway-nav-mobile-content">
            {items.map((item) => (
              <div key={item.name}>
                {item.hasDropdown ? (
                  <div>
                    <button
                      className="recway-nav-mobile-dropdown-trigger"
                      onClick={() => handleDropdownToggle(item.name)}
                    >
                      {item.name} <ChevronDown className="recway-nav-icon" />
                    </button>
                    {openDropdown === item.name && (
                      <div className="recway-nav-mobile-dropdown">
                        {item.dropdownItems?.map((dropdownItem) => (
                          <a
                            key={dropdownItem.name}
                            href={dropdownItem.href}
                            className="recway-nav-mobile-dropdown-item"
                            onClick={() => {
                              setIsMobileMenuOpen(false)
                              setOpenDropdown(null)
                            }}
                          >
                            {dropdownItem.name}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <a
                    href={item.href}
                    className="recway-nav-mobile-link"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <span>{item.name}</span>
                    {item.badge && (
                      <span className="recway-nav-badge">
                        {item.badge}
                      </span>
                    )}
                  </a>
                )}
              </div>
            ))}
            <div className="recway-nav-mobile-account">
              <button
                className="recway-nav-account-btn recway-nav-account-mobile"
                onClick={() => {
                  setIsMobileMenuOpen(false)
                  handleAccountClick()
                }}
              >
                Mi Cuenta
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default RecWayNavigation
