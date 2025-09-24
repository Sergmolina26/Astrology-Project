import React, { useEffect, useRef, useState } from 'react';
import { Loader } from '@googlemaps/js-api-loader';
import { Input } from './ui/input';
import { MapPin } from 'lucide-react';

const PlacesAutocomplete = ({ 
  value, 
  onChange, 
  onPlaceSelect, 
  placeholder = "Enter birth place",
  className = "",
  ...props 
}) => {
  const inputRef = useRef(null);
  const autocompleteRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const initializeAutocomplete = async () => {
      try {
        // Using a demo API key - in production, you'd want to use environment variables
        const loader = new Loader({
          apiKey: "AIzaSyBFw0Qbyq9zTuTlWnbs2B0l3mGDVYvfOWU", // Demo key - replace with your own
          version: "weekly",
          libraries: ["places"]
        });

        const google = await loader.load();
        
        if (inputRef.current && !autocompleteRef.current) {
          autocompleteRef.current = new google.maps.places.Autocomplete(
            inputRef.current,
            {
              types: ['(cities)'],
              fields: ['geometry', 'formatted_address', 'address_components']
            }
          );

          autocompleteRef.current.addListener('place_changed', () => {
            const place = autocompleteRef.current.getPlace();
            
            if (place.geometry && place.geometry.location) {
              const lat = place.geometry.location.lat();
              const lng = place.geometry.location.lng();
              const address = place.formatted_address;
              
              if (onPlaceSelect) {
                onPlaceSelect({
                  address,
                  latitude: lat,
                  longitude: lng
                });
              }
            }
          });
        }
        setIsLoaded(true);
      } catch (error) {
        console.warn('Google Maps not available, falling back to regular input:', error);
        setIsLoaded(false);
      }
    };

    initializeAutocomplete();
  }, [onPlaceSelect]);

  return (
    <div className="relative">
      <Input
        ref={inputRef}
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`${className} ${isLoaded ? 'pl-10' : ''}`}
        {...props}
      />
      {isLoaded && (
        <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
      )}
    </div>
  );
};

export default PlacesAutocomplete;