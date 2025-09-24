import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/button';
import { Globe, ChevronDown } from 'lucide-react';

const LanguageSwitcher = ({ variant = "compact", showLabel = false }) => {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const languages = [
    { code: 'en', name: t('common.english'), flag: '🇺🇸' },
    { code: 'es', name: t('common.spanish'), flag: '🇪🇸' }
  ];

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  const changeLanguage = (langCode) => {
    i18n.changeLanguage(langCode);
    localStorage.setItem('language', langCode);
    setIsOpen(false);
  };

  if (variant === "prominent") {
    return (
      <div className="relative">
        <Button
          onClick={() => setIsOpen(!isOpen)}
          variant="outline"
          className="bg-slate-800/50 border-amber-400/30 hover:border-amber-400 text-white flex items-center space-x-2 px-4 py-2"
          data-testid="language-switcher-prominent"
        >
          <Globe className="w-4 h-4 text-amber-400" />
          <span className="text-sm font-medium">{currentLanguage.flag} {currentLanguage.name}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </Button>

        {isOpen && (
          <div className="absolute top-full mt-2 left-0 bg-slate-800 border border-amber-400/30 rounded-lg shadow-xl z-50 min-w-[180px]">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => changeLanguage(lang.code)}
                className={`w-full px-4 py-3 text-left hover:bg-amber-400/10 flex items-center space-x-3 first:rounded-t-lg last:rounded-b-lg transition-colors ${
                  i18n.language === lang.code ? 'bg-amber-400/20 text-amber-400' : 'text-white'
                }`}
              >
                <span className="text-lg">{lang.flag}</span>
                <span className="font-medium">{lang.name}</span>
                {i18n.language === lang.code && <span className="ml-auto text-amber-400">✓</span>}
              </button>
            ))}
          </div>
        )}

        {/* Overlay to close dropdown */}
        {isOpen && (
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
        )}
      </div>
    );
  }

  // Compact version (original)
  return (
    <Button
      onClick={() => changeLanguage(i18n.language === 'en' ? 'es' : 'en')}
      variant="ghost"
      size="sm"
      className="text-slate-400 hover:text-amber-400 flex items-center space-x-2"
      data-testid="language-switcher"
    >
      <Globe className="w-4 h-4" />
      {showLabel ? (
        <span className="text-sm font-medium">{currentLanguage.name}</span>
      ) : (
        <span className="text-sm font-medium">
          {i18n.language === 'en' ? 'ES' : 'EN'}
        </span>
      )}
    </Button>
  );
};

export default LanguageSwitcher;