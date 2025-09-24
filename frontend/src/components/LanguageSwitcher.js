import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/button';
import { Globe } from 'lucide-react';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();

  const toggleLanguage = () => {
    const newLanguage = i18n.language === 'en' ? 'es' : 'en';
    i18n.changeLanguage(newLanguage);
    localStorage.setItem('language', newLanguage);
  };

  return (
    <Button
      onClick={toggleLanguage}
      variant="ghost"
      size="sm"
      className="text-slate-400 hover:text-amber-400 flex items-center space-x-2"
      data-testid="language-switcher"
    >
      <Globe className="w-4 h-4" />
      <span className="text-sm font-medium">
        {i18n.language === 'en' ? 'ES' : 'EN'}
      </span>
    </Button>
  );
};

export default LanguageSwitcher;