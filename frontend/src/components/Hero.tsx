import { useState, useEffect, useCallback } from "react";
import HeroBackgroundImage from "../assets/hero-background.jpeg";

// ---------------- Icons ----------------
const AlertTriangle = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
    <path d="M12 9v4" />
    <path d="M12 17h.01" />
  </svg>
);

const Shield = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const Phone = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
  </svg>
);

const Loader = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="animate-spin"
    {...props}
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);

// ---------------- SOS Modal ----------------
const SOSModal = ({ isOpen, onClose }) => {
  const [sosState, setSosState] = useState({
    status: "idle",
    location: null,
    message: "",
  });

  const fetchLocation = useCallback(() => {
    setSosState({ status: "loading", location: null, message: "" });

    if (!navigator.geolocation) {
      setSosState({
        status: "error",
        location: null,
        message: "Geolocation is not supported by your browser.",
      });
      return;
    }

    if (window.isSecureContext === false) {
      setSosState({
        status: "error",
        location: null,
        message:
          "Location API is only available on secure connections (HTTPS) or localhost.",
      });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setSosState({ status: "success", location: position.coords, message: "" });
      },
      (error) => {
        let message = "An unknown error occurred.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message =
              "Location access was denied. Please allow location access in your browser settings and try again.";
            break;
          case error.POSITION_UNAVAILABLE:
            message =
              "Location information is unavailable. Check your device’s GPS or internet connection.";
            break;
          case error.TIMEOUT:
            message = "The request to get your location timed out. Please retry.";
            break;
        }
        setSosState({ status: "error", location: null, message });
      }
    );
  }, []);

  useEffect(() => {
    if (isOpen) fetchLocation();
  }, [isOpen, fetchLocation]);

  if (!isOpen) return null;

  const renderContent = () => {
    switch (sosState.status) {
      case "loading":
        return (
          <div className="text-center py-6">
            <Loader className="mx-auto h-12 w-12 text-blue-600" />
            <h3 className="mt-4 text-lg font-medium text-gray-800">
              Finding your location...
            </h3>
            <p className="text-sm text-gray-500">
              Please approve the location request.
            </p>
          </div>
        );

      case "success":
        const { location } = sosState;
        const mapLink = `https://www.google.com/maps?q=${location.latitude},${location.longitude}`;
        const message = `Emergency! My current location is: ${mapLink}`;
        return (
          <div className="text-center py-4">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
              <svg
                className="h-8 w-8 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-green-700 mb-2">
              Location Found!
            </h3>
            <div className="bg-green-50 p-4 rounded-lg text-left text-sm text-gray-800 break-words mb-4">
              <p>
                <strong>Latitude:</strong> {location.latitude.toFixed(5)}
              </p>
              <p>
                <strong>Longitude:</strong> {location.longitude.toFixed(5)}
              </p>
              <a
                href={mapLink}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline inline-block mt-2 font-semibold"
              >
                View on Google Maps
              </a>
            </div>
            <div className="space-y-2">
              <a
                href={`sms:?body=${encodeURIComponent(message)}`}
                className="block w-full text-center bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 transition"
              >
                Share via SMS
              </a>
              <a
                href="tel:112"
                className="block w-full text-center bg-red-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-red-700 transition"
              >
                Call Emergency Services (112)
              </a>
              <button
                onClick={onClose}
                className="block w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        );

      case "error":
        return (
          <div className="text-center py-6">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
              <svg
                className="h-8 w-8 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-red-700 mb-2">
              Location Error
            </h3>
            <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">
              {sosState.message}
            </p>
            <div className="mt-4 flex gap-2">
              <button
                onClick={fetchLocation}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                Retry
              </button>
              <button
                onClick={onClose}
                className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        {renderContent()}
      </div>
    </div>
  );
};

// ---------------- Hero Section ----------------
const Hero = () => {
  const [isSOSOpen, setIsSOSOpen] = useState(false);

  return (
    <>
      <section
        className="min-h-screen flex items-center justify-center pt-20 relative bg-cover bg-center"
        style={{ backgroundImage: `url(${HeroBackgroundImage})` }}
      >
        <div
          className="absolute inset-0 bg-black bg-opacity-50 z-0"
          aria-hidden="true"
        ></div>

        <div className="container mx-auto px-4 py-20 relative z-10 grid md:grid-cols-2 gap-10 items-center">
          {/* Left: Emergency Support Card */}
          <div className="relative">
            <div className="w-full bg-gradient-to-br from-red-50 via-pink-50 to-orange-50 rounded-3xl shadow-2xl p-8 border border-red-100 relative z-10">
              <div className="space-y-6 text-center">
                <div className="w-16 h-16 bg-red-600 rounded-full mx-auto flex items-center justify-center shadow-lg">
                  <AlertTriangle className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-3xl font-bold text-gray-800">
                  Emergency Support
                </h3>
                <p className="text-gray-600 text-lg">
                  Immediate help when you need it most. Your safety is our
                  priority.
                </p>

                {/* Emergency Alert */}
                <div className="bg-white rounded-2xl p-6 shadow-lg border border-red-100">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-red-600 rounded-xl flex items-center justify-center">
                      <Phone className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 text-left">
                      <h4 className="text-xl font-bold text-gray-800">
                        Emergency Alert
                      </h4>
                      <p className="text-gray-600">
                        Instant SOS with location sharing
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsSOSOpen(true)}
                    className="w-full mt-4 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center"
                  >
                    <Phone className="w-4 h-4 mr-2" />
                    Activate SOS
                  </button>
                </div>

                {/* Report Violence */}
                <div className="bg-white rounded-2xl p-6 shadow-lg border border-red-100">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center">
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 text-left">
                      <h4 className="text-xl font-bold text-gray-800">
                        Report Violence
                      </h4>
                      <p className="text-gray-600">
                        Safe, anonymous reporting system
                      </p>
                    </div>
                  </div>
                  <a
                    href="/report"
                    className="w-full mt-4 border border-gray-300 text-gray-700 hover:bg-gray-100 font-medium py-2 px-4 rounded-lg flex items-center justify-center"
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Report Incident
                  </a>
                </div>

                <p className="text-sm text-gray-500">
                  🔒 All reports are confidential and secure
                </p>
              </div>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-red-400/10 via-pink-400/10 to-orange-400/10 rounded-3xl transform -rotate-1"></div>
          </div>

          {/* Right: Intro Section */}
          <div className="space-y-6 text-white">
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight">
              Your Complete{" "}
              <span className="bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 bg-clip-text text-transparent block">
                Women's Health
              </span>{" "}
              Companion
            </h1>
            <p className="text-xl text-gray-200 leading-relaxed max-w-xl">
              Track pregnancy, monitor periods, support mental wellness, and stay
              safe with our comprehensive health platform designed for women.
            </p>
            <a
              href="/auth"
              className="text-lg bg-gradient-to-r from-pink-500 to-purple-600 text-white font-semibold py-3 px-8 rounded-lg shadow-lg hover:shadow-xl transition-transform transform hover:scale-105 inline-block"
            >
              Start Your Journey
            </a>
          </div>
        </div>
      </section>

      <SOSModal isOpen={isSOSOpen} onClose={() => setIsSOSOpen(false)} />
    </>
  );
};

// ---------------- App Wrapper ----------------
export default function App() {
  return (
    <div className="font-sans">
      <Hero />
    </div>
  );
}
