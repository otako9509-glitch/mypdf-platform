// دالة شاملة لمعالجة أي عملية (دمج، ضغط، تحويل...)
async function handlePdfProcess({ endpoint, files, extraParams = {}, onProgress, onSuccess, onError }) {
  if (!files || files.length === 0) {
    if (onError) onError('يرجى اختيار ملف واحد على الأقل.');
    return;
  }

  const formData = new FormData();
  
  // إضافة الملفات إلى الـ FormData
  if (files instanceof FileList || Array.isArray(files)) {
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
  } else {
    formData.append('file', files);
  }

  // إضافة أي معاملات إضافية (مثل كلمة المرور أو خيارات التدوير)
  for (const [key, value] of Object.entries(extraParams)) {
    formData.append(key, value);
  }

  try {
    if (onProgress) onProgress('جاري رفع الملف إلى الخادم...');
    
    // إرسال الطلب إلى السيرفر
    const data = await ApiService.uploadFile(endpoint, formData);
    const jobId = data.job_id || data.id;

    if (!jobId) {
      throw new Error('لم يتم استلام رقم المهمة (Job ID) من الخادم.');
    }

    if (onProgress) onProgress('جاري معالجة الملف...');

    // متابعة حالة المهمة (Polling كل ثانيتين)
    const pollInterval = setInterval(async () => {
      try {
        const job = await ApiService.getJobStatus(jobId);

        if (job.status === 'completed' || job.status === 'done') {
          clearInterval(pollInterval);
          const downloadUrl = ApiService.getDownloadUrl(jobId);
          if (onSuccess) onSuccess({ jobId, downloadUrl, job });
        } else if (job.status === 'failed' || job.status === 'error') {
          clearInterval(pollInterval);
          if (onError) onError(job.error || 'فشلت العملية أثناء المعالجة.');
        } else {
          if (onProgress) onProgress('المعالجة قيد التنفيذ، يرجى الانتظار...');
        }
      } catch (err) {
        clearInterval(pollInterval);
        if (onError) onError(err.message);
      }
    }, 2000);

  } catch (err) {
    if (onError) onError(err.message);
  }
}
