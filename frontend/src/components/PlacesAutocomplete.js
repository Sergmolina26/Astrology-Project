import React, { useEffect, useRef, useState } from 'react';
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
  
  // For now, let's use a regular input with manual coordinate entry
  // Google Places can be added later with proper API key setup
  
  return (
    <div className="relative">
      <Input
        ref={inputRef}
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`${className} pl-10`}
        {...props}
      />
      <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
    </div>
  );
};

export default PlacesAutocomplete;