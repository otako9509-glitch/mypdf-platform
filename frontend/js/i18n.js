class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('mypdf_lang') || 'ar';
        this.fallbackTranslations = {
            ar: {
                "app.name": "MyPDF",
                "nav.home": "الرئيسية",
                "nav.tools": "جميع الأدوات",
                "nav.security": "الأمان والتشفير",
                "nav.about": "حول المنصة",
                "tools.catalog.title": "كتالوج أدوات PDF الكامل",
                "tools.catalog.description": "تصفح كل الأدوات المتاحة لمعالجة ملفاتك باحترافية وسرعة.",
                "tools.merge.title": "دمج PDF",
                "tools.merge.description": "دمج ملفات PDF متعددة في مستند واحد متناسق.",
                "tools.split.title": "تقسيم PDF",
                "tools.split.description": "فصل صفحات محددة في ملف جديد ومستقل.",
                "tools.compress.title": "ضغط PDF",
                "tools.compress.description": "تقليل حجم الملف لأقصى حد مع الحفاظ على الجودة.",
                "tools.rotate.title": "تدوير PDF",
                "tools.rotate.description": "تدوير صفحات المستند بالزاوية التي تختارها.",
                "tools.organize.title": "تنظيم الصفحات",
                "tools.organize.description": "إعادة ترتيب، حذف، أو استخراج صفحات من ملفك.",
                "tools.pdf_to_jpg.title": "PDF إلى JPG",
                "tools.pdf_to_jpg.description": "تحويل صفحات المستند إلى صور عالية الدقة.",
                "tools.jpg_to_pdf.title": "JPG إلى PDF",
                "tools.jpg_to_pdf.description": "تحويل صور متعددة إلى مستند PDF واحد.",
                "tools.watermark.title": "علامة مائية",
                "tools.watermark.description": "إضافة نص أو ختم لحماية وتوثيق مستنداتك.",
                "tools.protect.title": "حماية وتشفير",
                "tools.protect.description": "تأمين المستند بكلمة مرور قوية لمنع الفتح.",
                "tools.unlock.title": "فك الحماية",
                "tools.unlock.description": "إزالة كلمات المرور والقيود من ملفاتك المعتمدة."
            },
            en: {
                "app.name": "MyPDF",
                "nav.home": "Home",
                "nav.tools": "All Tools",
                "nav.security": "Security",
                "nav.about": "About",
                "tools.catalog.title": "Complete PDF Tools Catalog",
                "tools.catalog.description": "Explore all tools available to process your PDF files professionally.",
                "tools.merge.title": "Merge PDF",
                "tools.merge.description": "Combine multiple PDFs into a single file.",
                "tools.split.title": "Split PDF",
                "tools.split.description": "Extract specific pages into a standalone PDF.",
                "tools.compress.title": "Compress PDF",
                "tools.compress.description": "Reduce file size while keeping top quality.",
                "tools.rotate.title": "Rotate PDF",
                "tools.rotate.description": "Rotate your document pages smoothly.",
                "tools.organize.title": "Organize PDF",
                "tools.organize.description": "Reorder, delete, or extract pages easily.",
                "tools.pdf_to_jpg.title": "PDF to JPG",
                "tools.pdf_to_jpg.description": "Convert PDF pages into high-res images.",
                "tools.jpg_to_pdf.title": "JPG to PDF",
                "tools.jpg_to_pdf.description": "Convert multiple image files into one clean PDF.",
                "tools.watermark.title": "Watermark PDF",
                "tools.watermark.description": "Add custom text stamps to protect documents.",
                "tools.protect.title": "Protect PDF",
                "tools.protect.description": "Encrypt your document with a secure password.",
                "tools.unlock.title": "Unlock PDF",
                "tools.unlock.description": "Remove passwords and restrictions safely."
            }
        };
        this.translations = {};
        this.init();
    }

    // كشف المسار النسبي الصحيح حسب مكان تواجد صفحة الـ HTML
    getBasePath() {
        return window.location.pathname.includes('/pages/') ? '../' : './';
    }

    async init() {
        await this.loadTranslations(this.currentLang);
        this.applyLanguage();
    }

    async loadTranslations(lang) {
        const basePath = this.getBasePath();
        try {
            const response = await fetch(`${basePath}locales/${lang}.json`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            this.translations = await response.json();
        } catch (error) {
            // اعتماد القاموس المدمج عند فشل الـ fetch لتفادي إظهار المفاتيح
            this.translations = this.fallbackTranslations[lang] || this.fallbackTranslations['en'];
        }
    }

    async setLanguage(lang) {
        if (lang === this.currentLang) return;
        
        this.currentLang = lang;
        localStorage.setItem('mypdf_lang', lang);
        await this.loadTranslations(lang);
        this.applyLanguage();
    }

    applyLanguage() {
        document.documentElement.dir = this.currentLang === 'ar' ? 'rtl' : 'ltr';
        document.documentElement.lang = this.currentLang;

        const basePath = this.getBasePath();
        let rtlLink = document.getElementById('rtl-css');

        if (this.currentLang === 'ar') {
            if (!rtlLink) {
                rtlLink = document.createElement('link');
                rtlLink.id = 'rtl-css';
                rtlLink.rel = 'stylesheet';
                rtlLink.href = `${basePath}css/rtl.css`;
                document.head.appendChild(rtlLink);
            }
        } else if (rtlLink) {
            rtlLink.remove();
        }

        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.getTranslation(key);
            if (translation) {
                element.textContent = translation;
            }
        });

        const langToggle = document.getElementById('langToggle');
        if (langToggle) {
            langToggle.textContent = this.currentLang === 'ar' ? 'English' : 'العربية';
        }

        window.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { lang: this.currentLang } 
        }));
    }

    getTranslation(key) {
        const keys = key.split('.');
        let value = this.translations;
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                // محاولة البحث داخل القاموس الاحتياطي
                const fallback = this.fallbackTranslations[this.currentLang] || this.fallbackTranslations['en'];
                return fallback[key] || key;
            }
        }
        
        return value;
    }

    t(key) {
        return this.getTranslation(key);
    }
}

const i18n = new I18n();
window.i18n = i18n;