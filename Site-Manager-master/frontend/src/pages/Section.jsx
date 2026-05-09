import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, Layers, RefreshCw, Trash2 } from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';
import { Toast, PageHeader, LoadingSkeleton } from '../components/ui/index.js';

const Section = () => {
  const { sectionId } = useParams();
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const [section, setSection] = useState(null);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const showToast = (msg) => setToast(msg);
  const hideToast = () => setToast('');

  const fetchSectionData = async () => {
    try {
      const [sectionRes, devicesRes] = await Promise.all([
        api.get(`/api/v1/sites/sections/${sectionId}`),
        api.get(`/api/v1/devices/?section_id=${sectionId}`),
      ]);
      setSection(sectionRes.data);
      setDevices(devicesRes.data);
    } catch (e) {
      console.error(e);
      showToast('❌ שגיאה בטעינת הנתונים');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSectionData();
  }, [sectionId]);

  const handleExcelUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      showToast('❌ רק קבצי Excel (.xlsx, .xls) נתמכים');
      e.target.value = '';
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(
        `/api/v1/devices/import/${sectionId}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );
      const { summary } = response.data;
      showToast(
        `✅ יובאו ${summary.added} מכשירים` +
        (summary.already_exists > 0 ? ` (${summary.already_exists} קיימים)` : '') +
        (summary.duplicates_in_file > 0 ? `, ${summary.duplicates_in_file} כפולים` : '') +
        (summary.invalid_cells > 0 ? `, ${summary.invalid_cells} לא תקינים` : '')
      );
      await fetchSectionData(); // רענון הרשימה
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'שגיאה בייבוא הקובץ';
      showToast(`❌ ${errorMsg}`);
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => navigate('/sites')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={20} /> חזרה לרשימה
        </button>
        <LoadingSkeleton type="page" count={3} />
      </div>
    );
  }

  if (!section) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Section לא נמצא</p>
        <button
          onClick={() => navigate('/sites')}
          className="mt-4 text-indigo-600 hover:text-indigo-800"
        >
          חזרה לרשימה
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Toast msg={toast} onClose={hideToast} />

      {/* כפתור חזרה */}
      <button
        onClick={() => navigate('/sites')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft size={20} /> חזרה לרשימה
      </button>

      {/* כותרת */}
      <PageHeader
        title={section.name}
        subtitle={section.description || `Site: ${section.site_name || '—'}`}
        onRefresh={fetchSectionData}
        canAdd={false}
        extraActions={isAdmin && (
          <label className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all cursor-pointer ${
            isUploading 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-green-600 text-white hover:bg-green-700 shadow-sm'
          }`}>
            {isUploading ? (
              <>
                <RefreshCw size={16} className="animate-spin" /> מייבא...
              </>
            ) : (
              <>
                <Upload size={18} /> ייבא Excel
              </>
            )}
            <input
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={handleExcelUpload}
              disabled={isUploading}
            />
          </label>
        )}
      />

      {/* סטטיסטיקה */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <p className="text-sm text-gray-500">סה"כ מכשירים</p>
          <p className="text-2xl font-bold text-gray-900">{devices.length}</p>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <p className="text-sm text-gray-500">Classification</p>
          <p className="text-lg font-semibold text-indigo-600">{section.classification}</p>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <p className="text-sm text-gray-500">נוצר</p>
          <p className="text-sm text-gray-700">
            {new Date(section.created_at).toLocaleDateString('he-IL')}
          </p>
        </div>
      </div>

      {/* רשימת מכשירים */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2">
          <Layers size={18} className="text-indigo-500" />
          <h2 className="font-semibold text-gray-800">מכשירים ב-section</h2>
        </div>
        
        {devices.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-400 mb-4">אין מכשירים עדיין</p>
            {isAdmin && (
              <label className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 text-green-600 rounded-lg cursor-pointer hover:bg-green-100 transition-colors border border-green-200">
                <Upload size={16} /> ייבא מקובץ Excel
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  className="hidden"
                  onChange={handleExcelUpload}
                  disabled={isUploading}
                />
              </label>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {devices.map((device) => (
              <div key={device.id} className="flex items-center justify-between px-6 py-3 hover:bg-gray-50/50">
                <div>
                  <p className="font-medium text-gray-800">{device.identifier}</p>
                  <p className="text-xs text-gray-500">
                    נוסף: {new Date(device.created_at).toLocaleDateString('he-IL')}
                  </p>
                </div>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {device.classification}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Section;
