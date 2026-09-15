// رابط الـ Backend المباشر على Render
const API_BASE_URL = 'https://mypdf-api.onrender.com/api/v1';

const ApiService = {
  // فحص حالة الخادم
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      return await res.json();
    } catch (err) {
      console.warn('السيرفر قيد التشغيل أو جاري الإيقاظ...', err);
      return null;
    }
  },

  // رفع ملف أو عدة ملفات لمعالجتها
  async uploadFile(endpoint, formData) {
    try {
      const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'حدث خطأ أثناء معالجة الطلب');
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // تتبع حالة المهمة بالـ ID
  async getJobStatus(jobId) {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (!response.ok) throw new Error('تعذر جلب حالة المهمة');
    return await response.json();
  },

  // رابط التحميل النهائي
  getDownloadUrl(jobId) {
    return `${API_BASE_URL}/download/${jobId}`;
  }
};
