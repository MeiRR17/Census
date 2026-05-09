import { useEffect, useState } from 'react';
import { Layers, RefreshCw, ArrowRight, Plus, Building2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';
import { Toast, PageHeader, LoadingSkeleton, Modal } from '../components/ui/index.js';

const Sites = () => {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const [view, setView] = useState('sections'); // 'sites' or 'sections'
  const [sites, setSites] = useState([]);
  const [sections, setSections] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');
  const [modal, setModal] = useState(false);
  const [sectionModal, setSectionModal] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', group_id: '' });
  const [sectionForm, setSectionForm] = useState({ name: '', description: '', site_id: '', classification: 'viewer' });
  const [error, setError] = useState('');

  const showToast = (msg) => setToast(msg);
  const hideToast = () => setToast('');

  const fetchAllData = async () => {
    try {
      const [sitesRes, groupsRes] = await Promise.all([
        api.get('/api/v1/sites/'),
        api.get('/api/v1/groups/'),
      ]);
      setSites(sitesRes.data);
      setGroups(groupsRes.data);

      // Fetch all sections
      const allSections = [];
      for (const site of sitesRes.data) {
        try {
          const { data: siteSections } = await api.get(`/api/v1/sites/${site.id}/sections`);
          const sectionsWithSite = siteSections.map(s => ({
            ...s,
            site_name: site.name,
            site_id: site.id
          }));
          allSections.push(...sectionsWithSite);
        } catch (e) {
          console.error(`Failed to fetch sections for site ${site.id}`);
        }
      }
      setSections(allSections);
    } catch (e) {
      console.error(e);
      showToast('❌ שגיאה בטעינת הנתונים');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAllData(); }, []);

  const handleCreateSite = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/api/v1/sites/', form);
      setModal(false);
      setForm({ name: '', description: '', group_id: '' });
      await fetchAllData();
      showToast(`✅ Site "${form.name}" נוצר בהצלחה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create site');
    }
  };

  const handleCreateSection = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/api/v1/sites/sections', sectionForm);
      setSectionModal(false);
      setSectionForm({ name: '', description: '', site_id: '', classification: 'viewer' });
      await fetchAllData();
      showToast(`✅ Section "${sectionForm.name}" נוצר בהצלחה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create section');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Sites" subtitle="טוען..." canAdd={false} />
        <LoadingSkeleton type="page" count={4} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Toast msg={toast} onClose={hideToast} />

      <PageHeader
        title="Sites & Sections"
        subtitle={`${view === 'sites' ? sites.length : sections.length} פריטים זמינים`}
        onRefresh={fetchAllData}
        canAdd={isAdmin}
        onAdd={() => { view === 'sites' ? setModal(true) : setSectionModal(true); setError(''); }}
        addLabel={view === 'sites' ? 'הוסף Site' : 'הוסף Section'}
      />

      {/* View Toggle */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-xl w-fit">
        <button
          onClick={() => setView('sites')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            view === 'sites' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Sites
        </button>
        <button
          onClick={() => setView('sections')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            view === 'sections' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Sections
        </button>
      </div>

      {/* Sites View */}
      {view === 'sites' && (
        <div className="grid gap-4">
          {sites.map((site) => (
            <div key={site.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-indigo-50 rounded-lg">
                    <Building2 size={20} className="text-indigo-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{site.name}</p>
                    {site.description && <p className="text-xs text-gray-400 mt-0.5">{site.description}</p>}
                    <p className="text-xs text-gray-400 mt-1">
                      נוצר: {new Date(site.created_at).toLocaleDateString('he-IL')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => { setSectionModal(true); setSectionForm({ ...sectionForm, site_id: site.id }); setError(''); }}
                  className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-lg text-sm hover:bg-indigo-100 transition-colors"
                >
                  <Plus size={16} /> הוסף Section
                </button>
              </div>
            </div>
          ))}
          {sites.length === 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
              <Building2 size={40} className="mx-auto text-gray-200 mb-4" />
              <p className="text-gray-400 mb-2">אין Sites עדיין</p>
              {isAdmin && (
                <button
                  onClick={() => setModal(true)}
                  className="text-indigo-600 hover:text-indigo-800 text-sm"
                >
                  צור Site חדש
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Sections View */}
      {view === 'sections' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {sections.map((section) => (
            <div
              key={section.id}
              onClick={() => navigate(`/section/${section.id}`)}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-indigo-50 rounded-xl group-hover:bg-indigo-100 transition-colors">
                  <Layers size={24} className="text-indigo-600" />
                </div>
                <ArrowRight 
                  size={20} 
                  className="text-gray-300 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" 
                />
              </div>
              
              <h3 className="font-bold text-gray-900 mb-1">{section.name}</h3>
              <p className="text-sm text-gray-500 mb-3">{section.site_name}</p>
              
              <div className="flex items-center justify-between text-xs">
                <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {section.classification}
                </span>
                <span className="text-gray-400">
                  {new Date(section.created_at).toLocaleDateString('he-IL')}
                </span>
              </div>
            </div>
          ))}
          {sections.length === 0 && (
            <div className="text-center py-12 bg-white rounded-2xl border border-gray-100 col-span-full">
              <Layers size={48} className="mx-auto text-gray-200 mb-4" />
              <p className="text-gray-400 mb-2">אין Sections עדיין</p>
              <p className="text-sm text-gray-400">
                צור Site חדש ואז הוסף Section
              </p>
            </div>
          )}
        </div>
      )}

      {/* Create Site Modal */}
      <Modal
        isOpen={modal}
        onClose={() => { setModal(false); setError(''); }}
        title="יצירת Site חדש"
        size="sm"
      >
        <form onSubmit={handleCreateSite} className="space-y-4">
          <input placeholder="שם ה-Site" required
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          <input placeholder="תיאור (אופציונלי)"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
          <select
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
            value={form.group_id} onChange={e => setForm({ ...form, group_id: e.target.value })}>
            <option value="">בחר Group (אופציונלי)</option>
            {groups.map(g => (
              <option key={g.id} value={g.id}>{g.name}</option>
            ))}
          </select>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => { setModal(false); setError(''); }}
              className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm">ביטול</button>
            <button type="submit"
              className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 text-sm">צור Site</button>
          </div>
        </form>
      </Modal>

      {/* Create Section Modal */}
      <Modal
        isOpen={sectionModal}
        onClose={() => { setSectionModal(false); setError(''); }}
        title="יצירת Section חדש"
        size="sm"
      >
        <form onSubmit={handleCreateSection} className="space-y-4">
          <select
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
            value={sectionForm.site_id} onChange={e => setSectionForm({ ...sectionForm, site_id: e.target.value })}
            required>
            <option value="">בחר Site</option>
            {sites.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <input placeholder="שם ה-Section" required
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            value={sectionForm.name} onChange={e => setSectionForm({ ...sectionForm, name: e.target.value })} />
          <input placeholder="תיאור (אופציונלי)"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            value={sectionForm.description} onChange={e => setSectionForm({ ...sectionForm, description: e.target.value })} />
          <select
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
            value={sectionForm.classification} onChange={e => setSectionForm({ ...sectionForm, classification: e.target.value })}>
            <option value="viewer">Viewer</option>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => { setSectionModal(false); setError(''); }}
              className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm">ביטול</button>
            <button type="submit"
              className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 text-sm">צור Section</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Sites;